# KGP LIST — Mobile Spare-Parts Catalog & Ordering Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Alembic](https://img.shields.io/badge/Alembic-1.13+-red.svg)](https://alembic.sqlalchemy.org/)
[![Tests](https://img.shields.io/badge/pytest-62%20passed-brightgreen.svg)]()

> **Phase 2B: Real Authentication & Authorization Foundation**  
> Complete with JWT Bearer tokens, Granular RBAC, Customer Phone OTP, Order Ownership, Persistent Idempotency, and Rate Limiting.

---

## 1. System Mission

**KGP LIST** is an enterprise-grade mobile catalog and ordering system engineered for spare-parts suppliers, retail stores, and repair technicians across Algeria. 

The complete platform includes:
- **Android Customer Application:** Flutter-based mobile app for repair technicians.
- **Administration Web Dashboard:** Responsive web dashboard for catalog and order management.
- **Backend API:** High-performance Python FastAPI service.
- **Relational Database:** PostgreSQL 16 with decimal currency and historical snapshotting.
- **Push Notifications:** Firebase Cloud Messaging (FCM) integration (Phase 3).
- **Bulk Imports:** Excel/XLSX product price and inventory imports (Phase 3).

---

## 2. Repository Structure

```
kgp-list/
├── backend/                        # Python FastAPI backend service
│   ├── app/
│   │   ├── main.py                 # Application entrypoint & lifespan
│   │   ├── core/                   # Central config, structured logging, errors, security
│   │   ├── api/                    # Versioned API routes (/api/v1) & dependencies
│   │   ├── models/                 # SQLAlchemy 2.0 ORM models (8 core entities)
│   │   ├── schemas/                # Pydantic v2 validation models with Decimal support
│   │   ├── services/               # Product & Order business operations
│   │   └── db/                     # Connection pool session manager & metadata base
│   ├── alembic/                    # Database migration scripts & env.py
│   ├── tests/                      # Automated pytest suite (30 passing tests)
│   ├── requirements.txt            # Locked backend dependencies
│   ├── pyproject.toml              # Project metadata & pytest configuration
│   └── .env.example                # Centralized environment template
├── admin/                          # Web Admin Dashboard (Architecture & Roadmap)
├── mobile/                         # Flutter Customer Mobile App (Architecture & Roadmap)
├── database/                       # Docker Compose & PostgreSQL initialization scripts
├── deployment/                     # Multi-stage Dockerfile, production Compose, runbook
├── docs/                           # Architecture, Data Model (ERD), API Guide, Troubleshooting
├── .gitignore                      # Comprehensive exclusion rules
└── README.md                       # This developer documentation
```

---

## 3. Developer Quickstart (Windows PowerShell)

### Prerequisites
- Python 3.11+ (Python 3.14 verified)
- Windows PowerShell

### Step 1: Clone and Set Active Workspace
Open PowerShell:
```powershell
# Set workspace directory
Set-Location "C:\Users\youcef djamel hadjab\.gemini\antigravity\scratch\kgp-list\backend"
```

### Step 2: Set Up Virtual Environment & Dependencies
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
```powershell
# Copy environment configuration
Copy-Item .env.example .env
```

### Step 4: Run Automated Tests
```powershell
# Execute pytest suite
pytest -v
```
*(Result: 62 passed, 2 skipped integration tests for live PostgreSQL)*

### Step 5: Start Local PostgreSQL (Docker)
```powershell
Set-Location "..\database"
docker compose up -d
Set-Location "..\backend"
```

### Step 6: Run Database Migrations
```powershell
alembic upgrade head
```

### Step 7: Launch FastAPI Backend Server
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 4. Interactive API Documentation

Once started, open your web browser:
- **Interactive Swagger UI:** [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- **ReDoc Reference:** [http://127.0.0.1:8000/api/redoc](http://127.0.0.1:8000/api/redoc)
- **Health Check Endpoint:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 5. Architectural Pillars

1. **Exact Decimal Pricing:**
   Selling prices and order totals use `Numeric(12, 2)` and Python `Decimal` rather than floating-point arithmetic.
2. **Historical Order Preservation:**
   `OrderItem` snapshots product name, SKU, and unit price at time of order creation. Future price updates or product name revisions will never mutate historical order data.
3. **Information Security:**
   - Production CORS rejects wildcards (`*`).
   - Phone numbers and tokens are redacted from logs.
   - Internal stack traces are never sent to clients.
   - Clients never access PostgreSQL directly.

---

## 6. Comprehensive Documentation Links

- [System Architecture & Communication Model](docs/ARCHITECTURE.md)
- [Database Schema & ERD](docs/DATA_MODEL.md)
- [API Contract & Endpoints Guide](docs/API_GUIDE.md)
- [Troubleshooting & FAQ](docs/TROUBLESHOOTING.md)
- [Production Deployment Runbook](deployment/README.md)
