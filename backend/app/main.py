"""
Main FastAPI application entrypoint for AccessGuard AI.
Configures CORS, security headers, routers, and Mangum adapter for AWS Lambda.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from backend.app.api.routes import router as api_router, _process_and_store_df
from backend.app.config import get_settings
from backend.app.ml.validator import validate_csv
from backend.app.storage.base import get_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan: ensures initial sample data is analysed and loaded
    so the demo is ready immediately upon startup.
    """
    try:
        storage = get_storage()
        latest_run = storage.get_latest_run_id()
        if not latest_run:
            sample_path = "./data/sample_access.csv"
            if os.path.exists(sample_path):
                with open(sample_path, "rb") as f:
                    val_res = validate_csv(f.read(), filename="sample_access.csv")
                    if val_res.is_valid:
                        _process_and_store_df(
                            val_res.df,
                            source_label="initial_sample_load",
                            storage=storage,
                            actor="system_init",
                        )
    except Exception as e:
        # Never crash startup if sample data file isn't present yet
        print(f"[Init Warning] Could not auto-load sample data: {e}")
    yield


app = FastAPI(
    title="AccessGuard AI",
    description="SaaS Access Risk & Permission Drift Detection Decision-Support Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS Configuration ────────────────────────────────────────────────────────
settings = get_settings()
origins = [
    settings.frontend_origin,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://localhost:8000",
    "*",  # Permissive for hackathon demo testing across ports
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Security Headers Middleware ───────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── Mount API Routes ──────────────────────────────────────────────────────────
# Both root and /api prefixes for flexibility with frontend & cloud deployments
app.include_router(api_router, prefix="/api")
app.include_router(api_router)


# ── AWS Lambda Handler ────────────────────────────────────────────────────────
handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
