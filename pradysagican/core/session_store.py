"""Session store with SQLite FTS5 for cross-session recall."""

from __future__ import annotations

import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any


class SessionStore:
    def __init__(self, db_path: str | None = None) -> None:
        base = Path(os.getenv("PRADYSAGICAN_DATA", "./data"))
        base.mkdir(parents=True, exist_ok=True)
        self._db_path = db_path or str(base / "sessions.sqlite3")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            # FTS5 virtual table for full-text search over content.
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts
                USING fts5(id, session_id, role, content)
                """
            )
            conn.commit()

    def append(self, session_id: str, role: str, content: str) -> str:
        row_id = uuid.uuid4().hex
        ts = time.time()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions (id, session_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (row_id, session_id, role, content, ts),
            )
            conn.execute(
                "INSERT INTO sessions_fts (id, session_id, role, content) VALUES (?, ?, ?, ?)",
                (row_id, session_id, role, content),
            )
            conn.commit()
        return row_id

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT s.id, s.session_id, s.role, s.content, s.created_at
                FROM sessions_fts f
                JOIN sessions s ON s.id = f.id
                WHERE sessions_fts MATCH ?
                ORDER BY s.created_at DESC
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        return [
            {
                "id": r[0],
                "session_id": r[1],
                "role": r[2],
                "content": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]
