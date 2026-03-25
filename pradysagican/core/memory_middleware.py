"""Memory middleware: Mem0 bridge with fallback local session retrieval."""

from __future__ import annotations

import logging
from typing import Any

from pradysagican.config import load_config
from pradysagican.core.session_store import SessionStore

logger = logging.getLogger(__name__)


class MemoryMiddleware:
    """Unified memory ingestion/retrieval API for chat and agent loops."""

    def __init__(self) -> None:
        self._cfg = load_config()
        self._session_store = SessionStore()
        self._mem0_available = False
        self._mem0 = None
        if not self._cfg.upgrades.force_legacy_memory and not self._cfg.upgrades.kill_switch_new_paths:
            try:
                from mem0 import Memory  # type: ignore[import-not-found]
                self._mem0 = Memory
                self._mem0_available = True
            except Exception as exc:  # pragma: no cover
                logger.warning("Mem0 unavailable; using local session store fallback: %s", exc)
        self._mem0_client = None
        if self._mem0_available and self._mem0 is not None:
            try:
                self._mem0_client = self._mem0()
            except Exception as exc:
                logger.warning("Mem0 initialization failed; fallback mode enabled: %s", exc)

    def ingest_turn(self, session_id: str, role: str, content: str) -> dict[str, Any]:
        row_id = self._session_store.append(session_id=session_id, role=role, content=content)
        mem0_status = "disabled"
        if self._mem0_client is not None:
            try:
                self._mem0_client.add(content, user_id=session_id, metadata={"role": role})
                mem0_status = "stored"
            except Exception as exc:
                mem0_status = f"error:{exc}"
        return {"id": row_id, "mem0": mem0_status}

    def retrieve(self, session_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        if self._mem0_client is not None:
            try:
                mem0_results = self._mem0_client.search(query, user_id=session_id, limit=limit)
                for item in mem0_results or []:
                    merged.append({"source": "mem0", "content": str(item)})
            except Exception:
                pass
        local_results = self._session_store.search(query, limit=limit)
        merged.extend({"source": "session_store", **r} for r in local_results)
        return merged[:limit]
