# ===== COPY EVERYTHING BELOW THIS LINE INTO ANTIGRAVITY =====

# PROJECT: AccessGuard AI — SaaS Access Risk & Permission Drift Detection
Team Velora, REVA University. Hackathon: IMPULSE '26 (AWS Student Builder Group), 24 hours. I am a beginner CSE student.

## 0. FIRST ACTION — SAVE THIS BRIEF, THEN WORK CHEAPLY
1. Save this entire message unchanged as `PROJECT_BRIEF.md` in the project root. From now on, read that file instead of asking me to repeat anything.
2. Create `PROGRESS.md` (stage checklist, what works, what is broken, exact commands to run, decisions made). Update it at the end of every stage. If I open a new chat, I will say "resume", and you will continue from PROGRESS.md.
3. Inspect the workspace first. Then show me a SHORT plan (max 25 lines) and start Stage 1 without waiting for approval. Stop only at the checkpoints marked CHECKPOINT.

## 1. ROLE AND GOAL
Act as senior full-stack engineer, ML engineer and AWS architect. Build a complete, working web application (not a mockup) that uses AI to analyse consented SaaS roles, permissions, access history and usage, identifies excessive, outdated or anomalous access, and gives explainable early warnings and recommendations for permissions an administrator should review or revoke. It is a decision-support tool: NEVER revoke or change real permissions.

## 2. CREDIT AND EFFORT RULES (strict — my Antigravity credits are limited and must last until the project is finished)
- Work one stage at a time. Do not start the next stage until the current one passes its tests.
- Write each file once, completely and correctly. No placeholder code, no "TODO", no rewrites of working files. Edit with small diffs only.
- Do NOT paste full files or long logs into chat. Reply per stage in at most 15 lines: what was built, test result (pass/fail counts), the exact commands for me to run, next step.
- Do not re-read or re-scan files you have not changed. Do not re-explain earlier stages.
- Run tests quietly (`pytest -q`, `npm run build --silent`), show only failures.
- Maximum 3 fix attempts on one bug. After that, stop, summarise the cause in 5 lines and ask me.
- Use browser or screenshot verification only twice: once after the frontend is working (Stage 5) and once on the final deployed URL (Stage 10). Use API/curl tests otherwise.
- No new dependency unless essential. Pinned versions in `requirements.txt` and `package.json`.
- Never run installers, `aws` commands or anything that creates cloud resources without asking me first. Ask for approval before each AWS command group.
- Priority order if credits run low: (1) working local app with real ML, (2) tests, (3) live AWS deployment, (4) docs. Tell me when you are about halfway through your budget, and keep the app always runnable.

## 3. MEASURABLE SCOPE
**MUST build (all of these):**
1. Synthetic dataset generator (seeded, reproducible) producing about 250 employee-access records across 5 SaaS apps (GitHub, Google Workspace, AWS Console, Slack, Jira) with role, department, and ~8–10% injected risky patterns (excessive permissions, stale access, off-hours bursts, failed-login spikes, role mismatch). Also include 6 labelled showcase employees (2 High, 2 Medium, 2 Low) that tell clear stories for judges (e.g. "moved from Finance to Marketing but still has finance-system admin"). Store `data/sample_access.csv`.
2. CSV upload with validation. Required columns: `employee_id, permission_count, sensitive_access_count, inactive_days, off_hours_access_count, failed_logins_7d, role_mismatch`. Optional: `employee_name, role, department, app`. Reject: wrong type, negative values, missing required columns, duplicate IDs, empty file, file over 1 MB or over 5,000 rows, non-CSV. Missing numeric values are reported per row, not silently guessed. Show clear human-readable errors. Neutralise CSV-formula injection (cells starting with `= + - @`).
3. Real ML: scikit-learn `IsolationForest` (see section 5).
4. Transparent rules + role-permission baselines (see section 5). If no `role` column exists, skip baseline drift rules and say so in the UI. Never fake it.
5. For every record: anomaly score (0–100), anomaly flag, rule hits, risk level (Low/Medium/High), plain-language explanation ("why flagged"), and recommendation (review permissions / investigate unusual activity / consider revoking unnecessary access).
6. Dashboard: total records analysed, anomalies flagged, high-risk count, review-status counts, risk-distribution chart, risk-by-app chart, anomaly-score distribution, top reasons chart, and an in-app **Alerts feed** of newest High/Medium findings (our "early warning").
7. Employee-access table with search, filters (risk, app, status, anomaly), sorting, pagination, and a detail panel with the explanation and the top contributing features.
8. Admin review workflow: Pending Review → Investigating → Resolved (with a required comment, and "Accepted risk" / "Access reduced (manual action recorded)" outcomes). The app only RECORDS decisions; wording must say "recommended / recorded", never "revoked".
9. Audit history: append-only, every analysis run, upload, status change and comment is logged with timestamp, actor, action. Make it tamper-evident with a SHA-256 hash chain (each entry stores the previous entry's hash) and a "Verify audit integrity" button that really recomputes the chain. Add CSV export of the audit log.
10. Simple admin login (single demo admin; password from environment variable, never hardcoded or committed) protecting every API route except `/health`.
11. System-status page: real health check, model parameters, dataset info, active storage backend, and an honest architecture diagram of what is ACTUALLY deployed (plus a clearly separate "future architecture" section).
12. "Reset demo data" button that really works, so the demo is repeatable.
13. Tests, README, docs, judge demo script (section 10).

**WON'T build (state these as limitations/roadmap, not as features):** real SaaS API connectors (AppFlow etc.), automated revocation, Bedrock/SageMaker/Lookout use, multi-tenant accounts, real-time streaming. Do not display UI for them.

## 4. TECH STACK (keep it simple)
- Backend: Python 3.12, FastAPI, pandas, numpy, scikit-learn, pytest. Keep the dependency list small. Backend code must run in AWS Lambda via Mangum (or equivalent) AND locally with `uvicorn`.
- Frontend: React + Vite, plain CSS (or one small CSS lib), Recharts for charts. Responsive, WCAG-AA contrast, keyboard-accessible controls, labels on all inputs, charts have text alternatives/tables.
- Storage: one small storage interface with two implementations: SQLite (local) and DynamoDB (AWS, on-demand) — selected by an environment variable. Lambda's filesystem is temporary, so SQLite cannot hold the review/audit data in the cloud. Do not use more storage services than this.
- Layout: `backend/app/{api,ml,rules,storage,schemas}`, `backend/tests`, `frontend/src`, `data/`, `docs/`, `infra/`, `scripts/`.

## 5. ML AND RISK LOGIC (this is what judges will question — it must be real and explainable)
- Features (all 7): permission_count, sensitive_access_count, inactive_days, off_hours_access_count, failed_logins_7d, role_mismatch (0/1), plus employee_id as identifier only (never a feature).
- Pipeline: validate → impute only where documented → `StandardScaler` → `IsolationForest(n_estimators=200, contamination=0.08 (configurable), random_state=42)`. Train on the dataset being analysed (unsupervised). Convert `score_samples` / `decision_function` to a 0–100 anomaly score (higher = more unusual). Document the exact formula.
- Per-record "why anomalous": show the top 3 features whose value deviates most from the population (or role-group) median using z-scores. Do not claim SHAP or LIME.
- Rules (configurable thresholds in one file, documented): excessive permissions (above role baseline, or above the 90th percentile if no role), stale/outdated access (inactive_days above threshold while holding sensitive access), role mismatch with sensitive access, unusual activity (off-hours and failed-login spikes), unused-privilege combination.
- Role-permission baselines: per-role median/limits computed from the data (or a small configurable table). Permission drift = permissions above baseline for the current role.
- Risk level: documented table combining rule points and anomaly flag. Anomaly alone with no rule evidence is capped at Medium with the label "Anomaly — investigate". High requires rule evidence. Explain clearly in the UI and docs: **an anomaly is a statistical outlier, not a confirmed security risk or proof of an attack; drift needs a baseline or other reliable evidence; a human must review.**
- Model quality (honest): because the generator injects known risky records, report precision/recall/F1 against that synthetic ground truth in `docs/MODEL_EVALUATION.md` and label it "synthetic data only, not real-world validation". Never invent accuracy numbers; compute them in a test.

## 6. AWS: MINIMUM, JUSTIFIED, HONEST
The judging sheet requires the final demo to run LIVE ON AWS, not localhost (judges score AWS selection 15, architecture and security 15, scalability and cost 10). Target architecture (verify before building):
- **AWS Lambda + Function URL** hosts the FastAPI backend and ML.
- **Amazon S3** (static website hosting) hosts the built React app.
- **Amazon DynamoDB** (on-demand) stores reviews and the audit log.
That is 3 services, each with one clear purpose. Do not add more.

Before writing deployment code, in `docs/AWS_FEASIBILITY.md` check and report (using current official AWS documentation, not memory): (a) whether the Lambda package with numpy+scipy+scikit-learn fits Lambda limits (zip 50 MB direct / 250 MB unzipped; if too big, the smallest alternative such as S3-uploaded zip, a slimmer build, or a container image, with cost implications); (b) free-tier and always-free eligibility of Lambda, S3, DynamoDB for MY account type, which you cannot see, so tell me what to check in my own billing console; (c) S3 static hosting is HTTP only: say whether that is acceptable or whether CloudFront is needed and what it may cost; (d) a Function URL with AuthType NONE is public, so state how we protect it. If one service cannot satisfy "live on AWS", say so plainly and give the minimum alternative and its possible cost. Never claim "deployed on AWS", "free", or "compliant" until verified by an actual successful deployment test.

Cost and safety safeguards (required):
- Do not create resources, upgrade the account, or enable anything chargeable without my explicit approval each time.
- No SageMaker endpoints, Bedrock calls, OpenSearch, NAT gateways, load balancers, or EC2. If you think one is needed, stop and ask with the cost.
- Lambda: small memory, short timeout, reserved concurrency cap, and request-size limits. DynamoDB: on-demand with minimal tables. S3: private except the static site files.
- Give me exact steps to create a zero-spend/budget alert in AWS Billing and to use a least-privilege IAM user (not root). I will run them. Never ask me to paste secrets into chat. No credentials in code, git or logs.
- Infra as simple scripts (`infra/deploy.sh` or AWS SAM, whichever is simpler and verified) with a matching `infra/teardown.sh` that deletes everything. Document exactly what is created.
- Keep the app fully runnable locally at all times.

## 7. SECURITY AND DATA HANDLING
Synthetic data only by default; the UI states the CSV must contain consented data. Secrets via environment variables only (`.env.example` provided, `.env` in `.gitignore`). Login-protected API with constant-time password comparison, simple rate limiting on login, CORS restricted to the frontend origin, security headers, upload validation (type, size, rows, no execution of file contents), no employee data or secrets in logs, input validation with Pydantic, and read-only behaviour toward any SaaS. Write `docs/SECURITY.md`: threat list, what we do, what we don't (be honest, e.g. HTTP-only S3 endpoint, single demo admin, no MFA).

## 8. UI
Pages: Overview, Employee Access (table + detail panel), Review Queue and Audit Log, Upload Data, System Status and Architecture. Every visible button must work. No fake controls, no hardcoded results shown as AI, no decorative integrations. Loading, empty and error states everywhere. Consistent typography, professional dark or light security-dashboard look, mobile-responsive, and a small "How this works" explanation of Isolation Forest, anomalies vs risk.

## 9. STAGES (stop at each CHECKPOINT; run tests before moving on)
1. Structure, dependencies, `PROGRESS.md`, `.gitignore`, `.env.example`.
2. Data generator + `sample_access.csv` + validation module + tests.
3. Isolation Forest module + scoring + tests (reproducibility, anomalies ranked above normal, injected anomalies mostly detected, bad input rejected).
4. Rules, baselines, risk combiner, explanations, recommendations + tests.
5. FastAPI endpoints (auth, upload, analyse, records, filters, review, audit, verify-audit, reset, health) + React dashboard. Check in the browser once. **CHECKPOINT: I run it locally and approve.**
6. Upload flow end to end, incl. bad-file handling.
7. Review workflow, hash-chained audit log, alerts feed + tests.
8. Full test run, bug-fix pass, README, docs. **CHECKPOINT: local app complete.**
9. AWS feasibility doc → ask my approval → build Lambda package, DynamoDB storage backend, S3 frontend, deploy scripts. Test against the live URL with automated smoke tests.
10. Live verification, judge demo rehearsal, final checklist. **FINAL CHECKPOINT.**

## 10. REQUIRED FILES
`README.md` (exact setup/run/test commands for Windows, plus deploy commands), `PROGRESS.md`, `requirements.txt`, `.env.example`, `data/sample_access.csv`, `docs/ARCHITECTURE.md` (diagram, data flow, current vs future), `docs/AWS_FEASIBILITY.md`, `docs/AWS_SELECTION.md` (why each service, and why SageMaker/Bedrock/OpenSearch/AppFlow were NOT used for the MVP and where they would fit at scale), `docs/SECURITY.md`, `docs/SCALABILITY_AND_COST.md` (how this scales, estimated cost behaviour, upgrade path), `docs/MODEL_EXPLAINED.md` (simple language, for team understanding), `docs/MODEL_EVALUATION.md`, `docs/FEATURES_AND_LIMITATIONS.md` (implemented vs not, known bugs, honest), `docs/INNOVATION.md` (explainable hybrid ML+rules+baseline, tamper-evident audit, human-in-the-loop, no auto-revoke), `docs/JUDGE_DEMO_SCRIPT.md` (5-minute script with exact clicks and the 6 showcase employees), `docs/PITCH_QA.md` (15 likely judge questions with honest answers, incl. "why not SageMaker/Bedrock?", "is this really AI?", "what are the limits?"), `infra/` scripts, tests.

## 11. FINAL VERIFICATION CHECKLIST (report pass/fail with evidence; do not claim anything not actually run)
- Problem and use case: README opens with the problem and the users.
- AWS selection: each AWS service has a documented purpose and alternatives considered.
- Architecture and security: diagram matches what is really deployed; SECURITY.md complete; no secrets in repo.
- Feature plan and scope: MUST list all implemented, limitations listed.
- Scalability and cost: documented, no unapproved charges, teardown script tested.
- Innovation: documented.
- Team understanding: MODEL_EXPLAINED + PITCH_QA written in simple words.
- Features implemented: every MUST item demonstrated by a test or a manual step.
- Working demo: live AWS URL passes smoke tests; login, upload bad file, upload good file, filter, review, audit verify, reset all work live; there is a local fallback demo.
- Honest disclosure: known bugs and limitations listed.
- All tests pass (give counts from the real run).

Begin now with section 0.

# ===== END OF PROMPT =====
