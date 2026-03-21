"""Self-Improvement Engine (evolved EDITH) — PRADYSAGICAN
Godel Agent recursive self-improvement (Yin et al. 2025)."""
from __future__ import annotations
import logging, time
from dataclasses import dataclass, field
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class LearningEpisode:
    task: str
    actions: list[str]
    outcome: str
    success: bool
    lessons: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

class SelfImprovementEngine:
    """Recursive self-improvement through reflection and heuristic distillation."""

    def __init__(self) -> None:
        self._episodes: list[LearningEpisode] = []
        self._heuristics: dict[str, str] = {}
        self._performance_log: list[float] = []

    async def reflect(self, task: str, actions: list[str], outcome: str, success: bool) -> LearningEpisode:
        """Reflect on a completed task to extract lessons."""
        lessons = []
        if success:
            lessons.append(f"Successful approach for tasks like: {task[:30]}")
            lessons.append(f"Effective action sequence had {len(actions)} steps")
        else:
            lessons.append(f"Failed approach — avoid for: {task[:30]}")
            if len(actions) > 5:
                lessons.append("Consider simpler approach with fewer steps")
        episode = LearningEpisode(task=task, actions=actions, outcome=outcome, success=success, lessons=lessons)
        self._episodes.append(episode)
        self._performance_log.append(1.0 if success else 0.0)
        return episode

    async def distill_heuristics(self) -> dict[str, str]:
        """Extract reusable patterns from experience."""
        if len(self._episodes) < 3:
            return {"status": "Need more experience to distill heuristics"}
        successes = [e for e in self._episodes if e.success]
        failures = [e for e in self._episodes if not e.success]
        if successes:
            avg_steps = np.mean([len(e.actions) for e in successes])
            self._heuristics["optimal_steps"] = f"Successful tasks average {avg_steps:.0f} steps"
        if failures:
            self._heuristics["avoid_pattern"] = f"Common failure patterns in {len(failures)} episodes"
        success_rate = len(successes) / max(len(self._episodes), 1)
        self._heuristics["overall_success_rate"] = f"{success_rate:.1%}"
        return self._heuristics

    async def performance_trend(self) -> dict[str, Any]:
        """Analyze performance improvement over time."""
        if len(self._performance_log) < 2:
            return {"trend": "insufficient_data"}
        recent = self._performance_log[-10:]
        older = self._performance_log[:-10] if len(self._performance_log) > 10 else self._performance_log[:len(self._performance_log)//2]
        return {
            "total_episodes": len(self._performance_log),
            "recent_success_rate": float(np.mean(recent)),
            "older_success_rate": float(np.mean(older)) if older else 0,
            "improving": float(np.mean(recent)) > float(np.mean(older)) if older else True,
        }
