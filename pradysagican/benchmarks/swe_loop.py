"""SWE-Bench style repo context and test-repair execution scaffold."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pradysagican.tools.code_executor_e2b import E2BCodeExecutor


@dataclass
class RepoContext:
    root: str
    files: list[str] = field(default_factory=list)
    hint_files: list[str] = field(default_factory=list)


class RepoContextBuilder:
    """Builds repository context for coding-fix tasks."""

    def build(self, repo_root: str, hint_patterns: list[str] | None = None, max_files: int = 200) -> RepoContext:
        hints = hint_patterns or ["README", "pyproject.toml", "tests", "src", "pradysagican"]
        files: list[str] = []
        for p in Path(repo_root).rglob("*"):
            if p.is_file():
                files.append(str(p))
                if len(files) >= max_files:
                    break
        hint_files = [f for f in files if any(h.lower() in f.lower() for h in hints)]
        return RepoContext(root=repo_root, files=files, hint_files=hint_files[:50])


class TestRepairLoop:
    """Generate-fix-test-repair loop scaffold for SWE-style tasks."""

    def __init__(self, executor: E2BCodeExecutor | None = None) -> None:
        self._executor = executor or E2BCodeExecutor()

    async def run(self, test_command: str = "pytest -q", max_iters: int = 5) -> dict[str, Any]:
        history: list[dict[str, Any]] = []
        for i in range(max_iters):
            test_out = await self._executor.run_shell(test_command)
            history.append({"iter": i + 1, "test_out": test_out})
            if test_out.get("ok"):
                return {"ok": True, "iterations": i + 1, "history": history}
        return {"ok": False, "iterations": max_iters, "history": history}

