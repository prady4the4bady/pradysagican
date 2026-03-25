"""Code-as-action agent for tool-aware sandboxed execution tasks."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from pradysagican.config import load_config
from pradysagican.providers.llm import UniversalLLMProvider
from pradysagican.tools.code_executor_e2b import E2BCodeExecutor


@dataclass
class AgentOutput:
    task: str
    code: str
    result: dict[str, Any] = field(default_factory=dict)
    used_sandbox: bool = False
    duration_ms: float = 0.0


class PRADYCodeAgent:
    """Generates Python actions and executes them through a safe runtime."""

    def __init__(
        self,
        llm: UniversalLLMProvider | None = None,
        executor: E2BCodeExecutor | None = None,
    ) -> None:
        self._cfg = load_config()
        self._llm = llm or UniversalLLMProvider()
        self._executor = executor or E2BCodeExecutor()

    def _build_code_prompt(self, task: str) -> str:
        return (
            "Write only Python code to solve the task. "
            "No explanation, no markdown unless using one fenced block.\n"
            f"Task: {task}\n"
            "Return deterministic output."
        )

    def _extract_code(self, text: str) -> str:
        fenced = re.search(r"```(?:python)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1).strip()
        return text.strip()

    async def step(self, task: str) -> AgentOutput:
        started = time.time()
        prompt = self._build_code_prompt(task)
        raw = await self._llm.complete(prompt, temperature=0.1, max_tokens=1200)
        code = self._extract_code(raw)

        use_sandbox = self._cfg.upgrades.enable_code_agent and self._cfg.upgrades.enable_e2b
        if self._cfg.upgrades.kill_switch_new_paths:
            use_sandbox = False

        if use_sandbox:
            result = await self._executor.run_python(code)
        else:
            result = {
                "ok": True,
                "mode": "dry_run",
                "note": "Code generated but execution path is disabled by feature flags.",
            }

        return AgentOutput(
            task=task,
            code=code,
            result=result,
            used_sandbox=use_sandbox,
            duration_ms=round((time.time() - started) * 1000, 2),
        )

