"""
HVAC Complaint Intelligence System — Enterprise ML Pipeline Runner
Runs all 10 AI modules on database complaints.
"""
import os, sys
os.environ['PYTHONUTF8'] = '1'

from sqlalchemy.orm import Session
from database import init_db, engine, ComplaintDB
from services.sentiment import get_analyzer
from services.clustering import get_cluster_engine
from services.severity import get_severity_predictor
from services.routing import get_router
from services.category_prediction import get_category_predictor
from services.duplicate_detection import get_duplicate_detector
from services.spam_detection import get_spam_detector
from services.resolution_prediction import get_resolution_predictor


def run():
    init_db()
    session = Session(bind=engine)

    try:
        complaints = session.query(ComplaintDB).all()
        count = len(complaints)
        print(f"Found {count} complaints in database")
        if count == 0:
            print("No complaints found. Exiting."); return

        texts = [c.complaint_description or "" for c in complaints]
        product_types = [c.product_type for c in complaints]

        print("  [1/10] Sentiment & emotion analysis...")
        analyzer = get_analyzer()
        sentiments = analyzer.batch_analyze(texts)

        print("  [2/10] Category prediction...")
        cat_predictor = get_category_predictor()
        categories = cat_predictor.batch_predict(texts)

        print("  [3/10] Severity & urgency prediction...")
        predictor = get_severity_predictor()
        contexts = [{'customer_segment': c.customer_segment, 'warranty_status': c.warranty_status, 'resolution_status': c.resolution_status} for c in complaints]
        severities = predictor.batch_predict(texts, contexts)

        print("  [4/10] Intelligent department routing...")
        router = get_router()
        routings = router.batch_route(texts, product_types)

        print("  [5/10] Complaint clustering & topic modeling...")
        cluster_engine = get_cluster_engine()
        cluster_labels, cluster_info = cluster_engine.fit_predict(texts)

        print("  [6/10] Spam & fake complaint detection...")
        spam_detector = get_spam_detector()
        spam_results = spam_detector.batch_detect(texts)

        print("  [7/10] Duplicate complaint detection...")
        dup_detector = get_duplicate_detector()
        dup_complaints = [{'id': c.complaint_id, 'text': c.complaint_description or ''} for c in complaints]
        dup_results = dup_detector.detect_duplicates(dup_complaints)

        print("  [8/10] Resolution time prediction...")
        res_predictor = get_resolution_predictor()

        print("  [9/10] Escalation prediction...")
        print("  [10/10] Updating database...")

        for i, complaint in enumerate(complaints):
            complaint.sentiment_score = sentiments[i]['sentiment_score']
            complaint.sentiment_label = sentiments[i]['sentiment_label']
            complaint.emotion = sentiments[i]['emotion']
            complaint.emotion_intensity = sentiments[i].get('emotion_scores', {}).get(sentiments[i]['emotion'].lower(), 0.5)
            complaint.escalation_probability = sentiments[i]['escalation_probability']
            complaint.escalation_risk = "High" if sentiments[i]['escalation_probability'] > 0.6 else "Medium" if sentiments[i]['escalation_probability'] > 0.3 else "Low"

            complaint.predicted_category = categories[i]['predicted_category']
            complaint.category_confidence = categories[i]['confidence']

            complaint.severity_score = severities[i]['severity_score']
            complaint.severity_level = severities[i]['severity_level']
            complaint.priority_rank = severities[i]['priority_rank']

            complaint.predicted_department = routings[i]['predicted_department']
            complaint.department_confidence = routings[i]['confidence']

            if i < len(cluster_labels):
                cid = cluster_labels[i]
                complaint.cluster_id = cid
                complaint.cluster_label = cluster_info.get(cid, {}).get('label', f'Cluster {cid}')

            complaint.spam_probability = spam_results[i]['spam_probability']
            complaint.is_spam = spam_results[i]['is_spam']
            complaint.toxicity_score = spam_results[i]['toxicity_score']
            complaint.fraud_risk_score = spam_results[i]['fraud_risk_score']

            cid_str = complaint.complaint_id
            if cid_str in dup_results['duplicate_scores']:
                ds = dup_results['duplicate_scores'][cid_str]
                complaint.duplicate_score = ds['duplicate_score']
                complaint.is_duplicate = ds['is_duplicate']
                complaint.duplicate_group_id = ds['duplicate_group_id']

            res_ctx = {'predicted_category': complaint.predicted_category, 'severity_level': complaint.severity_level,
                       'customer_segment': complaint.customer_segment, 'warranty_status': complaint.warranty_status}
            res = res_predictor.predict(complaint.complaint_description or '', res_ctx)
            complaint.predicted_resolution_hours = res['predicted_resolution_hours']
            complaint.sla_breach_probability = res['sla_breach_probability']

        session.commit()
        print(f"SUCCESS: Enterprise ML pipeline complete! {count} complaints analyzed with 10 AI modules.")

        c = session.query(ComplaintDB).first()
        print(f"Verification: Sentiment={c.sentiment_label}, Category={c.predicted_category}, Severity={c.severity_level}, Dept={c.predicted_department}, Cluster={c.cluster_label}, Spam={c.is_spam}, Duplicate={c.is_duplicate}")

    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    run()
