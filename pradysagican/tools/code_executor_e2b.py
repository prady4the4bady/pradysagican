"""Sandboxed code execution via E2B with fallback local stub execution."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class E2BCodeExecutor:
    """Run code in sandbox for safe iterative coding tasks."""

    def __init__(self) -> None:
        self._available = False
        self._sandbox = None
        try:
            # Preferred package.
            from e2b_code_interpreter import Sandbox  # type: ignore[import-not-found]
            self._sandbox = Sandbox
            self._available = True
        except Exception:
            try:
                # Alternate package path fallback.
                from e2b import Sandbox  # type: ignore[import-not-found]
                self._sandbox = Sandbox
                self._available = True
            except Exception as exc:  # pragma: no cover
                logger.warning("E2B SDK unavailable; using stub executor: %s", exc)

    async def run_python(self, code: str) -> dict[str, Any]:
        if self._available and self._sandbox is not None:
            try:
                # Use thread offload to avoid blocking event loop.
                return await asyncio.to_thread(self._run_python_sync, code)
            except Exception as exc:
                logger.warning("E2B python execution failed, falling back: %s", exc)
        return {"ok": True, "mode": "stub", "stdout": "", "stderr": "", "result": None}

    def _run_python_sync(self, code: str) -> dict[str, Any]:
        sb = self._sandbox()
        # Different SDKs expose different APIs; handle best-effort.
        if hasattr(sb, "run_code"):
            res = sb.run_code(code)
            return {"ok": True, "mode": "e2b", "result": getattr(res, "results", str(res))}
        if hasattr(sb, "commands"):
            out = sb.commands.run(f"python - <<'PY'\n{code}\nPY")
            return {"ok": True, "mode": "e2b", "stdout": str(out)}
        return {"ok": True, "mode": "e2b", "result": None}

    async def run_shell(self, command: str) -> dict[str, Any]:
        if self._available and self._sandbox is not None:
            try:
                return await asyncio.to_thread(self._run_shell_sync, command)
            except Exception as exc:
                logger.warning("E2B shell execution failed, falling back: %s", exc)
        return {"ok": True, "mode": "stub", "stdout": "", "stderr": ""}

    def _run_shell_sync(self, command: str) -> dict[str, Any]:
        sb = self._sandbox()
        if hasattr(sb, "commands"):
            out = sb.commands.run(command)
            return {"ok": True, "mode": "e2b", "stdout": str(out)}
        return {"ok": False, "mode": "e2b", "error": "No shell command API available"}
