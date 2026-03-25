"""Prompt versioning registry with optional ell integration."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from pradysagican.config import load_config


@dataclass
class PromptVersion:
    prompt_id: str
    version_hash: str
    content: str
    metadata: dict[str, Any]
    created_at: float


class PromptRegistry:
    """Tracks prompt versions for reproducible experiments."""

    def __init__(self, store_dir: str | None = None) -> None:
        cfg = load_config()
        base = store_dir or os.getenv("PRADY_PROMPT_STORE", "./data/prompts")
        self._root = Path(base)
        self._root.mkdir(parents=True, exist_ok=True)
        self._cfg = cfg
        self._ell_enabled = False

        if cfg.upgrades.enable_prompt_versioning:
            try:
                import ell  # type: ignore[import-not-found]
                ell.init(store=str(self._root), autocommit=True)
                self._ell_enabled = True
            except Exception:
                self._ell_enabled = False

    def _hash(self, prompt_id: str, content: str, metadata: dict[str, Any]) -> str:
        payload = json.dumps(
            {"prompt_id": prompt_id, "content": content, "metadata": metadata},
            ensure_ascii=True,
            sort_keys=True,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _path(self, prompt_id: str) -> Path:
        return self._root / f"{prompt_id}.jsonl"

    def register(self, prompt_id: str, content: str, metadata: dict[str, Any] | None = None) -> PromptVersion:
        meta = metadata or {}
        version_hash = self._hash(prompt_id, content, meta)
        ver = PromptVersion(
            prompt_id=prompt_id,
            version_hash=version_hash,
            content=content,
            metadata=meta,
            created_at=time.time(),
        )
        with self._path(prompt_id).open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(ver), ensure_ascii=True) + "\n")
        return ver

    def history(self, prompt_id: str) -> list[PromptVersion]:
        path = self._path(prompt_id)
        if not path.exists():
            return []
        items: list[PromptVersion] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                raw = json.loads(line)
                items.append(PromptVersion(**raw))
        return items

    def latest(self, prompt_id: str) -> PromptVersion | None:
        hist = self.history(prompt_id)
        return hist[-1] if hist else None

