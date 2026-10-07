# Privacy-Preserving Adaptive Insider Threat Detection and Early Warning System

Final-Year Engineering Project  
**Phase 6: Adaptive User Profiling Layer (EWMA Baselines & Behavioral Deviations)**

---

## 1. Project Overview

This project implements an intelligent, privacy-preserving insider threat detection architecture capable of detecting anomalous and potentially malicious behavioral patterns across enterprise logs while strictly safeguarding employee privacy.

### Core Stack
- **Frontend**: React.js, Tailwind CSS (Vite build system)
- **Backend**: Python 3, Flask REST API
- **Database & ORM**: MySQL, SQLAlchemy (PyMySQL driver)
- **Privacy Preservation**: Deterministic SHA-256 HMAC pseudonymization, data minimization, and segregated identity registry
- **Feature Engineering**: Chronological user-day behavioral vector aggregation (`backend/ml/feature_engineering.py`)
- **Adaptive Profiling**: Exponential Weighted Moving Average (EWMA) behavioral baselines (`backend/ml/adaptive_profile.py`)
- **Machine Learning**: pandas, NumPy, scikit-learn, Isolation Forest (Step 7)
- **Explainability**: SHAP (SHapley Additive exPlanations)
- **Testing**: Python `unittest`, pytest

---

## 2. Adaptive User Profiling Formula & Viva Guide

### Mathematical Formula:
$$\text{baseline}(t) = (1 - \alpha) \cdot \text{baseline}(t-1) + \alpha \cdot x(t)$$
$$\text{deviation}(t) = x(t) - \text{baseline}(t-1)$$

Where:
* $x(t)$: The employee's observed action on day $t$.
* $\text{baseline}(t-1)$: The established historical baseline before today's observation.
* $\text{baseline}(t)$: The updated baseline after incorporating today's observation.
* $\alpha$: The adaptation rate (default $\alpha = 0.15$).
* $\text{deviation}(t)$: The degree to which today's action departs from historical habits.

### Why EWMA is Used (Viva Defense Summary):
1. **Adaptive to Role Evolution**: Static thresholding fails because employee duties evolve over months (e.g. quarterly close, new projects). EWMA allows the profile to adapt gradually.
2. **Resistance to Sudden Poisoning**: With $\alpha = 0.15$, $85\%$ of the profile weight remains anchored to historical habits, while only $15\%$ adapts to the latest single day. A malicious insider attempting a rapid exfiltration cannot suddenly shift their baseline without producing a massive positive deviation $\Delta$.
3. **User Baseline Isolation**: Every employee has their own distinct baseline computed in isolation. A software engineer's high file access never falsely skews an accountant's baseline.
4. **Day 0 Initialization**: On an employee's first observed day ($t = 0$), $\text{baseline}(0) = x(0)$ and $\text{deviation}(0) = 0.0$.

---

## 3. Directory Structure

```text
├── backend/
│   ├── app.py                  # Flask application factory, CORS, and blueprint registration
│   ├── config.py               # Environment configuration (MySQL / SQLAlchemy / Security)
│   ├── database.py             # SQLAlchemy instance, connection testing, and table creation
│   ├── models.py               # 8 SQLAlchemy domain models with relationships and serialization
│   ├── init_db.py              # CLI automated database verification and schema creation script
│   ├── ml/
│   │   ├── __init__.py         # ML module exports
│   │   ├── feature_engineering.py # extract_behavior_features() & save_features_to_mysql()
│   │   └── adaptive_profile.py    # calculate_adaptive_profile() & get_user_profile_summary()
│   ├── privacy/
│   │   ├── __init__.py         # Privacy module exports
│   │   └── pseudonymization.py # Deterministic SHA-256 HMAC pseudonymization & Identity Vault
│   ├── data/
│   │   ├── sample_data.py      # Synthetic activity-log generator
│   │   ├── sample_data.csv     # 1,800 records across 40 users and 45 days
│   │   └── README.md           # Dataset documentation
│   ├── routes/
│   │   ├── __init__.py         # Route blueprints index
│   │   ├── health.py           # GET /api/health
│   │   ├── database_routes.py  # GET /api/database/status, /schema, and POST /api/database/init
│   │   ├── sample_data_routes.py# POST /api/generate-sample, GET /api/sample-data/preview
│   │   ├── privacy_routes.py   # POST /api/privacy/pseudonymize, /lookup, GET /api/privacy/status, /users
│   │   ├── feature_routes.py   # POST /api/features/extract, GET /api/features/preview
│   │   └── profile_routes.py   # POST /api/profile/adaptive, GET /api/profile/user/:id
│   └── tests/
│       ├── test_health.py      # Health endpoint unit tests
│       ├── test_database.py    # Database models and connection tests
│       ├── test_sample_data.py # Sample data generator tests
│       ├── test_privacy.py     # Deterministic pseudonymization tests
│       ├── test_feature_engineering.py # Behavioral feature extraction tests
│       └── test_adaptive_profile.py    # Adaptive profiling and EWMA formula tests
│
├── frontend/
│   ├── package.json            # Frontend package configuration
│   └── src/
│       ├── components/
│       │   └── Header.tsx      # Application header & live status indicator
│       ├── pages/
│       │   └── HomePage.tsx    # Unified UI with Adaptive Profiling Viva Demo, Feature Extractor, & Privacy Tester
│       ├── services/
│       │   └── api.ts          # REST client communicating with Flask backend
│       ├── charts/
│       │   └── README.md       # Placeholder for Chart.js / Recharts visualization
│       └── App.tsx             # Root React component
│
├── .env.example                # Safe configuration template
├── requirements.txt            # Python dependencies (Flask, MySQL, ML, SHAP)
├── package.json                # Integrated development scripts and dependencies
├── server.ts                   # Full-stack orchestrator (spawns Flask & serves React)
├── vite.config.ts              # Vite configuration with /api reverse proxy
└── README.md                   # Project documentation
```

---

## 4. How to Test Adaptive User Profiling

### A. Run Automated Unit Tests (36 Tests)
```bash
python3 -m unittest discover -s backend/tests
```

### B. Python CLI Verification & Viva Demonstration
```bash
python3 backend/ml/adaptive_profile.py
```

### C. Test via REST API Endpoint
```bash
curl -X POST http://localhost:5000/api/profile/adaptive \
  -H "Content-Type: application/json" \
  -d '{"alpha": 0.15, "user_id": "USR-1001", "limit": 6}'
```

### D. Via the Web Interface
Open `http://localhost:3000`:
- Adjust the **Adaptation Rate ($\alpha$)** slider (default 0.15).
- Select any user (e.g. `USR-1001` or `USR-1012`) and behavioral metric (`file_access_count`, `web_upload_volume`).
- View the step-by-step day-by-day progression table showing how the baseline evolves and generates deviations.
