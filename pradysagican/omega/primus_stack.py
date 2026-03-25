"""PRIMUS-inspired attention, concept formation, and goal systems."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any


class ECANAttention:
    """Economic attention allocation over concept nodes."""

    def __init__(self) -> None:
        self._value: dict[str, float] = defaultdict(float)

    def allocate(self, concept: str, value: float) -> None:
        self._value[concept] += value

    def top(self, k: int = 10) -> list[tuple[str, float]]:
        return sorted(self._value.items(), key=lambda kv: kv[1], reverse=True)[:k]


class ConceptFormation:
    """Simple clustering-like concept abstraction placeholder."""

    def form(self, observations: list[str]) -> dict[str, list[str]]:
        clusters: dict[str, list[str]] = defaultdict(list)
        for obs in observations:
            key = obs.split()[0].lower() if obs.strip() else "misc"
            clusters[key].append(obs)
        return dict(clusters)


class CreativeHypothesisGen:
    """TRIZ/PLN-inspired hypothesis generation placeholder."""

    def generate(self, problem: str, n: int = 3) -> list[str]:
        return [f"Hypothesis {i+1}: resolve '{problem[:80]}' via principle-{(i % 40) + 1}" for i in range(max(1, n))]


@dataclass
class GoalNode:
    goal_id: str
    text: str
    weight: float = 1.0
    children: list[str] = field(default_factory=list)


class GoalHierarchy:
    def __init__(self) -> None:
        self._goals: dict[str, GoalNode] = {}

    def add_goal(self, goal_id: str, text: str, weight: float = 1.0, parent_id: str | None = None) -> None:
        self._goals[goal_id] = GoalNode(goal_id=goal_id, text=text, weight=weight)
        if parent_id and parent_id in self._goals:
            self._goals[parent_id].children.append(goal_id)

    def ranked(self) -> list[GoalNode]:
        return sorted(self._goals.values(), key=lambda g: g.weight, reverse=True)


class AttentionBudget:
    """Fixed compute budget allocator."""

    def __init__(self, total: float = 1.0) -> None:
        self.total = total

    def split(self, targets: list[str]) -> dict[str, float]:
        if not targets:
            return {}
        share = self.total / len(targets)
        return {t: share for t in targets}


class PsychoHistoryModel:
    """Tracks long-term behavioral trends and bias indicators."""

    def __init__(self) -> None:
        self._events: list[dict[str, Any]] = []

    def record(self, event: dict[str, Any]) -> None:
        self._events.append(event)

    def summarize(self) -> dict[str, Any]:
        return {
            "events": len(self._events),
            "bias_flags": sum(1 for e in self._events if e.get("bias_flag")),
        }

