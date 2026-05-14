/* IntelligentComplaintIQ — Chart Factory */
const COLORS = {
  blue: '#6366f1', cyan: '#06b6d4', green: '#10b981', red: '#ef4444',
  orange: '#f59e0b', purple: '#a855f7', pink: '#ec4899', teal: '#14b8a6',
  indigo: '#818cf8', amber: '#fbbf24', emerald: '#34d399', rose: '#fb7185',
  slate: '#64748b', lime: '#84cc16', sky: '#38bdf8', violet: '#8b5cf6',
};
const PALETTE = [COLORS.blue, COLORS.cyan, COLORS.green, COLORS.orange, COLORS.purple, COLORS.pink, COLORS.teal, COLORS.red, COLORS.indigo, COLORS.amber, COLORS.emerald, COLORS.rose, COLORS.lime, COLORS.sky, COLORS.violet, COLORS.slate];
const SEVERITY_COLORS = { Critical: COLORS.red, High: COLORS.orange, Medium: COLORS.blue, Low: COLORS.green };
const SENTIMENT_COLORS = { 'Highly Negative': '#dc2626', Negative: COLORS.red, Neutral: COLORS.slate, Positive: COLORS.green };

const chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) { chartInstances[id].destroy(); delete chartInstances[id]; }
}

const CHART_DEFAULTS = {
  responsive: true, maintainAspectRatio: false,
  plugins: {
    legend: { position: 'top', align: 'end', labels: { color: '#94a3b8', font: { family: 'Inter', size: 10 }, padding: 8, boxWidth: 8, usePointStyle: true, pointStyleWidth: 8 } },
    tooltip: { backgroundColor: 'rgba(17,24,39,0.95)', titleColor: '#f1f5f9', bodyColor: '#94a3b8', borderColor: 'rgba(99,102,241,0.3)', borderWidth: 1, padding: 10, cornerRadius: 8, titleFont: { family: 'Inter', size: 12, weight: '600' }, bodyFont: { family: 'Inter', size: 11 } }
  },
  scales: {
    x: { ticks: { color: '#64748b', font: { family: 'Inter', size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' }, border: { color: 'rgba(255,255,255,0.08)' } },
    y: { ticks: { color: '#64748b', font: { family: 'Inter', size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' }, border: { color: 'rgba(255,255,255,0.08)' } }
  }
};

function createChart(canvasId, type, labels, datasets, customOpts = {}) {
  destroyChart(canvasId);
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  
  const opts = JSON.parse(JSON.stringify(CHART_DEFAULTS));
  if (type === 'doughnut' || type === 'pie' || type === 'polarArea') {
    delete opts.scales;
  }
  Object.assign(opts, customOpts);
  if (customOpts.plugins) Object.assign(opts.plugins, customOpts.plugins);
  
  chartInstances[canvasId] = new Chart(ctx, { type, data: { labels, datasets }, options: opts });
  return chartInstances[canvasId];
}

function createDoughnut(canvasId, data, colors) {
  const labels = Object.keys(data);
  const values = Object.values(data);
  const bgColors = colors || labels.map((_, i) => PALETTE[i % PALETTE.length]);
  return createChart(canvasId, 'doughnut', labels, [{
    data: values, backgroundColor: bgColors,
    borderColor: 'rgba(10,14,26,0.8)', borderWidth: 2, hoverOffset: 6,
  }], { cutout: '65%' });
}

function createBar(canvasId, labels, values, color, label = 'Count') {
  return createChart(canvasId, 'bar', labels, [{
    label, data: values, backgroundColor: color || COLORS.blue + '99',
    borderColor: color || COLORS.blue, borderWidth: 1, borderRadius: 4, maxBarThickness: 40,
  }]);
}

function createHorizontalBar(canvasId, labels, values, colors) {
  const bgColors = colors || labels.map((_, i) => PALETTE[i % PALETTE.length] + '99');
  const borderColors = colors || labels.map((_, i) => PALETTE[i % PALETTE.length]);
  return createChart(canvasId, 'bar', labels, [{
    label: 'Count', data: values, backgroundColor: bgColors, borderColor: borderColors,
    borderWidth: 1, borderRadius: 4,
  }], { indexAxis: 'y', plugins: { legend: { display: false } } });
}

function createLineChart(canvasId, labels, datasets) {
  const ds = datasets.map((d, i) => ({
    label: d.label, data: d.data,
    borderColor: d.color || PALETTE[i % PALETTE.length],
    backgroundColor: (d.color || PALETTE[i % PALETTE.length]) + '15',
    borderWidth: 2, fill: d.fill || false, tension: 0.3,
    pointRadius: 3, pointHoverRadius: 5,
    pointBackgroundColor: d.color || PALETTE[i % PALETTE.length],
  }));
  return createChart(canvasId, 'line', labels, ds);
}

function createStackedBar(canvasId, labels, datasets) {
  const ds = datasets.map((d, i) => ({
    label: d.label, data: d.data,
    backgroundColor: (d.color || PALETTE[i % PALETTE.length]) + '99',
    borderColor: d.color || PALETTE[i % PALETTE.length],
    borderWidth: 1, borderRadius: 2,
  }));
  return createChart(canvasId, 'bar', labels, ds, {
    scales: { ...CHART_DEFAULTS.scales, x: { ...CHART_DEFAULTS.scales.x, stacked: true }, y: { ...CHART_DEFAULTS.scales.y, stacked: true } }
  });
}
