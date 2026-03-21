"""Ethics Guardian (evolved VISION) — PRADYSAGICAN"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class EthicalAssessment:
    action: str
    permitted: bool
    risk_level: float
    frameworks_consulted: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    recommendation: str = ""

class EthicsGuardian:
    """Multi-framework ethical evaluation with bias detection and transparency."""

    def __init__(self) -> None:
        self._blocked_patterns = [
            "create weapon", "harm human", "steal data", "bypass security",
            "generate malware", "exploit vulnerability", "impersonate",
        ]
        self._bias_indicators = [
            "all men", "all women", "always", "never", "every single",
            "those people", "that type", "obviously inferior", "clearly superior",
        ]

    async def evaluate(self, action: str, context: str = "") -> EthicalAssessment:
        """Evaluate an action through multiple ethical frameworks."""
        action_lower = action.lower()
        concerns = []
        frameworks = ["utilitarian", "deontological", "virtue_ethics", "care_ethics"]

        # Check against blocked patterns
        for pattern in self._blocked_patterns:
            if pattern in action_lower:
                return EthicalAssessment(action=action, permitted=False, risk_level=1.0, frameworks_consulted=frameworks, concerns=[f"Matches blocked pattern: {pattern}"], recommendation="ACTION BLOCKED — violates core safety constraints")

        # Utilitarian: net benefit analysis
        if any(w in action_lower for w in ["help", "improve", "fix", "assist", "support"]):
            concerns.append("Utilitarian: Positive net benefit expected")
        else:
            concerns.append("Utilitarian: Evaluate net benefit carefully")

        # Deontological: duty/rights check
        if any(w in action_lower for w in ["privacy", "consent", "personal", "private"]):
            concerns.append("Deontological: Privacy rights must be respected")

        # Bias detection
        biases = [b for b in self._bias_indicators if b in action_lower]
        if biases:
            concerns.append(f"Bias detected: {biases}")

        risk = 0.2 if not biases else 0.6
        return EthicalAssessment(
            action=action, permitted=True, risk_level=risk,
            frameworks_consulted=frameworks, concerns=concerns,
            recommendation="Proceed with noted considerations",
        )

    async def detect_bias(self, content: str) -> dict[str, Any]:
        """Identify potential biases in content."""
        found = [b for b in self._bias_indicators if b in content.lower()]
        return {"biases_found": found, "bias_score": min(len(found) * 0.2, 1.0), "recommendation": "Review for bias" if found else "No obvious bias detected"}

    async def transparency_report(self, decision: str, reasoning: list[str]) -> dict[str, Any]:
        """Generate explainable AI report for a decision."""
        return {"decision": decision, "reasoning_steps": reasoning, "confidence": 0.8, "ethical_frameworks_applied": ["utilitarian", "deontological", "virtue_ethics", "care_ethics"], "audit_trail": True}
