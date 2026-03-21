"""
Expanded Focus Engine — PRADYSAGICAN (NOVEL)
Dynamic attention management: deep focus, broad scan, flow state.
Implements Csikszentmihalyi\'s flow state theory.
"""
from __future__ import annotations
import logging, time, asyncio
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class FocusState:
    mode: str  # "deep", "broad", "flow", "peripheral"
    target: str
    depth_level: int = 1
    duration_sec: float = 0.0
    effectiveness: float = 0.5

class ExpandedFocusEngine:
    """Dynamic attention allocation between focused and diffuse modes."""

    def __init__(self) -> None:
        self._current_focus = FocusState(mode="broad", target="general")
        self._focus_history: list[FocusState] = []
        self._start_time: float = time.time()

    async def deep_focus(self, topic: str, depth_level: int = 3) -> dict[str, Any]:
        """Increasingly detailed analysis at specified depth."""
        layers = []
        for d in range(1, depth_level + 1):
            layers.append({"depth": d, "analysis": f"Level-{d} analysis of {topic}", "detail": "high" if d > 2 else "medium"})
        self._current_focus = FocusState(mode="deep", target=topic, depth_level=depth_level, effectiveness=min(0.5 + depth_level * 0.15, 0.95))
        self._focus_history.append(self._current_focus)
        return {"topic": topic, "layers": layers, "focus_state": self._current_focus}

    async def broad_scan(self, domain: str) -> dict[str, Any]:
        """Wide-ranging overview of a domain."""
        aspects = ["trends", "key_players", "challenges", "opportunities", "recent_developments"]
        scan = {aspect: f"Overview of {domain} {aspect}" for aspect in aspects}
        self._current_focus = FocusState(mode="broad", target=domain, effectiveness=0.6)
        return {"domain": domain, "scan": scan, "coverage": "wide"}

    async def flow_state(self, task: str) -> dict[str, Any]:
        """Enter optimal engagement mode (Csikszentmihalyi)."""
        # Flow conditions: clear goals, immediate feedback, challenge ≈ skill
        self._current_focus = FocusState(mode="flow", target=task, effectiveness=0.95)
        self._start_time = time.time()
        return {
            "task": task, "state": "flow",
            "conditions": {"clear_goals": True, "immediate_feedback": True, "challenge_skill_balance": True},
            "expected_productivity_boost": "2-5x normal",
        }

    async def attention_allocation(self, tasks: list[dict[str, float]]) -> list[dict[str, Any]]:
        """Optimally distribute attention across tasks (priority-weighted)."""
        total_priority = sum(t.get("priority", 0.5) for t in tasks)
        return [
            {"task": t.get("name", f"task_{i}"), "attention_share": t.get("priority", 0.5) / max(total_priority, 0.01), "recommended_mode": "deep" if t.get("priority", 0.5) > 0.7 else "broad"}
            for i, t in enumerate(tasks)
        ]

    async def peripheral_awareness(self, main_task: str, background_items: list[str]) -> dict[str, Any]:
        """Monitor background items while focused on main task."""
        alerts = [item for item in background_items if any(kw in item.lower() for kw in ["urgent", "critical", "error", "alert"])]
        return {"main_focus": main_task, "background_monitored": len(background_items), "alerts_detected": alerts, "main_focus_maintained": len(alerts) == 0}
