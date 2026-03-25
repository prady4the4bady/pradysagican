"""Superintelligence-oriented safety-net scaffolds."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


class GoalPreservationLock:
    def hash_goals(self, goals: list[str]) -> str:
        payload = "|".join(sorted(goals)).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def verify_unchanged(self, before_hash: str, after_goals: list[str]) -> bool:
        return before_hash == self.hash_goals(after_goals)


class CapabilityOntology:
    def __init__(self, allowed: list[str] | None = None) -> None:
        self.allowed = set(allowed or ["reasoning", "memory", "tool_use", "planning"])

    def can_modify(self, capability: str) -> bool:
        return capability in self.allowed


class ImpactMinimizer:
    def penalty(self, irreversible_risk: float) -> float:
        return round(max(0.0, irreversible_risk) * 2.0, 4)


class TriplockApproval:
    def approve(self, formal: bool, human: bool, oracle: bool) -> bool:
        return formal and human and oracle


@dataclass
class SafeRSICage:
    enabled: bool = True

    def run_experiment(self, proposal: dict[str, Any]) -> dict[str, Any]:
        return {"sandboxed": self.enabled, "proposal": proposal, "status": "evaluated"}


class CorrigibilityModule:
    def correction_reward(self, accepted_correction: bool) -> float:
        return 1.0 if accepted_correction else -1.0

