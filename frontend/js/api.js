/* IntelligentComplaintIQ — API Client */
const API = {
  BASE: '',

  async get(endpoint, params = {}) {
    const url = new URL(endpoint, window.location.origin);
    Object.entries(params).forEach(([k, v]) => { if (v) url.searchParams.set(k, v); });
    const res = await fetch(url);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },

  async post(endpoint, data) {
    const res = await fetch(endpoint, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },

  async uploadFile(file) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/upload', { method: 'POST', body: form });
    if (!res.ok) throw new Error(`Upload error: ${res.status}`);
    return res.json();
  },

  async ingestData(filepath, mapping) {
    const form = new FormData();
    form.append('filepath', filepath);
    form.append('mapping', JSON.stringify(mapping));
    const res = await fetch('/api/ingest', { method: 'POST', body: form });
    if (!res.ok) throw new Error(`Ingest error: ${res.status}`);
    return res.json();
  },

  getFilters() { return this.get('/api/filters'); },
  getOverview(f) { return this.get('/api/dashboard/overview', f); },
  getSentiment(f) { return this.get('/api/dashboard/sentiment', f); },
  getSeverity(f) { return this.get('/api/dashboard/severity', f); },
  getClusters(f) { return this.get('/api/dashboard/clusters', f); },
  getDuplicates() { return this.get('/api/dashboard/duplicates'); },
  getDepartments(f) { return this.get('/api/dashboard/departments', f); },
  getPredictions() { return this.get('/api/dashboard/predictions'); },
  getRecommendations() { return this.get('/api/dashboard/recommendations'); },
  getComplaints(params) { return this.get('/api/complaints', params); },
  analyzeComplaint(data) { return this.post('/api/analyze', data); },
  runPipeline() { return this.post('/api/run-pipeline', {}); },

  async autoAnalyze(filename) {
    const form = new FormData();
    form.append('filename', filename);
    const res = await fetch('/api/auto-analyze', { method: 'POST', body: form });
    if (!res.ok) throw new Error(`Analysis error: ${res.status}`);
    return res.json();
  },

  async uploadAndActivate(file) {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch('/api/upload-and-activate', { method: 'POST', body: form });
    if (!res.ok) throw new Error(`Activation error: ${res.status}`);
    return res.json();
  },
};
