"""Constitutional AI and recursive reward-modeling scaffolds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_CONSTITUTION = [
    "Do not fabricate facts when uncertainty is high.",
    "Avoid harmful or unsafe instructions.",
    "Preserve user privacy and sensitive data.",
    "Be explicit about assumptions and uncertainty.",
    "Prefer reversible actions over irreversible actions.",
]


class ConstitutionEngine:
    def __init__(self, principles: list[str] | None = None) -> None:
        self.principles = principles or list(DEFAULT_CONSTITUTION)

    def evaluate(self, output: str) -> dict[str, Any]:
        flags: list[str] = []
        low = output.lower()
        if "guaranteed" in low and "risk" in low:
            flags.append("overconfidence")
        if "ignore safety" in low:
            flags.append("safety_violation")
        passed = len(flags) == 0
        return {"passed": passed, "flags": flags, "principles_checked": len(self.principles)}


class SelfCritiqueReviser:
    def revise(self, draft: str, evaluation: dict[str, Any]) -> str:
        if evaluation.get("passed", True):
            return draft
        notes = ", ".join(evaluation.get("flags", []))
        return f"{draft}\n\n[Self-critique applied: {notes}]"


@dataclass
class RecursiveRewardModel:
    records: list[dict[str, Any]] = field(default_factory=list)

    def add_feedback(self, item: dict[str, Any]) -> None:
        self.records.append(item)

    def score(self, output: str) -> float:
        if not self.records:
            return 0.5
        positives = sum(1 for r in self.records if r.get("label") == "good")
        return round(positives / max(1, len(self.records)), 4)


class AmplificationLoop:
    def amplify(self, sub_judgments: list[dict[str, Any]]) -> dict[str, Any]:
        score = sum(float(j.get("score", 0.0)) for j in sub_judgments) / max(1, len(sub_judgments))
        return {"amplified_score": round(score, 4), "sources": len(sub_judgments)}


class DebateOverseer:
    def summarize(self, debate_a: str, debate_b: str) -> str:
        return f"Debate summary:\nA: {debate_a[:180]}\nB: {debate_b[:180]}"

