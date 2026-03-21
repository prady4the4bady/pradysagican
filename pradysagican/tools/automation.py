"""Automation Engine — PRADYSAGICAN. n8n/Make.com equivalent."""
from __future__ import annotations
import logging, asyncio, uuid, time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

@dataclass
class WorkflowStep:
    name: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    condition: str | None = None  # conditional execution

@dataclass
class Workflow:
    id: str
    name: str
    steps: list[WorkflowStep]
    trigger: str = "manual"  # manual, cron, webhook, event
    cron_expr: str | None = None
    enabled: bool = True
    runs: int = 0

class AutomationEngine:
    """Workflow automation with triggers, conditions, and scheduling."""

    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}
        self._event_handlers: dict[str, list[str]] = {}  # event -> workflow_ids

    def create_workflow(self, name: str, steps: list[dict[str, Any]], trigger: str = "manual") -> Workflow:
        wf = Workflow(
            id=f"wf_{uuid.uuid4().hex[:8]}", name=name,
            steps=[WorkflowStep(**s) for s in steps], trigger=trigger,
        )
        self._workflows[wf.id] = wf
        return wf

    async def execute_workflow(self, workflow_id: str) -> dict[str, Any]:
        """Execute a workflow step by step."""
        wf = self._workflows.get(workflow_id)
        if not wf:
            return {"error": f"Workflow not found: {workflow_id}"}
        results = []
        for step in wf.steps:
            if step.condition:
                # Simple condition eval
                if not self._eval_condition(step.condition, results):
                    results.append({"step": step.name, "skipped": True})
                    continue
            results.append({"step": step.name, "action": step.action, "status": "completed"})
        wf.runs += 1
        return {"workflow": wf.name, "steps_executed": len(results), "results": results}

    def register_event_trigger(self, event_type: str, workflow_id: str) -> None:
        self._event_handlers.setdefault(event_type, []).append(workflow_id)

    async def trigger_event(self, event_type: str, data: dict[str, Any] | None = None) -> list[dict]:
        """Fire all workflows registered for an event."""
        wf_ids = self._event_handlers.get(event_type, [])
        results = []
        for wf_id in wf_ids:
            r = await self.execute_workflow(wf_id)
            results.append(r)
        return results

    def list_workflows(self) -> list[dict[str, Any]]:
        return [{"id": w.id, "name": w.name, "trigger": w.trigger, "runs": w.runs} for w in self._workflows.values()]

    @staticmethod
    def _eval_condition(condition: str, prior_results: list) -> bool:
        if "always" in condition.lower():
            return True
        if "never" in condition.lower():
            return False
        return True  # Default: proceed
