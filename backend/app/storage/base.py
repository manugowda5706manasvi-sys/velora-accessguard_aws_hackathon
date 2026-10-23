"""
Storage interface for AccessGuard AI.

Two implementations:
  - SQLiteStorage  (local; selected when STORAGE_BACKEND=sqlite)
  - DynamoDBStorage (AWS; selected when STORAGE_BACKEND=dynamodb)

Selected by the STORAGE_BACKEND environment variable.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

# ── Abstract interface ────────────────────────────────────────────────────────

class StorageBackend(ABC):
    """Base interface for all storage backends."""

    @abstractmethod
    def save_analysis_run(self, run_data: dict) -> str:
        """Persist an analysis run; return run_id."""

    @abstractmethod
    def get_records(
        self,
        run_id: str,
        risk_level: Optional[str] = None,
        app: Optional[str] = None,
        review_status: Optional[str] = None,
        is_anomaly: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "anomaly_score",
        sort_desc: bool = True,
    ) -> dict:
        """Return paginated records dict: {items, total, page, page_size}."""

    @abstractmethod
    def get_record(self, run_id: str, employee_id: str) -> Optional[dict]:
        """Return a single record by run_id + employee_id."""

    @abstractmethod
    def update_review_status(
        self,
        run_id: str,
        employee_id: str,
        status: str,
        comment: str,
        outcome: Optional[str],
        actor: str,
    ) -> None:
        """Update the review status of a record."""

    @abstractmethod
    def get_latest_run_id(self) -> Optional[str]:
        """Return the most recent run_id, or None if no runs exist."""

    @abstractmethod
    def append_audit_entry(self, entry: dict) -> str:
        """Append an audit log entry; return entry_id."""

    @abstractmethod
    def get_audit_log(self, limit: int = 500) -> list[dict]:
        """Return audit log entries, newest first."""

    @abstractmethod
    def reset(self) -> None:
        """Delete all data (for demo reset)."""


# ── Audit chain helper ────────────────────────────────────────────────────────

def _hash_entry(entry: dict, prev_hash: str) -> str:
    """Compute SHA-256 of entry content + prev_hash."""
    payload = json.dumps(
        {k: v for k, v in sorted(entry.items()) if k not in ("hash", "prev_hash")},
        sort_keys=True, default=str
    ) + prev_hash
    return hashlib.sha256(payload.encode()).hexdigest()


# ── SQLite implementation ─────────────────────────────────────────────────────

class SQLiteStorage(StorageBackend):
    """SQLite-backed storage for local development."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS analysis_runs (
        run_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        record_count INTEGER,
        anomaly_count INTEGER,
        high_risk_count INTEGER,
        metadata TEXT
    );

    CREATE TABLE IF NOT EXISTS records (
        run_id TEXT NOT NULL,
        employee_id TEXT NOT NULL,
        employee_name TEXT,
        role TEXT,
        department TEXT,
        app TEXT,
        permission_count INTEGER,
        sensitive_access_count INTEGER,
        inactive_days INTEGER,
        off_hours_access_count INTEGER,
        failed_logins_7d INTEGER,
        role_mismatch INTEGER,
        anomaly_score REAL,
        is_anomaly INTEGER,
        raw_if_score REAL,
        risk_level TEXT,
        explanation TEXT,
        recommendation TEXT,
        rule_hits TEXT,
        top_features TEXT,
        permission_drift REAL,
        role_baseline INTEGER,
        review_status TEXT DEFAULT 'Pending Review',
        review_comment TEXT,
        review_outcome TEXT,
        review_actor TEXT,
        review_at TEXT,
        PRIMARY KEY (run_id, employee_id)
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        entry_id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        prev_hash TEXT NOT NULL,
        hash TEXT NOT NULL,
        seq INTEGER NOT NULL
    );
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript(self.SCHEMA)

    def _last_hash(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT hash FROM audit_log ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return row["hash"] if row else "0" * 64

    def save_analysis_run(self, run_data: dict) -> str:
        run_id = run_data["run_id"]
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO analysis_runs VALUES (?,?,?,?,?,?)",
                (
                    run_id,
                    run_data.get("created_at", datetime.now(timezone.utc).isoformat()),
                    run_data.get("record_count", 0),
                    run_data.get("anomaly_count", 0),
                    run_data.get("high_risk_count", 0),
                    json.dumps(run_data.get("metadata", {})),
                ),
            )
            for rec in run_data.get("records", []):
                conn.execute(
                    """INSERT OR REPLACE INTO records
                    (run_id, employee_id, employee_name, role, department, app,
                     permission_count, sensitive_access_count, inactive_days,
                     off_hours_access_count, failed_logins_7d, role_mismatch,
                     anomaly_score, is_anomaly, raw_if_score, risk_level,
                     explanation, recommendation, rule_hits, top_features,
                     permission_drift, role_baseline)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        run_id,
                        rec["employee_id"],
                        rec.get("employee_name"),
                        rec.get("role"),
                        rec.get("department"),
                        rec.get("app"),
                        rec.get("permission_count"),
                        rec.get("sensitive_access_count"),
                        rec.get("inactive_days"),
                        rec.get("off_hours_access_count"),
                        rec.get("failed_logins_7d"),
                        rec.get("role_mismatch"),
                        rec.get("anomaly_score"),
                        int(rec.get("is_anomaly", False)),
                        rec.get("raw_if_score"),
                        rec.get("risk_level"),
                        rec.get("explanation"),
                        rec.get("recommendation"),
                        json.dumps(rec.get("rule_hits", [])),
                        json.dumps(rec.get("top_features", [])),
                        rec.get("permission_drift"),
                        rec.get("role_baseline"),
                    ),
                )
        return run_id

    def get_records(
        self,
        run_id: str,
        risk_level=None,
        app=None,
        review_status=None,
        is_anomaly=None,
        search=None,
        page=1,
        page_size=50,
        sort_by="anomaly_score",
        sort_desc=True,
    ) -> dict:
        # Whitelist sort columns to prevent SQL injection
        allowed_sort = {
            "anomaly_score", "employee_id", "risk_level", "permission_count",
            "inactive_days", "failed_logins_7d",
        }
        if sort_by not in allowed_sort:
            sort_by = "anomaly_score"
        order = "DESC" if sort_desc else "ASC"

        where = ["run_id = ?"]
        params: list = [run_id]

        if risk_level:
            where.append("risk_level = ?")
            params.append(risk_level)
        if app:
            where.append("app = ?")
            params.append(app)
        if review_status:
            where.append("review_status = ?")
            params.append(review_status)
        if is_anomaly is not None:
            where.append("is_anomaly = ?")
            params.append(1 if is_anomaly else 0)
        if search:
            where.append("(employee_id LIKE ? OR employee_name LIKE ? OR role LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like, like])

        where_clause = " AND ".join(where)
        with self._conn() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM records WHERE {where_clause}", params
            ).fetchone()[0]
            offset = (page - 1) * page_size
            rows = conn.execute(
                f"SELECT * FROM records WHERE {where_clause} "
                f"ORDER BY {sort_by} {order} LIMIT ? OFFSET ?",
                params + [page_size, offset],
            ).fetchall()

        items = []
        for row in rows:
            d = dict(row)
            d["is_anomaly"] = bool(d["is_anomaly"])
            d["rule_hits"] = json.loads(d["rule_hits"] or "[]")
            d["top_features"] = json.loads(d["top_features"] or "[]")
            items.append(d)

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_record(self, run_id: str, employee_id: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM records WHERE run_id=? AND employee_id=?",
                (run_id, employee_id),
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["is_anomaly"] = bool(d["is_anomaly"])
        d["rule_hits"] = json.loads(d["rule_hits"] or "[]")
        d["top_features"] = json.loads(d["top_features"] or "[]")
        return d

    def update_review_status(self, run_id, employee_id, status, comment, outcome, actor):
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            conn.execute(
                """UPDATE records SET review_status=?, review_comment=?,
                review_outcome=?, review_actor=?, review_at=?
                WHERE run_id=? AND employee_id=?""",
                (status, comment, outcome, actor, now, run_id, employee_id),
            )

    def get_latest_run_id(self) -> Optional[str]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT run_id FROM analysis_runs ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
        return row["run_id"] if row else None

    def append_audit_entry(self, entry: dict) -> str:
        entry_id = str(uuid.uuid4())
        ts = entry.get("timestamp", datetime.now(timezone.utc).isoformat())
        actor = entry.get("actor", "system")
        action = entry["action"]
        details = entry.get("details", {})
        with self._conn() as conn:
            prev_hash = self._last_hash(conn)
            seq = (conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]) + 1
            canonical_entry = {
                "entry_id": entry_id,
                "timestamp": ts,
                "actor": actor,
                "action": action,
                "details": details,
                "seq": seq,
            }
            h = _hash_entry(canonical_entry, prev_hash)
            conn.execute(
                """INSERT INTO audit_log
                (entry_id, timestamp, actor, action, details, prev_hash, hash, seq)
                VALUES (?,?,?,?,?,?,?,?)""",
                (
                    entry_id,
                    ts,
                    actor,
                    action,
                    json.dumps(details),
                    prev_hash,
                    h,
                    seq,
                ),
            )
        return entry_id

    def get_audit_log(self, limit: int = 500) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY seq DESC LIMIT ?", (limit,)
            ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["details"] = json.loads(d["details"] or "{}")
            result.append(d)
        return result

    def verify_audit_chain(self) -> dict:
        """Recompute the hash chain and return {valid: bool, first_bad_seq: int|None, total_entries: int}."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY seq ASC"
            ).fetchall()
        prev_hash = "0" * 64
        for row in rows:
            d = dict(row)
            d["details"] = json.loads(d["details"] or "{}")
            canonical_entry = {
                "entry_id": d["entry_id"],
                "timestamp": d["timestamp"],
                "actor": d["actor"],
                "action": d["action"],
                "details": d["details"],
                "seq": d["seq"],
            }
            expected = _hash_entry(canonical_entry, prev_hash)
            if expected != d["hash"]:
                return {"valid": False, "first_bad_seq": d["seq"], "total_entries": len(rows)}
            if d["prev_hash"] != prev_hash:
                return {"valid": False, "first_bad_seq": d["seq"], "total_entries": len(rows)}
            prev_hash = d["hash"]
        return {"valid": True, "first_bad_seq": None, "total_entries": len(rows)}

    def reset(self) -> None:
        with self._conn() as conn:
            conn.executescript("""
                DELETE FROM records;
                DELETE FROM analysis_runs;
                DELETE FROM audit_log;
            """)


# ── DynamoDB stub (implemented in Stage 9) ───────────────────────────────────

class DynamoDBStorage(StorageBackend):
    """DynamoDB-backed storage for AWS deployment. Implemented in Stage 9."""

    def __init__(self):
        import boto3
        self._dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.getenv("DYNAMODB_REGION", "ap-south-1"),
        )
        self._records_table = self._dynamodb.Table(
            os.getenv("DYNAMODB_RECORDS_TABLE", "accessguard-records")
        )
        self._audit_table = self._dynamodb.Table(
            os.getenv("DYNAMODB_AUDIT_TABLE", "accessguard-audit")
        )

    def save_analysis_run(self, run_data: dict) -> str:
        raise NotImplementedError("DynamoDB backend: implemented in Stage 9")

    def get_records(self, run_id, **kwargs) -> dict:
        raise NotImplementedError("DynamoDB backend: implemented in Stage 9")

    def get_record(self, run_id, employee_id) -> Optional[dict]:
        raise NotImplementedError("DynamoDB backend: implemented in Stage 9")

    def update_review_status(self, run_id, employee_id, status, comment, outcome, actor):
        raise NotImplementedError("DynamoDB backend: implemented in Stage 9")

    def get_latest_run_id(self) -> Optional[str]:
        raise NotImplementedError("DynamoDB backend: implemented in Stage 9")

    def append_audit_entry(self, entry: dict) -> str:
        raise NotImplementedError("DynamoDB backend: implemented in Stage 9")

    def get_audit_log(self, limit=500) -> list[dict]:
        raise NotImplementedError("DynamoDB backend: implemented in Stage 9")

    def reset(self) -> None:
        raise NotImplementedError("DynamoDB backend: implemented in Stage 9")


# ── Factory ───────────────────────────────────────────────────────────────────

def get_storage() -> StorageBackend:
    """Return the configured storage backend."""
    backend = os.getenv("STORAGE_BACKEND", "sqlite").lower()
    if backend == "dynamodb":
        return DynamoDBStorage()
    db_path = os.getenv("SQLITE_DB_PATH", "./data/accessguard.db")
    return SQLiteStorage(db_path)
