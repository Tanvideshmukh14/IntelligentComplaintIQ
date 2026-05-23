<<<<<<< HEAD
# IntelligentConplaintIQ
IntelligentComplaintIQ is an AI-powered complaint intelligence platform that helps organizations capture, analyze, and act on customer complaints . It combines a React dashboard, FastAPI backend, WebSocket live updates, analytics charts, and NLP-driven insights to surface trends, urgency, escalation risk, and high-priority issues quickly.
=======
# 🏭 HVAC Customer Complaint Analysis System

**AI-Powered Intelligent Complaint Analytics Platform for the HVAC Industry**

An end-to-end machine learning platform that ingests, analyzes, classifies, and visualizes customer complaints from multiple channels. Features automated sentiment analysis, severity detection, complaint clustering, department routing, and a premium interactive dashboard with actionable KPIs.

---

## ✨ Features

### AI & ML Capabilities
- **Sentiment Analysis** — VADER-inspired scoring with HVAC-specific lexicon, emotion detection (Frustration, Anger, Fear, Urgency, Confusion), and escalation probability
- **Severity Prediction** — Hybrid rule-based + keyword scoring with contextual adjustments for customer segment, warranty status, and safety risks
- **Complaint Clustering** — TF-IDF vectorization + K-Means with automatic topic labeling (Cooling Failures, Heating Issues, Installation Problems, System Failures, Warranty Disputes)
- **Department Routing** — Multi-class keyword classifier routing complaints to 10 business departments with confidence scoring
- **Predictive Analytics** — Complaint volume forecasting, emerging defect detection, customer churn risk prediction
- **AI Recommendations** — Automated maintenance suggestions, product redesign alerts, training recommendations

### Dashboard Sections (9 Tabs)
1. **Executive Overview** — Total complaints, open/resolved/escalated counts, CSAT, NPS, resolution rate
2. **Sentiment Dashboard** — Sentiment distribution, emotion analysis, trends over time, product sentiment comparison
3. **Severity Dashboard** — Critical/high priority counts, severity by product, critical alerts panel
4. **Clusters & Topics** — ML-identified complaint groups, cluster trends, detailed cluster breakdown
5. **Department Performance** — Complaints by department, resolution rates, SLA compliance, performance table
6. **Geographic Insights** — Complaints by state/city, severity index, seasonal climate patterns
7. **Complaints Table** — Full searchable/paginated complaint browser with filtering
8. **AI Analyzer** — Real-time complaint analysis tool (paste any complaint text for instant AI results)
9. **Predictions** — Forecast charts, emerging issues, churn risk, AI-driven recommendations

### Data Pipeline
- Synthetic data generator producing 2,500+ realistic HVAC complaints
- Supports CSV and Excel file uploads
- Automatic data cleaning, missing value handling, text preprocessing
- SQLite database with full complaint schema

---

## 📁 Project Structure

```
hvac-complaint-analysis/
├── requirements.txt          # Python dependencies
├── setup.bat                 # Windows: First-time setup (install + generate data + run ML)
├── setup.sh                  # Linux/Mac: First-time setup
├── start.bat                 # Windows: Launch the dashboard server
├── start.sh                  # Linux/Mac: Launch the dashboard server
├── README.md                 # This file
│
├── backend/
│   ├── config.py             # Configuration (paths, settings)
│   ├── database.py           # SQLAlchemy models & database setup
│   ├── generate_data.py      # Synthetic HVAC complaint data generator (2500+ records)
│   ├── main.py               # FastAPI application (REST API + server)
│   ├── run_pipeline.py       # Standalone ML pipeline runner
│   ├── data/
│   │   ├── complaints.db     # SQLite database (generated)
│   │   └── complaints_raw.csv# Raw CSV export (generated)
│   ├── ml_models/            # Saved ML model artifacts (auto-created)
│   └── services/
│       ├── __init__.py
│       ├── analytics.py      # KPI computation, trends, predictions, recommendations
│       ├── clustering.py     # TF-IDF + K-Means complaint clustering engine
│       ├── routing.py        # Department classification & routing
│       ├── sentiment.py      # Sentiment & emotion analysis engine
│       └── severity.py       # Severity prediction engine
│
└── frontend/
    ├── index.html            # Main dashboard HTML (9 tab sections)
    ├── css/
    │   └── dashboard.css     # Premium dark theme with glassmorphism
    └── js/
        ├── api.js            # API client for frontend-backend communication
        ├── charts.js         # Chart.js configuration & chart builders
        └── app.js            # Main application controller (tabs, data loading, filtering)
```

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** installed and in PATH
- **pip** package manager

### Option 1: One-Click (Windows)

**First time:**
```
Double-click setup.bat
```
This installs dependencies, generates 2,500 synthetic complaints, and runs the ML pipeline.

**Every time after:**
```
Double-click start.bat
```
Opens the dashboard at http://localhost:8000 automatically.

### Option 2: Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic data
cd backend
python generate_data.py

# 3. Run ML analysis pipeline
python run_pipeline.py

# 4. Start the server
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Then open **http://localhost:8000** in your browser.

---

## 🔌 REST API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Dashboard HTML |
| `/api/health` | GET | Health check |
| `/api/filters` | GET | Available filter options |
| `/api/dashboard/overview` | GET | Executive KPIs |
| `/api/dashboard/sentiment` | GET | Sentiment analytics |
| `/api/dashboard/severity` | GET | Severity analytics |
| `/api/dashboard/clusters` | GET | Clustering analytics |
| `/api/dashboard/departments` | GET | Department performance |
| `/api/dashboard/geographic` | GET | Geographic insights |
| `/api/dashboard/products` | GET | Product quality KPIs |
| `/api/dashboard/predictions` | GET | Predictive analytics |
| `/api/dashboard/recommendations` | GET | AI recommendations |
| `/api/complaints` | GET | Paginated complaints list |
| `/api/analyze` | POST | Analyze a single complaint |
| `/api/upload` | POST | Upload CSV/Excel file |
| `/api/run-pipeline` | POST | Trigger ML pipeline |

All dashboard endpoints support query parameters for filtering: `start_date`, `end_date`, `product_type`, `severity_level`, `department`, `channel`, `status`, `segment`, `state`.

---

## 📊 KPIs Tracked

### Customer Experience
- Customer Satisfaction Score (CSAT)
- Net Promoter Score (NPS)
- Complaint Escalation Rate
- Customer Churn Risk

### Operational
- Mean Time to Resolution (MTTR)
- SLA Compliance %
- Resolution Rate by Department
- Average Handling Time

### Product Quality
- Failure Frequency by HVAC Model
- Warranty Claim Rate
- Repeat Failure Rate
- Severity by Product Type

### AI Performance
- Sentiment Distribution Accuracy
- Clustering Coherence (5 distinct clusters)
- Severity Detection Coverage
- Department Routing Confidence

---

## 🛠 Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, FastAPI, Uvicorn |
| **ML/NLP** | scikit-learn (TF-IDF, K-Means), Custom VADER-inspired sentiment engine |
| **Database** | SQLite via SQLAlchemy ORM |
| **Frontend** | HTML5, CSS3 (glassmorphism dark theme), Vanilla JavaScript |
| **Charts** | Chart.js 4.x (doughnut, bar, line, polar area, radar) |
| **Typography** | Inter (Google Fonts) |

---

## 📋 Supported Complaint Fields

| Field | Description |
|---|---|
| Complaint ID | Unique identifier (HVAC-YYYY-NNNNN) |
| Customer Name | Customer full name |
| Date & Time | Complaint timestamp |
| Product Type | HVAC equipment category (10 types) |
| Equipment Model | Specific model number |
| Complaint Description | Full complaint text |
| Service Location | City and State |
| Customer Segment | Residential / Commercial / Industrial |
| Resolution Status | Open / In Progress / Resolved / Escalated / Closed |
| Technician Notes | Service technician notes |
| Communication Channel | CRM / Email / Phone / Chat / Survey / Social Media / Service Portal |
| Warranty Status | Active / Expired / Not Applicable |

---

## 📄 License

This project is for educational and demonstration purposes.
>>>>>>> 9dcd80f (Add Project Files)
#   I n t e l l i g e n t C o m p l a i n t I Q  
 