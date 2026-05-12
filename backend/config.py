"""
HVAC Complaint Intelligence System — Configuration
Enterprise-grade configuration for all modules.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "ml_models")
STATIC_DIR = os.path.join(BASE_DIR, "..", "frontend")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")

# Create directories
for d in [DATA_DIR, MODELS_DIR, UPLOADS_DIR]:
    os.makedirs(d, exist_ok=True)

# Database
DB_PATH = os.path.join(DATA_DIR, "complaints.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ML Pipeline Settings
CLUSTER_COUNT = 8
MIN_CLUSTER_SIZE = 10
DUPLICATE_THRESHOLD = 0.85
SPAM_THRESHOLD = 0.6
ESCALATION_THRESHOLD = 0.65

# SLA Targets (hours)
SLA_TARGETS = {
    "Critical": 12,
    "High": 24,
    "Medium": 48,
    "Low": 72,
}

# Department list
DEPARTMENTS = [
    "Technical Support", "Installation Team", "Field Service",
    "Warranty Department", "Product Quality", "Customer Support",
    "IoT/Smart HVAC Team", "Maintenance", "Supply Chain", "Quality Assurance",
]

# Complaint categories
CATEGORIES = [
    "Cooling Failure", "Heating Failure", "Gas Leakage",
    "Installation Problem", "Maintenance Issue", "Warranty Complaint",
    "Thermostat Connectivity", "High Energy Consumption",
    "Noise Issue", "Water Leakage", "Customer Service Issue",
    "Electrical Failure", "Refrigerant Leak", "Compressor Failure",
]
