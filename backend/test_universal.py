"""Test the upload + auto-analyze endpoints."""
import requests, json, os, sys
os.environ['PYTHONUTF8'] = '1'

BASE = 'http://localhost:8000'
FILE = r'c:\Users\muska\.gemini\antigravity\scratch\hvac-complaint-analysis\dataset\carrier_complaints_2000.csv'

print("=== UPLOAD TEST ===")
r = requests.post(f'{BASE}/api/upload', files={'file': open(FILE, 'rb')})
d = r.json()
print(f"Status: {d['status']}")
print(f"Rows: {d['rows']}, Columns: {len(d['columns'])}")

si = d.get('schema_intelligence', {})
print(f"Dataset Type: {si.get('dataset_type')}")
print(f"Summary: {si.get('summary')}")
print(f"Quality Score: {si.get('data_quality', {}).get('quality_score')}%")
print(f"Applicable Analyses: {len(si.get('applicable_analyses', []))}")
for a in si.get('applicable_analyses', []):
    print(f"  {a['icon']} {a['label']}")

# Show semantic mapping
print("\n=== SEMANTIC MAPPING ===")
for col, info in list(si.get('semantic_mapping', {}).items())[:10]:
    print(f"  {col:35s} -> {info['detected_type']:12s} | {info['semantic_role']:20s} | {info['confidence']:.2f}")

print("\n=== AUTO-ANALYZE TEST ===")
r2 = requests.post(f'{BASE}/api/auto-analyze', data={'filename': d['filename']})
results = r2.json()
print(f"Status: {results['status']}")
res = results.get('results', {})
print(f"KPIs: {len(res.get('kpis', []))}")
print(f"Charts: {len(res.get('charts', []))}")
print(f"Insights: {len(res.get('insights', []))}")
print(f"Analyses run: {list(res.get('analyses', {}).keys())}")

for kpi in res.get('kpis', []):
    print(f"  {kpi['icon']} {kpi['label']}: {kpi['value']}")

print("\nInsights:")
for i in res.get('insights', []):
    print(f"  [{i['priority'].upper()}] {i['icon']} {i['title']}: {i['message']}")

print("\nCharts:")
for c in res.get('charts', []):
    print(f"  {c['type']:10s} | {c['title']}")
