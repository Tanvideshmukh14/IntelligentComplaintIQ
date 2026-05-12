"""
HVAC Complaint Intelligence System — Database Models
Enterprise-grade SQLAlchemy ORM with full ML enrichment fields.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


class ComplaintDB(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core fields
    complaint_id = Column(String(50), unique=True, index=True)
    customer_name = Column(String(200))
    date_time = Column(String(50), index=True)
    product_type = Column(String(100), index=True)
    equipment_model = Column(String(100))
    complaint_description = Column(Text)
    complaint_category = Column(String(100), index=True)
    service_location_city = Column(String(100))
    service_location_state = Column(String(100), index=True)
    customer_segment = Column(String(50))
    resolution_status = Column(String(50), index=True)
    technician_notes = Column(Text)
    communication_channel = Column(String(50))
    warranty_status = Column(String(50))
    resolution_time_hours = Column(Float)
    csat_score = Column(Float)

    # ML: Sentiment
    sentiment_score = Column(Float)
    sentiment_label = Column(String(30))

    # ML: Emotion
    emotion = Column(String(30))
    emotion_intensity = Column(Float)

    # ML: Severity
    severity_score = Column(Float)
    severity_level = Column(String(20))
    priority_rank = Column(Integer)

    # ML: Category prediction
    predicted_category = Column(String(100))
    category_confidence = Column(Float)

    # ML: Clustering
    cluster_id = Column(Integer)
    cluster_label = Column(String(200))

    # ML: Department routing
    predicted_department = Column(String(100))
    department_confidence = Column(Float)

    # ML: Escalation
    escalation_probability = Column(Float)
    escalation_risk = Column(String(20))

    # ML: Resolution time prediction
    predicted_resolution_hours = Column(Float)
    sla_breach_probability = Column(Float)

    # ML: Duplicate detection
    duplicate_group_id = Column(Integer)
    duplicate_score = Column(Float)
    is_duplicate = Column(Boolean, default=False)

    # ML: Spam detection
    spam_probability = Column(Float)
    is_spam = Column(Boolean, default=False)
    toxicity_score = Column(Float)
    fraud_risk_score = Column(Float)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_session():
    """Get a new database session."""
    return SessionLocal()
