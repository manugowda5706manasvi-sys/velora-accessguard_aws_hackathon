# AccessGuard AI — SaaS Access Risk & Permission Drift Detection

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/manugowda5706manasvi-sys/velora-accessguard_aws_hackathon)

> **Team Velora — REVA University**  
> Hackathon: **IMPULSE '26 (AWS Student Builder Group)**

AccessGuard AI is a decision-support system for investigating employee SaaS access risk. The default workflow searches an employee by ID or name, shows their available application assignments and permissions, and presents evidence-backed findings and review recommendations.

**Data-source status:** the current employee directory contains synthetic demo profiles only. No live identity provider or SaaS platform is connected. Application names, permissions, activity evidence, and last-used labels in these profiles are sample data; do not treat them as records fetched from a company system.

## Employee Access Risk Scanner

The scanner is the default landing page and does not require a CSV upload. Use the employee ID/name search or choose a sample profile to review the employee's application inventory, role baseline comparisons, findings, and recommended next steps. The report can be downloaded as CSV. Recommendations are read-only and require human review; the scanner does not grant or revoke access.

The backend endpoints are:

- `GET /api/scanner/suggestions` — synthetic demo search suggestions.
- `GET /api/scanner/employees?query=EMP-1042` — find an employee by ID or name and return that profile's access analysis. Unknown employees return `404`.

When the backend cannot be reached, the static frontend can use the labeled local synthetic fixtures. For production, set the frontend build variable `VITE_API_URL` to the deployed backend origin; it must not contain credentials. The Vite `localhost:8000` proxy is for local development only.

Risk scoring is deterministic: the highest finding severity contributes its base score (Critical 90, High 75, Medium 40, Low 10); each additional finding at that same severity adds 5, capped at 100. Score bands are Critical (90–100), High (70–89), Medium (30–69), and Low (0–29). The number of assigned applications or total permissions is not itself a score input. Permission rows are sample evidence and may not enumerate every permission included in an application's reported total.

---

## 🚀 1-Click Cloud Deployment (Render Free Tier)

Deploy both the FastAPI backend and React frontend directly to Render with zero cost:

1. Click the button below:  
   [![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/manugowda5706manasvi-sys/velora-accessguard_aws_hackathon)
2. Log in with your GitHub account on Render.
3. Review the services defined in [`render.yaml`](./render.yaml) (`accessguard-backend` on the Free plan, and `accessguard-frontend` as a Free static site).
4. Click **Apply** to deploy.

---

## 💻 Local Setup & Development

### 1. Backend Setup (FastAPI + ML)
```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
Copy-Item .env.example .env

# Run FastAPI backend server (port 8000)
.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Setup (React + Vite)
```powershell
cd frontend
npm install
npm run dev
```
Open **`http://localhost:5173/`** in your browser.

### 3. Run Tests
```powershell
.venv\Scripts\python.exe -m pytest -q
```
Runs the unit, ML pipeline, rules-engine, scanner, and API integration tests.

---

## 🧠 Architecture & Principles
- **Unsupervised Anomaly Detection**: `scikit-learn` Isolation Forest (`n_estimators=200`, `contamination=0.08`, `random_state=42`) with population-median z-score explainability.
- **Role-Permission Baselines**: Deterministic drift calculation against role medians.
- **Employee Scanner**: Synthetic directory lookup, role-baseline comparison, evidence-linked findings, and employee-specific CSV reports.
- **Tamper-Evident Audit Trail**: Uploads, employee risk analyses, and administrative decisions are cryptographically chained using SHA-256 hashes.
- **Decision-Support Only**: Does NOT automatically revoke or modify permissions — records human administrative reviews with mandatory audit commentary.
