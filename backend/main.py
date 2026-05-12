"""
HVAC Complaint Intelligence System — FastAPI Application
Enterprise-grade API server with 10 AI modules and full analytics.
"""
import os, sys, io, json
import pandas as pd
import numpy as np
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

from config import STATIC_DIR, DATA_DIR, UPLOADS_DIR
from database import init_db, engine, ComplaintDB

from services.sentiment import get_analyzer
from services.clustering import get_cluster_engine
from services.severity import get_severity_predictor
from services.routing import get_router
from services.analytics import get_analytics_engine
from services.category_prediction import get_category_predictor
from services.duplicate_detection import get_duplicate_detector
from services.spam_detection import get_spam_detector
from services.resolution_prediction import get_resolution_predictor
from services.data_ingestion import get_ingestion_engine
from services.schema_intelligence import get_schema_engine
from services.universal_analytics import get_universal_analytics

app = FastAPI(title="IntelligentComplaintIQ", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


# --- Pydantic Models ---
class ComplaintInput(BaseModel):
    complaint_text: str
    product_type: Optional[str] = None
    customer_segment: Optional[str] = None
    warranty_status: Optional[str] = None

class ColumnMapping(BaseModel):
    mapping: Dict[str, str]


# --- Helper ---
def get_complaints_df(filters=None):
    session = Session(bind=engine)
    try:
        query = session.query(ComplaintDB)
        if filters:
            if filters.get('start_date'): query = query.filter(ComplaintDB.date_time >= filters['start_date'])
            if filters.get('end_date'): query = query.filter(ComplaintDB.date_time <= filters['end_date'])
            if filters.get('product_type'): query = query.filter(ComplaintDB.product_type == filters['product_type'])
            if filters.get('severity_level'): query = query.filter(ComplaintDB.severity_level == filters['severity_level'])
            if filters.get('department'): query = query.filter(ComplaintDB.predicted_department == filters['department'])
            if filters.get('channel'): query = query.filter(ComplaintDB.communication_channel == filters['channel'])
            if filters.get('status'): query = query.filter(ComplaintDB.resolution_status == filters['status'])
            if filters.get('segment'): query = query.filter(ComplaintDB.customer_segment == filters['segment'])
            if filters.get('state'): query = query.filter(ComplaintDB.service_location_state == filters['state'])
        complaints = query.all()
        if not complaints:
            return pd.DataFrame()
        data = []
        for c in complaints:
            row = {}
            for col in ComplaintDB.__table__.columns:
                row[col.name] = getattr(c, col.name, None)
            data.append(row)
        df = pd.DataFrame(data)
        if 'date_time' in df.columns:
            df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')
        return df
    finally:
        session.close()


def _build_filters(**kwargs):
    return {k: v for k, v in kwargs.items() if v}


def run_ml_pipeline():
    """Run all 10 AI modules on database complaints."""
    print("[ML] Starting enterprise ML pipeline (10 modules)...")
    session = Session(bind=engine)
    try:
        complaints = session.query(ComplaintDB).all()
        if not complaints:
            print("[WARN] No complaints found."); return

        texts = [c.complaint_description or "" for c in complaints]
        product_types = [c.product_type for c in complaints]

        # 1. Sentiment & Emotion
        print("  [1/10] Sentiment & emotion analysis...")
        analyzer = get_analyzer()
        sentiments = analyzer.batch_analyze(texts)

        # 2. Category prediction
        print("  [2/10] Category prediction...")
        cat_predictor = get_category_predictor()
        categories = cat_predictor.batch_predict(texts)

        # 3. Severity prediction
        print("  [3/10] Severity & urgency prediction...")
        predictor = get_severity_predictor()
        contexts = [{'customer_segment': c.customer_segment, 'warranty_status': c.warranty_status, 'resolution_status': c.resolution_status} for c in complaints]
        severities = predictor.batch_predict(texts, contexts)

        # 4. Department routing
        print("  [4/10] Intelligent department routing...")
        router = get_router()
        routings = router.batch_route(texts, product_types)

        # 5. Clustering
        print("  [5/10] Complaint clustering & topic modeling...")
        cluster_engine = get_cluster_engine()
        cluster_labels, cluster_info = cluster_engine.fit_predict(texts)

        # 6. Spam detection
        print("  [6/10] Spam & fake complaint detection...")
        spam_detector = get_spam_detector()
        spam_results = spam_detector.batch_detect(texts)

        # 7. Duplicate detection
        print("  [7/10] Duplicate complaint detection...")
        dup_detector = get_duplicate_detector()
        dup_complaints = [{'id': c.complaint_id, 'text': c.complaint_description or ''} for c in complaints]
        dup_results = dup_detector.detect_duplicates(dup_complaints)

        # 8. Resolution time prediction
        print("  [8/10] Resolution time prediction...")
        res_predictor = get_resolution_predictor()

        # 9-10. Escalation (from sentiment) + update DB
        print("  [9/10] Escalation prediction...")
        print("  [10/10] Updating database...")

        for i, complaint in enumerate(complaints):
            # Sentiment
            complaint.sentiment_score = sentiments[i]['sentiment_score']
            complaint.sentiment_label = sentiments[i]['sentiment_label']
            complaint.emotion = sentiments[i]['emotion']
            complaint.emotion_intensity = sentiments[i].get('emotion_scores', {}).get(sentiments[i]['emotion'].lower(), 0.5)
            complaint.escalation_probability = sentiments[i]['escalation_probability']
            complaint.escalation_risk = "High" if sentiments[i]['escalation_probability'] > 0.6 else "Medium" if sentiments[i]['escalation_probability'] > 0.3 else "Low"

            # Category
            complaint.predicted_category = categories[i]['predicted_category']
            complaint.category_confidence = categories[i]['confidence']

            # Severity
            complaint.severity_score = severities[i]['severity_score']
            complaint.severity_level = severities[i]['severity_level']
            complaint.priority_rank = severities[i]['priority_rank']

            # Routing
            complaint.predicted_department = routings[i]['predicted_department']
            complaint.department_confidence = routings[i]['confidence']

            # Clustering
            if i < len(cluster_labels):
                cid = cluster_labels[i]
                complaint.cluster_id = cid
                complaint.cluster_label = cluster_info.get(cid, {}).get('label', f'Cluster {cid}')

            # Spam
            complaint.spam_probability = spam_results[i]['spam_probability']
            complaint.is_spam = spam_results[i]['is_spam']
            complaint.toxicity_score = spam_results[i]['toxicity_score']
            complaint.fraud_risk_score = spam_results[i]['fraud_risk_score']

            # Duplicates
            cid_str = complaint.complaint_id
            if cid_str in dup_results['duplicate_scores']:
                ds = dup_results['duplicate_scores'][cid_str]
                complaint.duplicate_score = ds['duplicate_score']
                complaint.is_duplicate = ds['is_duplicate']
                complaint.duplicate_group_id = ds['duplicate_group_id']

            # Resolution prediction
            res_ctx = {'predicted_category': complaint.predicted_category, 'severity_level': complaint.severity_level,
                       'customer_segment': complaint.customer_segment, 'warranty_status': complaint.warranty_status}
            res = res_predictor.predict(complaint.complaint_description or '', res_ctx)
            complaint.predicted_resolution_hours = res['predicted_resolution_hours']
            complaint.sla_breach_probability = res['sla_breach_probability']

        session.commit()
        print(f"[OK] Enterprise ML pipeline complete! {len(complaints)} complaints analyzed with 10 AI modules.")
    except Exception as e:
        session.rollback()
        print(f"[ERROR] ML pipeline: {e}")
        raise
    finally:
        session.close()


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        with open(index_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>HVAC Intelligence System</h1><p>Frontend not found.</p>")

@app.get("/api/health")
async def health():
    session = Session(bind=engine)
    count = session.query(ComplaintDB).count()
    session.close()
    return {"status": "healthy", "version": "2.0.0", "complaints": count, "timestamp": datetime.now().isoformat(), "modules": ["sentiment", "emotion", "category", "severity", "routing", "clustering", "spam", "duplicate", "resolution", "escalation"]}

@app.post("/api/analyze")
async def analyze_complaint(complaint: ComplaintInput):
    text = complaint.complaint_text
    analyzer = get_analyzer()
    predictor = get_severity_predictor()
    router = get_router()
    cat_predictor = get_category_predictor()
    spam_detector = get_spam_detector()
    res_predictor = get_resolution_predictor()

    sentiment = analyzer.analyze_sentiment(text)
    category = cat_predictor.predict_category(text)
    severity = predictor.predict_severity(text, {'customer_segment': complaint.customer_segment, 'warranty_status': complaint.warranty_status})
    routing = router.route_complaint(text, complaint.product_type)
    spam = spam_detector.detect(text)
    resolution = res_predictor.predict(text, {'predicted_category': category['predicted_category'], 'severity_level': severity['severity_level'], 'customer_segment': complaint.customer_segment, 'warranty_status': complaint.warranty_status})

    return {"sentiment": sentiment, "category": category, "severity": severity, "routing": routing, "spam_analysis": spam, "resolution_prediction": resolution}


# --- Dashboard APIs ---

@app.get("/api/dashboard/overview")
async def get_overview(start_date: Optional[str]=None, end_date: Optional[str]=None, product_type: Optional[str]=None, channel: Optional[str]=None, status: Optional[str]=None, segment: Optional[str]=None, state: Optional[str]=None):
    df = get_complaints_df(_build_filters(start_date=start_date, end_date=end_date, product_type=product_type, channel=channel, status=status, segment=segment, state=state))
    return get_analytics_engine().compute_executive_overview(df)

@app.get("/api/dashboard/sentiment")
async def get_sentiment(start_date: Optional[str]=None, end_date: Optional[str]=None, product_type: Optional[str]=None, segment: Optional[str]=None, state: Optional[str]=None):
    df = get_complaints_df(_build_filters(start_date=start_date, end_date=end_date, product_type=product_type, segment=segment, state=state))
    return get_analytics_engine().compute_sentiment_analytics(df)

@app.get("/api/dashboard/severity")
async def get_severity(start_date: Optional[str]=None, end_date: Optional[str]=None, product_type: Optional[str]=None, segment: Optional[str]=None):
    df = get_complaints_df(_build_filters(start_date=start_date, end_date=end_date, product_type=product_type, segment=segment))
    return get_analytics_engine().compute_severity_analytics(df)

@app.get("/api/dashboard/clusters")
async def get_clusters(start_date: Optional[str]=None, end_date: Optional[str]=None, product_type: Optional[str]=None):
    df = get_complaints_df(_build_filters(start_date=start_date, end_date=end_date, product_type=product_type))
    return get_analytics_engine().compute_cluster_analytics(df)

@app.get("/api/dashboard/duplicates")
async def get_duplicates():
    df = get_complaints_df()
    return get_analytics_engine().compute_duplicate_spam_analytics(df)

@app.get("/api/dashboard/departments")
async def get_departments(start_date: Optional[str]=None, end_date: Optional[str]=None, product_type: Optional[str]=None):
    df = get_complaints_df(_build_filters(start_date=start_date, end_date=end_date, product_type=product_type))
    return get_analytics_engine().compute_department_analytics(df)

@app.get("/api/dashboard/geographic")
async def get_geographic(start_date: Optional[str]=None, end_date: Optional[str]=None, product_type: Optional[str]=None):
    df = get_complaints_df(_build_filters(start_date=start_date, end_date=end_date, product_type=product_type))
    return get_analytics_engine().compute_geographic_analytics(df)

@app.get("/api/dashboard/products")
async def get_products(start_date: Optional[str]=None, end_date: Optional[str]=None):
    df = get_complaints_df(_build_filters(start_date=start_date, end_date=end_date))
    return get_analytics_engine().compute_product_kpis(df)

@app.get("/api/dashboard/predictions")
async def get_predictions():
    return get_analytics_engine().compute_predictions(get_complaints_df())

@app.get("/api/dashboard/recommendations")
async def get_recommendations():
    return get_analytics_engine().compute_recommendations(get_complaints_df())


# --- Complaints CRUD ---

@app.get("/api/complaints")
async def get_complaints(page: int=1, page_size: int=50, sort_by: str="date_time", sort_order: str="desc", search: Optional[str]=None,
    start_date: Optional[str]=None, end_date: Optional[str]=None, product_type: Optional[str]=None, severity_level: Optional[str]=None,
    department: Optional[str]=None, status: Optional[str]=None, segment: Optional[str]=None, channel: Optional[str]=None, state: Optional[str]=None):
    df = get_complaints_df(_build_filters(start_date=start_date, end_date=end_date, product_type=product_type, severity_level=severity_level, department=department, status=status, segment=segment, channel=channel, state=state))
    if len(df) == 0:
        return {"complaints": [], "total": 0, "page": page, "pages": 0}
    if search:
        mask = df['complaint_description'].str.contains(search, case=False, na=False)
        if 'customer_name' in df.columns: mask |= df['customer_name'].str.contains(search, case=False, na=False)
        if 'complaint_id' in df.columns: mask |= df['complaint_id'].str.contains(search, case=False, na=False)
        df = df[mask]
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=sort_order == "asc", na_position='last')
    total = len(df)
    pages = max(1, (total + page_size - 1) // page_size)
    page_df = df.iloc[(page-1)*page_size : page*page_size]
    complaints = []
    for _, row in page_df.iterrows():
        record = row.to_dict()
        for k, v in record.items():
            if isinstance(v, pd.Timestamp): record[k] = v.isoformat()
            elif isinstance(v, (np.floating, np.integer)): record[k] = None if np.isnan(v) else float(v)
            elif pd.isna(v): record[k] = None
        complaints.append(record)
    return {"complaints": complaints, "total": total, "page": page, "pages": pages, "page_size": page_size}

@app.get("/api/filters")
async def get_filters():
    df = get_complaints_df()
    if len(df) == 0:
        return {}
    result = {"severity_levels": ["Low", "Medium", "High", "Critical"]}
    for key, col in [("product_types", "product_type"), ("departments", "predicted_department"), ("channels", "communication_channel"), ("statuses", "resolution_status"), ("segments", "customer_segment"), ("states", "service_location_state")]:
        if col in df.columns:
            result[key] = sorted(df[col].dropna().unique().tolist())
    if 'date_time' in df.columns:
        result["date_range"] = {"min": df['date_time'].min().isoformat(), "max": df['date_time'].max().isoformat()}
    return result


# --- Universal Dataset Upload & Auto-Analysis ---

# Store last uploaded dataset in memory for analysis
_uploaded_datasets = {}

@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload any dataset — AI auto-detects schema and column meanings."""
    if not file.filename:
        raise HTTPException(400, "No file provided")
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ('csv', 'xlsx', 'xls', 'json'):
        raise HTTPException(400, "Supported formats: CSV, Excel, JSON")
    try:
        contents = await file.read()
        filepath = os.path.join(UPLOADS_DIR, f"uploaded_{file.filename}")
        with open(filepath, 'wb') as f:
            f.write(contents)
        ingestion = get_ingestion_engine()
        df = ingestion.read_file(filepath, ext)
        # AI Schema Intelligence
        schema_engine = get_schema_engine()
        schema_result = schema_engine.analyze_schema(df)
        # Store for subsequent auto-analyze
        _uploaded_datasets[file.filename] = {"filepath": filepath, "df": df, "schema": schema_result}
        return {
            "status": "success", "filename": file.filename, "filepath": filepath,
            "rows": len(df), "columns": list(df.columns),
            "schema_intelligence": schema_result,
        }
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/auto-analyze")
async def auto_analyze(filename: str = Form(...)):
    """Run universal AI analytics on the uploaded dataset."""
    try:
        if filename not in _uploaded_datasets:
            # Try to find the file
            filepath = os.path.join(UPLOADS_DIR, f"uploaded_{filename}")
            if not os.path.exists(filepath):
                raise HTTPException(404, f"Dataset '{filename}' not found. Please upload first.")
            ingestion = get_ingestion_engine()
            ext = filename.rsplit('.', 1)[-1].lower()
            df = ingestion.read_file(filepath, ext)
            schema_engine = get_schema_engine()
            schema_result = schema_engine.analyze_schema(df)
            _uploaded_datasets[filename] = {"filepath": filepath, "df": df, "schema": schema_result}

        dataset = _uploaded_datasets[filename]
        analytics = get_universal_analytics()
        results = analytics.run_all(dataset["df"], dataset["schema"])
        return {"status": "success", "filename": filename, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(500, str(e))

@app.post("/api/ingest")
async def ingest_dataset(filepath: str = Form(...), mapping: str = Form("{}")):
    try:
        ingestion = get_ingestion_engine()
        column_mapping = json.loads(mapping) if mapping else {}
        df = ingestion.read_file(filepath)
        if column_mapping:
            df = ingestion.apply_mapping(df, column_mapping)
        df, preprocess_stats = ingestion.preprocess_dataframe(df)
        session = Session(bind=engine)
        try:
            ingest_stats = ingestion.ingest_to_database(df, session, ComplaintDB, column_mapping)
            return {"status": "success", "preprocessing": preprocess_stats, "ingestion": ingest_stats}
        finally:
            session.close()
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/run-pipeline")
async def trigger_pipeline():
    try:
        run_ml_pipeline()
        return {"status": "success", "message": "Enterprise ML pipeline completed (10 modules)"}
    except Exception as e:
        raise HTTPException(500, str(e))


# --- Startup ---

@app.on_event("startup")
async def startup():
    init_db()
    session = Session(bind=engine)
    count = session.query(ComplaintDB).count()
    session.close()
    print(f"[DB] Database: {count} complaints")


if __name__ == "__main__":
    import uvicorn
    if "--setup" in sys.argv:
        init_db()
        from generate_data import generate_complaints, save_to_database, save_to_csv
        complaints = generate_complaints(2500)
        save_to_csv(complaints)
        save_to_database(complaints)
        run_ml_pipeline()
    uvicorn.run(app, host="0.0.0.0", port=8000)
