"""Shell execution backend with history tracking and optional SSH profile."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShellHistoryItem:
    command: str
    stdout: str
    stderr: str
    return_code: int
    timestamp: float = field(default_factory=time.time)


class ShellHistoryManager:
    def __init__(self) -> None:
        self._history: list[ShellHistoryItem] = []

    def add(self, item: ShellHistoryItem) -> None:
        self._history.append(item)

    def tail(self, n: int = 10) -> list[ShellHistoryItem]:
        return self._history[-n:]

    def as_context(self, n: int = 10) -> str:
        items = self.tail(n)
        lines = []
        for it in items:
            lines.append(f"$ {it.command}\nrc={it.return_code}\n{it.stdout}\n{it.stderr}".strip())
        return "\n\n".join(lines)


class ShellExecutor:
    """Local shell executor; SSH profiles can be added later via adapters."""

    def __init__(self) -> None:
        self.history = ShellHistoryManager()

    async def run(self, command: str, timeout_sec: int = 60) -> dict[str, Any]:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
            rc = int(proc.returncode or 0)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            stdout_b, stderr_b, rc = b"", b"Command timed out", 124

        item = ShellHistoryItem(
            command=command,
            stdout=stdout_b.decode("utf-8", errors="replace"),
            stderr=stderr_b.decode("utf-8", errors="replace"),
            return_code=rc,
        )
        self.history.add(item)
        return {"ok": rc == 0, "stdout": item.stdout, "stderr": item.stderr, "return_code": rc}
