"""Terminal benchmark scaffold powered by shell executor history loops."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pradysagican.tools.shell_executor import ShellExecutor


@dataclass
class TerminalStep:
    command: str
    ok: bool
    stdout: str
    stderr: str
    return_code: int


@dataclass
class TerminalRunResult:
    success: bool
    steps: list[TerminalStep] = field(default_factory=list)
    context: str = ""


class TerminalMode:
    """Executes command trajectories with context replay for multi-step tasks."""

    def __init__(self, executor: ShellExecutor | None = None) -> None:
        self._executor = executor or ShellExecutor()

    async def run_plan(self, commands: list[str]) -> TerminalRunResult:
        steps: list[TerminalStep] = []
        success = True
        for cmd in commands:
            out = await self._executor.run(cmd)
            step = TerminalStep(
                command=cmd,
                ok=bool(out.get("ok")),
                stdout=str(out.get("stdout", "")),
                stderr=str(out.get("stderr", "")),
                return_code=int(out.get("return_code", 1)),
            )
            steps.append(step)
            if not step.ok:
                success = False
                break
        return TerminalRunResult(
            success=success,
            steps=steps,
            context=self._executor.history.as_context(10),
        )

