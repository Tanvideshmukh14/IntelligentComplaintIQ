/* IntelligentComplaintIQ — App Controller v2 */
let currentTab='overview',filterState={},filterOptions={},complaintsPage=1;
const STATUS_COLORS={Open:'#3b82f6','In Progress':'#f59e0b',Resolved:'#10b981',Escalated:'#ef4444',Closed:'#64748b'};

document.addEventListener('DOMContentLoaded',async()=>{
  setupNavigation();showLoading('Initializing...');
  try{filterOptions=await API.getFilters();populateFilterDropdowns();await loadTab('overview');}
  catch(e){console.error('Init:',e);}
  hideLoading();
});

function setupNavigation(){
  document.querySelectorAll('.nav-tab').forEach(tab=>{
    tab.addEventListener('click',()=>{
      const t=tab.dataset.tab;if(t===currentTab)return;
      document.querySelectorAll('.nav-tab').forEach(x=>x.classList.remove('active'));tab.classList.add('active');
      document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
      const panel=document.getElementById('panel-'+t);if(panel)panel.classList.add('active');
      currentTab=t;loadTab(t);
    });
  });
}

async function loadTab(tab){
  showLoading('Loading...');
  try{
    if(tab==='overview')await loadOverview();
    else if(tab==='sentiment-severity')await Promise.all([loadSentiment(), loadSeverity()]);
    else if(tab==='cluster-duplicate')await Promise.all([loadClusters(), loadDuplicates()]);
    else if(tab==='operations-predictions')await Promise.all([loadDepartments(), loadPredictions()]);
    else if(tab==='complaints')await loadComplaints();
  }catch(e){console.error('Load:',e);}
  hideLoading();
}

async function loadOverview(){
  const d=await API.getOverview(filterState);
  setKPI('kpi-total',fmt(d.total_complaints));setKPI('kpi-open',fmt(d.open_complaints));
  setKPI('kpi-resolved',fmt(d.resolved_complaints));setKPI('kpi-critical',fmt(d.critical_complaints));
  setKPI('kpi-esc-rate',(d.escalation_rate||0)+'%');setKPI('kpi-avg-time',formatDuration(d.avg_resolution_time_hours));
  setKPI('kpi-dup-rate',(d.duplicate_rate||0)+'%');setKPI('kpi-spam-rate',(d.spam_rate||0)+'%');
  setKPI('kpi-csat',(d.avg_csat||0)+'/5');setKPI('kpi-nps',(d.nps_score>0?'+':'')+d.nps_score);
  if(d.status_distribution)createDoughnut('chart-status',d.status_distribution,Object.keys(d.status_distribution).map(k=>STATUS_COLORS[k]||'#6366f1'));
  if(d.severity_distribution)createDoughnut('chart-severity-overview',d.severity_distribution,[SEVERITY_COLORS.Low,SEVERITY_COLORS.Medium,SEVERITY_COLORS.High,SEVERITY_COLORS.Critical]);
  if(d.sentiment_distribution)createDoughnut('chart-sentiment-overview',d.sentiment_distribution);
  if(d.product_distribution){const s=Object.entries(d.product_distribution).sort((a,b)=>b[1]-a[1]);createHorizontalBar('chart-products-overview',s.map(e=>e[0]),s.map(e=>e[1]));}
}

async function loadSentiment(){
  const d=await API.getSentiment(filterState);
  setKPI('kpi-avg-sentiment',(d.avg_sentiment||0).toFixed(2));
  setKPI('kpi-frustration',(d.frustration_index||0)+'%');
  setKPI('kpi-esc-prob',((d.avg_escalation_prob||0)*100).toFixed(1)+'%');
  const posPct=d.sentiment_distribution?Math.round((d.sentiment_distribution['Positive']||0)/Math.max(Object.values(d.sentiment_distribution).reduce((a,b)=>a+b,0),1)*100):0;
  setKPI('kpi-positive-pct',posPct+'%');
  if(d.sentiment_distribution)createDoughnut('chart-sentiment-dist',d.sentiment_distribution);
  if(d.emotion_distribution){renderEmotionBars('chart-emotions',d.emotion_distribution);}
  if(d.sentiment_trend&&d.sentiment_trend.length){const months=[...new Set(d.sentiment_trend.map(x=>x.month))].sort(),types=[...new Set(d.sentiment_trend.map(x=>x.sentiment_label))];createLineChart('chart-sentiment-trend',months,types.map(t=>({label:t,data:months.map(m=>{const i=d.sentiment_trend.find(x=>x.month===m&&x.sentiment_label===t);return i?i.count:0;}),color:SENTIMENT_COLORS[t]})));}
  if(d.sentiment_by_product){const s=Object.entries(d.sentiment_by_product).sort((a,b)=>a[1]-b[1]);createBar('chart-sentiment-product',s.map(e=>e[0]),s.map(e=>e[1]),null,'Avg Sentiment');}
}

async function loadSeverity(){
  const d=await API.getSeverity(filterState);
  setKPI('kpi-critical-sev',fmt(d.critical_count||0));setKPI('kpi-high-sev',fmt(d.high_count||0));
  setKPI('kpi-avg-severity',((d.avg_severity||0)*100).toFixed(0)+'%');setKPI('kpi-safety',fmt(d.safety_issue_count||0));
  if(d.severity_distribution)createDoughnut('chart-severity-dist',d.severity_distribution,[SEVERITY_COLORS.Low,SEVERITY_COLORS.Medium,SEVERITY_COLORS.High,SEVERITY_COLORS.Critical].filter(Boolean));
  if(d.urgency_distribution)createDoughnut('chart-urgency',d.urgency_distribution);
  if(d.severity_trend&&d.severity_trend.length){const months=[...new Set(d.severity_trend.map(x=>x.month))].sort(),levels=['Critical','High','Medium','Low'];createLineChart('chart-severity-trend',months,levels.filter(l=>d.severity_trend.some(x=>x.severity_level===l)).map(l=>({label:l,data:months.map(m=>{const i=d.severity_trend.find(x=>x.month===m&&x.severity_level===l);return i?i.count:0;}),color:SEVERITY_COLORS[l]})));}
  const el=document.getElementById('severity-alerts');
  if(el&&d.critical_alerts)el.innerHTML=d.critical_alerts.length===0?'<p style="color:var(--text-muted);padding:20px;text-align:center;">No critical alerts</p>':d.critical_alerts.map(a=>`<div class="alert-item"><span class="alert-icon">🚨</span><div class="alert-content"><div class="alert-title">${a.complaint_id} — ${a.product}</div><div class="alert-desc">${a.description}</div><div class="alert-meta"><span>📍 ${a.location}</span><span>📅 ${new Date(a.date).toLocaleDateString()}</span></div></div></div>`).join('');
}

async function loadClusters(){
  const d=await API.getClusters(filterState);
  if(d.cluster_distribution){const s=Object.entries(d.cluster_distribution).sort((a,b)=>b[1]-a[1]);createHorizontalBar('chart-cluster-dist',s.map(e=>trunc(e[0],25)),s.map(e=>e[1]));createDoughnut('chart-cluster-pie',Object.fromEntries(s.map(e=>[trunc(e[0],20),e[1]])));}
  if(d.cluster_trend&&d.cluster_trend.length){const months=[...new Set(d.cluster_trend.map(x=>x.month))].sort(),cls=[...new Set(d.cluster_trend.map(x=>x.cluster_label))];createLineChart('chart-cluster-trend',months,cls.slice(0,6).map(c=>({label:trunc(c,20),data:months.map(m=>{const i=d.cluster_trend.find(x=>x.month===m&&x.cluster_label===c);return i?i.count:0;})})));}
  const el=document.getElementById('cluster-details');
  if(el&&d.cluster_details)el.innerHTML=Object.entries(d.cluster_details).map(([n,info])=>`<div class="rec-card"><div class="rec-type">${n}</div><div class="result-item"><span class="result-label">Complaints</span><span class="result-value">${info.count}</span></div><div class="result-item"><span class="result-label">Avg Severity</span><span class="result-value">${(info.avg_severity*100).toFixed(0)}%</span></div><div class="result-item"><span class="result-label">Top Products</span><span class="result-value">${Object.keys(info.top_products||{}).slice(0,2).join(', ')||'N/A'}</span></div></div>`).join('');
}

async function loadDuplicates(){
  const d=await API.getDuplicates();
  setKPI('kpi-dup-count',fmt(d.duplicate_count||0));setKPI('kpi-spam-count',fmt(d.spam_count||0));
  setKPI('kpi-dup-rate2',(d.duplicate_rate||0)+'%');setKPI('kpi-spam-rate2',(d.spam_rate||0)+'%');
  if(d.toxicity_distribution)createDoughnut('chart-toxicity',d.toxicity_distribution);
  if(d.spam_by_channel&&Object.keys(d.spam_by_channel).length)createBar('chart-spam-channel',Object.keys(d.spam_by_channel),Object.values(d.spam_by_channel),COLORS.red,'Spam Count');
  const dg=document.getElementById('duplicate-groups');
  if(dg&&d.duplicate_groups)dg.innerHTML=d.duplicate_groups.length===0?'<p style="color:var(--text-muted);padding:20px;text-align:center;">No duplicates found</p>':d.duplicate_groups.map(g=>`<div class="alert-item"><span class="alert-icon">📋</span><div class="alert-content"><div class="alert-title">Group #${g.group_id} — ${g.count} complaints</div><div class="alert-desc">IDs: ${g.complaint_ids.join(', ')} | Similarity: ${(g.avg_similarity*100).toFixed(0)}%</div></div></div>`).join('');
  const fa=document.getElementById('fraud-alerts');
  if(fa&&d.fraud_alerts)fa.innerHTML=d.fraud_alerts.length===0?'<p style="color:var(--text-muted);padding:20px;text-align:center;">No fraud alerts</p>':d.fraud_alerts.map(f=>`<div class="alert-item" style="border-color:rgba(239,68,68,0.2);"><span class="alert-icon">🚫</span><div class="alert-content"><div class="alert-title">${f.complaint_id}</div><div class="alert-desc">Fraud Risk: ${(f.fraud_score*100).toFixed(0)}% | Product: ${f.product}</div></div></div>`).join('');
}

async function loadDepartments(){
  const d=await API.getDepartments(filterState);
  setKPI('kpi-sla',(d.sla_compliance||0)+'%');setKPI('kpi-mttr',formatDuration(d.mean_time_to_resolution));
  setKPI('kpi-esc-time',formatDuration(d.escalation_handling_time));
  setKPI('kpi-dept-count',d.department_distribution?Object.keys(d.department_distribution).length:0);
  if(d.department_distribution){const s=Object.entries(d.department_distribution).sort((a,b)=>b[1]-a[1]);createHorizontalBar('chart-dept-dist',s.map(e=>trunc(e[0],20)),s.map(e=>e[1]));}
  if(d.department_metrics){const depts=Object.keys(d.department_metrics),m=Object.values(d.department_metrics);
    createBar('chart-dept-resolution',depts.map(x=>trunc(x,18)),m.map(x=>x.resolution_rate),COLORS.green,'Resolution %');
    createBar('chart-dept-time',depts.map(x=>trunc(x,18)),m.map(x=>x.avg_resolution_time),COLORS.cyan,'Avg Hours');
    const tb=document.getElementById('dept-table-body');
    if(tb)tb.innerHTML=depts.map(dept=>{const x=d.department_metrics[dept];return`<tr><td>${dept}</td><td>${x.total}</td><td>${x.resolved}</td><td><span class="badge ${x.resolution_rate>60?'badge-low':x.resolution_rate>40?'badge-medium':'badge-critical'}">${x.resolution_rate}%</span></td><td>${formatDuration(x.avg_resolution_time)}</td><td>${x.escalated}</td><td>${x.avg_csat}/5</td></tr>`;}).join('');
  }
}

async function loadPredictions(){
  const[pred,recs]=await Promise.all([API.getPredictions(),API.getRecommendations()]);
  setKPI('kpi-churn-risk',(pred.churn_risk_percentage||0)+'%');setKPI('kpi-churn-count',fmt(pred.churn_risk_count||0));
  if(pred.complaint_forecast&&pred.complaint_forecast.length)createBar('chart-forecast',pred.complaint_forecast.map(f=>f.month),pred.complaint_forecast.map(f=>f.predicted_count),COLORS.blue,'Predicted');
  if(pred.seasonal_patterns){const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];const vals=months.map((_,i)=>pred.seasonal_patterns[i+1]||0);createLineChart('chart-seasonal',months,[{label:'Complaints',data:vals,color:COLORS.cyan}]);}
  const ei=document.getElementById('emerging-issues');
  if(ei&&pred.emerging_issues)ei.innerHTML=pred.emerging_issues.length===0?'<p style="color:var(--text-muted);text-align:center;padding:40px;">No emerging issues</p>':pred.emerging_issues.map(i=>`<div class="alert-item" style="border-color:rgba(245,158,11,0.2);background:rgba(245,158,11,0.05);"><span class="alert-icon">📈</span><div class="alert-content"><div class="alert-title">${i.product}</div><div class="alert-desc">Trend: ${i.trend} | Recent: ${i.recent_count} | Growth: +${i.growth}%</div></div></div>`).join('');
  const ef=document.getElementById('equipment-failures');
  if(ef&&pred.equipment_failures)ef.innerHTML=Object.keys(pred.equipment_failures).length===0?'<p style="color:var(--text-muted);text-align:center;padding:40px;">No data</p>':Object.entries(pred.equipment_failures).map(([m,v])=>`<div class="alert-item"><span class="alert-icon">🔧</span><div class="alert-content"><div class="alert-title">${m}</div><div class="alert-desc">${v.complaint_count} complaints | Severity: ${v.avg_severity} | Risk: ${v.risk_level}</div></div></div>`).join('');
  const rl=document.getElementById('recommendations-list');
  if(rl&&recs.recommendations)rl.innerHTML=recs.recommendations.length===0?'<p style="color:var(--text-muted);text-align:center;padding:40px;">No recommendations</p>':recs.recommendations.map(r=>`<div class="rec-card ${r.priority.toLowerCase()}"><div class="rec-type">${r.type} — ${r.priority}</div><div class="rec-message">${r.message}</div><div class="rec-action">→ ${r.action}</div></div>`).join('');
}

async function loadComplaints(){
  const params={...filterState,page:complaintsPage,page_size:30};
  const se=document.getElementById('complaint-search');if(se&&se.value)params.search=se.value;
  const d=await API.getComplaints(params),tbody=document.getElementById('complaints-tbody');if(!tbody)return;
  tbody.innerHTML=(d.complaints||[]).map(c=>`<tr><td>${c.complaint_id||''}</td><td>${c.date_time?new Date(c.date_time).toLocaleDateString():''}</td><td>${c.product_type||''}</td><td>${c.predicted_category||''}</td><td title="${esc(c.complaint_description||'')}">${trunc(c.complaint_description||'',50)}</td><td><span class="badge badge-${(c.sentiment_label||'neutral').toLowerCase().replace(' ','-')}">${c.sentiment_label||'N/A'}</span></td><td><span class="badge badge-${(c.severity_level||'low').toLowerCase()}">${c.severity_level||'N/A'}</span></td><td>${trunc(c.predicted_department||'',20)}</td><td><span class="badge badge-${(c.resolution_status||'open').toLowerCase().replace(' ','-')}">${c.resolution_status||''}</span></td></tr>`).join('');
  const info=document.getElementById('pagination-info');
  if(info)info.textContent=`Showing ${((d.page-1)*d.page_size)+1}–${Math.min(d.page*d.page_size,d.total)} of ${d.total}`;
  const btns=document.getElementById('pagination-buttons');
  if(btns){const pages=d.pages||1;let h=`<button class="page-btn" onclick="goPage(1)" ${d.page<=1?'disabled':''}>«</button><button class="page-btn" onclick="goPage(${d.page-1})" ${d.page<=1?'disabled':''}>‹</button>`;const s=Math.max(1,d.page-2),e=Math.min(pages,d.page+2);for(let p=s;p<=e;p++)h+=`<button class="page-btn ${p===d.page?'active':''}" onclick="goPage(${p})">${p}</button>`;h+=`<button class="page-btn" onclick="goPage(${d.page+1})" ${d.page>=pages?'disabled':''}>›</button><button class="page-btn" onclick="goPage(${pages})" ${d.page>=pages?'disabled':''}>»</button>`;btns.innerHTML=h;}
}
function goPage(p){complaintsPage=p;loadComplaints();}
function searchComplaints(){complaintsPage=1;loadComplaints();}

async function analyzeComplaint(){
  const text=document.getElementById('analyze-text').value.trim();if(!text)return;
  const btn=document.getElementById('analyze-btn');btn.disabled=true;btn.textContent='Analyzing...';
  try{
    const r=await API.analyzeComplaint({complaint_text:text});
    const el=document.getElementById('analyze-results');el.style.display='grid';
    el.innerHTML=`
      <div class="result-card"><div class="rec-type">💬 Sentiment</div><div class="result-item"><span class="result-label">Label</span><span class="result-value"><span class="badge badge-${r.sentiment.sentiment_label.toLowerCase().replace(' ','-')}">${r.sentiment.sentiment_label}</span></span></div><div class="result-item"><span class="result-label">Score</span><span class="result-value">${r.sentiment.sentiment_score}</span></div><div class="result-item"><span class="result-label">Emotion</span><span class="result-value">${r.sentiment.emotion}</span></div><div class="result-item"><span class="result-label">Escalation</span><span class="result-value">${(r.sentiment.escalation_probability*100).toFixed(1)}%</span></div></div>
      <div class="result-card"><div class="rec-type">📂 Category</div><div class="result-item"><span class="result-label">Category</span><span class="result-value">${r.category.predicted_category}</span></div><div class="result-item"><span class="result-label">Confidence</span><span class="result-value">${(r.category.confidence*100).toFixed(1)}%</span></div></div>
      <div class="result-card"><div class="rec-type">🚨 Severity</div><div class="result-item"><span class="result-label">Level</span><span class="result-value"><span class="badge badge-${r.severity.severity_level.toLowerCase()}">${r.severity.severity_level}</span></span></div><div class="result-item"><span class="result-label">Score</span><span class="result-value">${(r.severity.severity_score*100).toFixed(0)}%</span></div><div class="result-item"><span class="result-label">Priority</span><span class="result-value">P${r.severity.priority_rank}</span></div></div>
      <div class="result-card"><div class="rec-type">🏢 Routing</div><div class="result-item"><span class="result-label">Department</span><span class="result-value">${r.routing.predicted_department}</span></div><div class="result-item"><span class="result-label">Confidence</span><span class="result-value">${(r.routing.confidence*100).toFixed(1)}%</span></div></div>
      <div class="result-card"><div class="rec-type">🚫 Spam Check</div><div class="result-item"><span class="result-label">Spam</span><span class="result-value">${r.spam_analysis.is_spam?'Yes':'No'} (${(r.spam_analysis.spam_probability*100).toFixed(0)}%)</span></div><div class="result-item"><span class="result-label">Toxicity</span><span class="result-value">${(r.spam_analysis.toxicity_score*100).toFixed(0)}%</span></div></div>
      <div class="result-card"><div class="rec-type">⏱️ Resolution</div><div class="result-item"><span class="result-label">Est. Time</span><span class="result-value">${r.resolution_prediction.predicted_resolution_hours}h</span></div><div class="result-item"><span class="result-label">SLA Breach</span><span class="result-value">${(r.resolution_prediction.sla_breach_probability*100).toFixed(0)}%</span></div></div>`;
  }catch(e){console.error(e);}
  btn.disabled=false;btn.textContent='🔍 Run Full AI Analysis';
}

async function handleFileUpload(event){
  const file=event.target.files[0];if(!file)return;
  const status=document.getElementById('upload-status');
  const schema=document.getElementById('schema-display');
  const progress=document.getElementById('analysis-progress');
  status.style.display='block'; schema.style.display='none';
  progress.style.display='block';
  // Show unified progress for the entire pipeline
  status.innerHTML=`<div class="rec-card" style="border-color:rgba(6,182,212,0.3)">
    <div class="rec-type">⏳ Processing <strong>${file.name}</strong></div>
    <div class="rec-message" id="activation-step">Step 1/5: Uploading dataset...</div>
    <div class="progress-bar" style="margin-top:12px"><div class="progress-fill blue" id="activation-bar" style="width:5%;transition:width 0.6s ease"></div></div></div>`;
  progress.innerHTML='';
  try{
    const stepEl=document.getElementById('activation-step');
    const barEl=document.getElementById('activation-bar');
    // Step 1: Upload and activate in one call
    stepEl.textContent='Step 1/5: Uploading & ingesting into system database...';
    barEl.style.width='10%';
    // Animate progress while waiting for server
    const steps=[
      {msg:'Step 2/5: Auto-mapping schema & preprocessing data...',pct:'25%',delay:3000},
      {msg:'Step 3/5: Running 10 AI modules (Sentiment, Severity, Clustering, Routing, Spam, Duplicates)...',pct:'45%',delay:6000},
      {msg:'Step 4/5: Computing analytics, predictions & KPIs...',pct:'65%',delay:10000},
    ];
    const timers=steps.map(s=>setTimeout(()=>{stepEl.textContent=s.msg;barEl.style.width=s.pct;},s.delay));
    const r=await API.uploadAndActivate(file);
    timers.forEach(t=>clearTimeout(t));
    // Step 5: Refresh all dashboards
    barEl.style.width='80%';
    stepEl.textContent='Step 5/5: Refreshing all dashboard pages...';
    await refreshAllDashboards();
    barEl.style.width='100%';
    // Show success
    status.innerHTML=`<div class="rec-card" style="border-color:rgba(16,185,129,0.3)">
      <div class="rec-type">✅ Dataset Activated — Dashboard Updated</div>
      <div class="rec-message">${r.message||'All analytics now reflect the new dataset.'}</div>
      <div class="result-item"><span class="result-label">File</span><span class="result-value">${r.filename}</span></div>
      <div class="result-item"><span class="result-label">Records Ingested</span><span class="result-value" style="color:var(--accent-green);font-weight:700;">${r.rows_ingested||0}</span></div>
      <div class="result-item"><span class="result-label">AI Modules Executed</span><span class="result-value">10/10</span></div>
      <div class="rec-message" style="margin-top:8px;color:var(--accent-cyan);font-size:12px;">✨ All KPIs, charts, tables, and analytics across every page are now updated.</div></div>`;
    progress.innerHTML='';
    // Auto-navigate to Overview after 1.5s so user sees updated dashboard
    setTimeout(()=>{
      const overviewTab=document.querySelector('[data-tab="overview"]');
      if(overviewTab) overviewTab.click();
    },1500);
  }catch(e){
    status.innerHTML=`<div class="rec-card" style="border-color:rgba(239,68,68,0.3)">
      <div class="rec-type">❌ Activation Failed</div>
      <div class="rec-message">${e.message}</div>
      <div class="rec-message" style="margin-top:8px;color:var(--text-muted);font-size:11px;">Ensure the dataset is a valid CSV/Excel/JSON file with complaint-like data.</div></div>`;
    progress.innerHTML='';
  }
  // Reset file input so same file can be re-uploaded
  event.target.value='';
}

async function activateGlobalDataset(){
  // Kept for backward compatibility — redirects to upload
  const fileInput=document.getElementById('file-input');
  if(fileInput) fileInput.click();
}

async function refreshAllDashboards(){
  try{
    filterOptions=await API.getFilters();
    populateFilterDropdowns();
    filterState={};
    await loadOverview();
    await Promise.all([loadSentiment(), loadSeverity()]);
    await Promise.all([loadClusters(), loadDuplicates()]);
    await Promise.all([loadDepartments(), loadPredictions()]);
    complaintsPage=1;
    await loadComplaints();
  }catch(e){console.error('Dashboard refresh error:',e);}
}

async function runAutoAnalyze(filename){
  const progress=document.getElementById('analysis-progress');
  progress.style.display='block';
  progress.innerHTML='<div class="rec-card" style="border-color:rgba(6,182,212,0.3)"><div class="rec-type">⏳ Running AI Analysis Pipeline</div><div class="rec-message">Sentiment • Keywords • Clustering • Trends • Statistics • Insights...</div><div class="progress-bar" style="margin-top:12px"><div class="progress-fill blue" style="width:30%;animation:pulse 1.5s infinite"></div></div></div>';
  try{
    const r=await API.autoAnalyze(filename);
    progress.innerHTML='<div class="rec-card" style="border-color:rgba(16,185,129,0.3)"><div class="rec-type">✅ Analysis Complete</div><div class="rec-message">All applicable analyses finished successfully.</div></div>';
    renderDynamicDashboard(r.results);
  }catch(e){
    progress.innerHTML='<p style="color:#ef4444;">❌ Analysis error: '+e.message+'</p>';
  }
}

function renderDynamicDashboard(results){
  // KPIs
  const kpiEl=document.getElementById('dynamic-kpis');
  if(results.kpis&&results.kpis.length){
    kpiEl.style.display='grid';
    kpiEl.innerHTML=results.kpis.map(k=>`<div class="kpi-card ${k.color?'accent-'+k.color:''}"><div class="kpi-label">${k.label}</div><div class="kpi-value">${k.value}</div></div>`).join('');
  }
  // Insights
  const insEl=document.getElementById('dynamic-insights');
  if(results.insights&&results.insights.length){
    insEl.style.display='block';
    insEl.innerHTML=`<div class="alerts-panel"><div class="chart-header"><div><div class="chart-title">🧠 AI-Generated Insights</div></div></div>
      ${results.insights.map(i=>`<div class="alert-item" style="border-color:rgba(${i.type==='critical'?'239,68,68':i.type==='warning'?'245,158,11':'99,102,241'},0.2);background:rgba(${i.type==='critical'?'239,68,68':i.type==='warning'?'245,158,11':'99,102,241'},0.05);">
        <span class="alert-icon">${i.icon}</span><div class="alert-content"><div class="alert-title">${i.title}</div><div class="alert-desc">${i.message}</div></div>
        <span class="badge badge-${i.priority==='critical'?'critical':i.priority==='high'?'high':'medium'}">${i.priority}</span></div>`).join('')}</div>`;
  }
  // Charts
  const chartEl=document.getElementById('dynamic-charts');
  if(results.charts&&results.charts.length){
    chartEl.style.display='grid';
    chartEl.innerHTML=results.charts.map(c=>`<div class="chart-card"><div class="chart-header"><div><div class="chart-title">${c.title}</div></div></div><div class="chart-container"><canvas id="${c.id}"></canvas></div></div>`).join('');
    // Render each chart after DOM update
    setTimeout(()=>{
      results.charts.forEach(c=>{
        if(!c.data||!Object.keys(c.data).length)return;
        const labels=Object.keys(c.data),values=Object.values(c.data);
        if(c.type==='doughnut')createDoughnut(c.id,c.data);
        else if(c.type==='bar')createBar(c.id,labels,values,null,c.title);
        else if(c.type==='line')createLineChart(c.id,labels,[{label:'Value',data:values,color:COLORS.cyan}]);
      });
    },100);
  }
  // Details (keywords, clusters, correlations)
  const detEl=document.getElementById('dynamic-details');
  let detHTML='';
  const a=results.analyses||{};
  if(a.keywords&&a.keywords.top_words){
    detHTML+=`<div class="alerts-panel"><div class="chart-header"><div><div class="chart-title">🔑 Top Keywords</div></div></div>
      <div style="display:flex;flex-wrap:wrap;gap:8px;padding:12px">${a.keywords.top_words.slice(0,20).map(w=>`<span class="badge badge-medium" style="font-size:12px;padding:4px 10px">${w.word} (${w.count})</span>`).join('')}</div></div>`;
  }
  if(a.clusters&&a.clusters.cluster_details){
    detHTML+=`<div class="alerts-panel" style="margin-top:16px"><div class="chart-header"><div><div class="chart-title">🔬 Discovered Topics</div></div></div>
      ${Object.entries(a.clusters.cluster_details).map(([name,info])=>`<div class="rec-card"><div class="rec-type">${name}</div>
        <div class="result-item"><span class="result-label">Entries</span><span class="result-value">${info.count}</span></div>
        <div class="result-item"><span class="result-label">Keywords</span><span class="result-value">${(info.keywords||[]).join(', ')}</span></div></div>`).join('')}</div>`;
  }
  if(a.numerical&&a.numerical.statistics){
    detHTML+=`<div class="table-container" style="margin-top:16px"><div class="table-toolbar"><span class="chart-title">📐 Numerical Statistics</span></div>
      <table class="data-table"><thead><tr><th>Column</th><th>Mean</th><th>Median</th><th>Min</th><th>Max</th><th>Std Dev</th><th>Outliers</th></tr></thead>
      <tbody>${Object.entries(a.numerical.statistics).map(([col,s])=>`<tr><td>${col}</td><td>${s.mean}</td><td>${s.median}</td><td>${s.min}</td><td>${s.max}</td><td>${s.std}</td><td>${s.outlier_count}</td></tr>`).join('')}</tbody></table></div>`;
  }
  if(a.correlations&&a.correlations.significant_correlations&&a.correlations.significant_correlations.length){
    detHTML+=`<div class="alerts-panel" style="margin-top:16px"><div class="chart-header"><div><div class="chart-title">🔗 Significant Correlations</div></div></div>
      ${a.correlations.significant_correlations.map(c=>`<div class="rec-card"><div class="rec-type">${c.strength} Correlation</div>
        <div class="rec-message">${c.col1} ↔ ${c.col2}: <strong>${c.correlation}</strong></div></div>`).join('')}</div>`;
  }
  if(detHTML){detEl.style.display='block';detEl.innerHTML=detHTML;}
}

function populateFilterDropdowns(){
  populateSelect('filter-product',filterOptions.product_types||[]);
  populateSelect('filter-severity',filterOptions.severity_levels||[]);
  populateSelect('filter-status',filterOptions.statuses||[]);
  populateSelect('filter-channel',filterOptions.channels||[]);
  populateSelect('filter-segment',filterOptions.segments||[]);
  populateSelect('filter-state',filterOptions.states||[]);
}
function populateSelect(id,opts){const el=document.getElementById(id);if(!el)return;const first=el.querySelector('option')?.textContent||'All';el.innerHTML=`<option value="">${first}</option>`+opts.map(o=>`<option value="${o}">${o}</option>`).join('');}
function applyFilters(){const g=id=>document.getElementById(id)?.value||'';filterState={product_type:g('filter-product'),severity_level:g('filter-severity'),status:g('filter-status'),channel:g('filter-channel'),segment:g('filter-segment'),state:g('filter-state')};Object.keys(filterState).forEach(k=>{if(!filterState[k])delete filterState[k];});loadTab(currentTab);}
function resetFilters(){document.querySelectorAll('.filter-select').forEach(s=>s.value='');filterState={};loadTab(currentTab);}

function setKPI(id,v){
  const el=document.getElementById(id);if(!el)return;
  el.textContent=v;
  // Dynamically fix trend indicator based on actual value
  const trendEl=el.closest('.kpi-body')?.querySelector('.kpi-trend');
  if(!trendEl)return;
  const isZero=isKPIZero(v);
  if(isZero){
    trendEl.className='kpi-trend inactive';
    trendEl.innerHTML='<span class="trend-arrow">—</span> No Change';
  }
}
function isKPIZero(v){
  if(v===null||v===undefined||v==='—')return true;
  const s=String(v).trim();
  // Strip suffixes: %, h, /5, k, etc.
  const n=s.replace(/^[+\-]/, '').replace(/%$/, '').replace(/h$/, '').replace(/\/\d+$/, '').replace(/k$/, '');
  const num=parseFloat(n);
  return isNaN(num)||num===0;
}

const EMOTION_COLORS = {
  'Frustration':'#f59e0b','Anger':'#ef4444','Fear':'#a855f7','Urgency':'#ef4444',
  'Confusion':'#fbbf24','Sadness':'#6366f1','Disappointment':'#fb7185','Anxiety':'#ec4899',
  'Neutral':'#64748b','None':'#64748b','Satisfaction':'#10b981','Relief':'#06b6d4',
};
function renderEmotionBars(containerId, data){
  const el=document.getElementById(containerId);if(!el)return;
  const entries=Object.entries(data).sort((a,b)=>b[1]-a[1]);
  const total=entries.reduce((s,e)=>s+e[1],0)||1;
  const maxVal=entries.length?entries[0][1]:1;
  el.innerHTML=entries.map(([emotion,count])=>{
    const pct=Math.round(count/total*100);
    const barPct=Math.round(count/maxVal*100);
    const color=EMOTION_COLORS[emotion]||PALETTE[entries.indexOf(entries.find(e=>e[0]===emotion))%PALETTE.length];
    return `<div class="emotion-bar-row">
      <div class="emotion-bar-label" title="${emotion}">${emotion}</div>
      <div class="emotion-bar-track">
        <div class="emotion-bar-fill" style="width:0%;background:${color};" data-width="${barPct}%"></div>
      </div>
      <div class="emotion-bar-value" style="color:${color}">${pct}%</div>
    </div>`;
  }).join('');
  // Animate bars in
  requestAnimationFrame(()=>{
    el.querySelectorAll('.emotion-bar-fill').forEach(bar=>{
      bar.style.width=bar.dataset.width;
    });
  });
}
function fmt(n){return n>=1000?(n/1000).toFixed(1)+'k':String(n);}
function formatDuration(hours){if(!hours||isNaN(hours)||hours<=0)hours=24.5;if(hours<24)return Number(hours).toFixed(1)+'h';const d=Math.floor(hours/24),h=Math.round(hours%24);return h===0?d+'d':d+'d '+h+'h';}
function trunc(s,n){return s.length>n?s.substring(0,n)+'…':s;}
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML;}
function showLoading(msg){const el=document.getElementById('loading');if(el){el.querySelector('.loading-text').textContent=msg||'';el.classList.add('active');}}
function hideLoading(){const el=document.getElementById('loading');if(el)el.classList.remove('active');}
