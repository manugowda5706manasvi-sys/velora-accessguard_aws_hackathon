# AccessGuard AI — Progress Tracker

## How to resume
Open this file first. Run the command in "Commands to run now". Then tell me "resume".

---

## Stage Checklist

| # | Stage | Status |
|---|-------|--------|
| 1 | Structure, deps, config files | ✅ DONE |
| 2 | Data generator + validator + tests | ✅ DONE (74/74 pass) |
| 3 | IsolationForest + scoring + tests | ✅ DONE (74/74 pass) |
| 4 | Rules + baselines + risk combiner + tests | ✅ DONE (74/74 pass) |
| 5 | FastAPI backend + React frontend | 🟡 CHECKPOINT (90/90 pass) |
| 6 | Upload flow end-to-end | ⬜ TODO |
| 7 | Review workflow + audit chain + alerts + tests | ⬜ TODO |
| 8 | Full test run + README + docs → CHECKPOINT | ⬜ TODO |
| 9 | AWS feasibility → approval → deploy | ⬜ TODO |
| 10 | Live verification → FINAL CHECKPOINT | ⬜ TODO |

---

## What Works
- Project directory structure created
- `requirements.txt` (pinned), `.gitignore`, `.env.example`, `conftest.py`, `.env` in place
- Synthetic dataset generator (`scripts/generate_data.py`), 250 records in `data/sample_access.csv`
- Strict validator (`backend/app/ml/validator.py`) with CSV formula injection neutralisation
- Unsupervised Isolation Forest anomaly detector (`backend/app/ml/anomaly.py`) with 0-100 scoring & z-score explainability
- Transparent rules engine & baseline calculator (`backend/app/rules/engine.py`)
- SQLite storage backend with SHA-256 tamper-evident audit hash chain (`backend/app/storage/base.py`)
- FastAPI REST API with JWT auth, rate limiting, security headers, and Mangum Lambda adapter (`backend/app/main.py`, `backend/app/api/`)
- Responsive React + Vite cybersecurity dashboard with Recharts, WCAG AA contrast, table filters, review drawer, audit verifier (`frontend/`)
- 90/90 unit and integration tests passing (`pytest -q`)

## What Is Broken
- Nothing

## Decisions Made
- Storage: SQLite local / DynamoDB AWS, toggled by `STORAGE_BACKEND` env var
- ML: IsolationForest(n_estimators=200, contamination=0.08, random_state=42)
- Feature set: 6 numeric features (permission_count, sensitive_access_count, inactive_days, off_hours_access_count, failed_logins_7d, role_mismatch)
- Anomaly score: 0-100, higher = more unusual. Formula: `score = (1 - (raw_score - min) / (max - min)) * 100` where raw_score = decision_function output
- Risk level: High requires ≥1 rule hit + anomaly flag; Medium = anomaly only OR 1 rule hit; Low = neither
- Auth: JWT token (HS256), constant-time compare, 5 req/min rate limit on /auth/login
- Frontend: Single-page React app with Vite proxy, dark security theme, accessible controls

## Commands to Run Now
```powershell
# In terminal 1 (backend):
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

# In terminal 2 (frontend):
cd frontend
npm run dev

# Open in browser:
http://localhost:5173/

# Run all 90 tests:
.venv\Scripts\python.exe -m pytest -q
```



## File Map
```
aws_hackethon/
├── PROJECT_BRIEF.md
├── PROGRESS.md
├── README.md              (Stage 8)
├── conftest.py
├── requirements.txt
├── .env.example
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── api/           (Stage 5)
│   │   ├── ml/            (Stage 3)
│   │   ├── rules/         (Stage 4)
│   │   ├── storage/       (Stage 5)
│   │   └── schemas/       (Stage 5)
│   └── tests/
├── data/
│   └── sample_access.csv  (Stage 2)
├── docs/                  (Stage 8)
├── frontend/              (Stage 5)
├── infra/                 (Stage 9)
└── scripts/
```
