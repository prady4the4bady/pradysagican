"""Persistent storage for traces and evaluation summaries."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List


class PersistentObservabilityStore:
    """SQLite-backed store for trace and evaluation artifacts."""

    def __init__(self, db_path: str = "data/observability.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trace_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    quality_score REAL NOT NULL,
                    relevance_score REAL NOT NULL,
                    coherence_score REAL NOT NULL,
                    estimated_cost_usd REAL NOT NULL,
                    latency_ms REAL NOT NULL,
                    token_input INTEGER NOT NULL,
                    token_output INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    raw_json TEXT NOT NULL
                )
                """
            )

    def insert_trace_event(self, event: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO trace_events (request_id, status, latency_ms, tokens_used, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event["request_id"],
                    event["status"],
                    float(event["latency_ms"]),
                    int(event["tokens_used"]),
                    event["timestamp"],
                ),
            )

    def insert_evaluation_result(self, result: Dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_results (
                    case_id, model_name, passed, quality_score, relevance_score,
                    coherence_score, estimated_cost_usd, latency_ms, token_input,
                    token_output, timestamp, raw_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result["case_id"],
                    result["model_name"],
                    1 if result["passed"] else 0,
                    float(result["quality_score"]),
                    float(result["relevance_score"]),
                    float(result["coherence_score"]),
                    float(result["estimated_cost_usd"]),
                    float(result["latency_ms"]),
                    int(result["token_input"]),
                    int(result["token_output"]),
                    result["timestamp"],
                    json.dumps(result),
                ),
            )

    def list_traces(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT request_id, status, latency_ms, tokens_used, timestamp
                FROM trace_events ORDER BY id DESC LIMIT ?
                """,
                (max(1, min(limit, 1000)),),
            ).fetchall()
        return [dict(r) for r in rows]

    def list_evaluations(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT raw_json FROM evaluation_results ORDER BY id DESC LIMIT ?
                """,
                (max(1, min(limit, 1000)),),
            ).fetchall()
        return [json.loads(r["raw_json"]) for r in rows]

