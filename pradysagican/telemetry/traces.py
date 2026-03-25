"""Simple trace/event logger for reproducible benchmark and runtime diagnostics."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any


class TraceLogger:
    """Append-only JSONL trace logger."""

    def __init__(self, trace_dir: str | None = None) -> None:
        base_dir = trace_dir or os.getenv("PRADY_TRACE_DIR", "./data/traces")
        self._dir = Path(base_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._file = self._dir / "events.jsonl"

    def emit(self, event_type: str, payload: dict[str, Any]) -> str:
        trace_id = uuid.uuid4().hex
        record = {
            "trace_id": trace_id,
            "timestamp": time.time(),
            "event_type": event_type,
            "payload": payload,
        }
        with self._file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=True) + "\n")
        return trace_id
