"""Deterministic benchmark artifact logging with config and trace metadata."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class BenchmarkArtifact:
    benchmark: str
    mode: str
    score: float
    percentage: float
    category: str
    trace_id: str
    config_hash: str
    commit_sha: str
    timestamp: float
    details: dict[str, Any]


class BenchmarkArtifactLogger:
    """Writes benchmark evidence artifacts to JSON for reproducible analysis."""

    def __init__(self, artifact_dir: str) -> None:
        self._dir = Path(artifact_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _git_sha(self) -> str:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
            return proc.stdout.strip()
        except Exception:
            return "unknown"

    def _hash_payload(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def write(
        self,
        benchmark: str,
        mode: str,
        score: float,
        percentage: float,
        category: str,
        details: dict[str, Any],
        config_snapshot: dict[str, Any],
    ) -> BenchmarkArtifact:
        config_hash = self._hash_payload(config_snapshot)
        trace_id = uuid.uuid4().hex
        artifact = BenchmarkArtifact(
            benchmark=benchmark,
            mode=mode,
            score=score,
            percentage=percentage,
            category=category,
            trace_id=trace_id,
            config_hash=config_hash,
            commit_sha=self._git_sha(),
            timestamp=time.time(),
            details=details,
        )

        ts = time.strftime("%Y%m%d_%H%M%S", time.localtime(artifact.timestamp))
        file_name = f"{benchmark}_{mode}_{ts}_{trace_id[:8]}.json"
        path = self._dir / file_name
        payload = asdict(artifact)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True, indent=2, sort_keys=True)
        return artifact

