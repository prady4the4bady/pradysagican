"""Lightweight telemetry metrics for latency/throughput/resource tracking."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricEvent:
    name: str
    started_at: float
    ended_at: float
    duration_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Thread-safe in-memory metrics collector with minimal overhead."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: list[MetricEvent] = []

    def record(self, name: str, started_at: float, ended_at: float, metadata: dict[str, Any] | None = None) -> None:
        evt = MetricEvent(
            name=name,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=round((ended_at - started_at) * 1000, 3),
            metadata=metadata or {},
        )
        with self._lock:
            self._events.append(evt)

    def time_block(self, name: str, metadata: dict[str, Any] | None = None) -> "_MetricsTimer":
        return _MetricsTimer(self, name, metadata or {})

    def summary(self) -> dict[str, Any]:
        with self._lock:
            events = list(self._events)
        if not events:
            return {"count": 0, "avg_latency_ms": 0.0, "p95_latency_ms": 0.0}
        durations = sorted(e.duration_ms for e in events)
        count = len(durations)
        p95_idx = max(0, min(count - 1, int(count * 0.95) - 1))
        return {
            "count": count,
            "avg_latency_ms": round(sum(durations) / count, 3),
            "p95_latency_ms": durations[p95_idx],
        }


class _MetricsTimer:
    def __init__(self, collector: MetricsCollector, name: str, metadata: dict[str, Any]) -> None:
        self._collector = collector
        self._name = name
        self._metadata = metadata
        self._started = 0.0

    def __enter__(self) -> "_MetricsTimer":
        self._started = time.time()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        ended = time.time()
        meta = dict(self._metadata)
        if exc is not None:
            meta["error"] = str(exc)
        self._collector.record(self._name, self._started, ended, meta)
