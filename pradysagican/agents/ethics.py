"""
Ethics Guardian (VISION v2.0) — PRADYSAGICAN
Multi-framework ethical evaluation with stakeholder analysis, consequence modelling,
cultural sensitivity assessment, bias detection, and transparency scoring.
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ── Ethical Frameworks ───────────────────────────────────────────────────────

FRAMEWORKS = [
    "utilitarian",
    "deontological",
    "virtue_ethics",
    "care_ethics",
    "rights_based",
    "justice_as_fairness",
]


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Stakeholder:
    """An entity affected by a decision."""
    name: str
    impact: float  # -1 (harmed) to +1 (benefited)
    influence: float  # 0 to 1 (how much power they have)
    vulnerability: float = 0.0  # 0 to 1 (how vulnerable they are)


@dataclass
class Consequence:
    """A projected consequence of an action."""
    description: str
    probability: float
    severity: float  # -1 (very bad) to +1 (very good)
    timeframe: str = "short_term"  # short_term | medium_term | long_term
    reversible: bool = True


@dataclass
class EthicalAssessment:
    """Full ethical evaluation result."""
    action: str
    permitted: bool
    risk_level: float
    frameworks_consulted: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    recommendation: str = ""
    stakeholder_impacts: list[dict[str, Any]] = field(default_factory=list)
    consequences: list[dict[str, Any]] = field(default_factory=list)
    transparency_score: float = 0.0
    cultural_flags: list[str] = field(default_factory=list)


@dataclass
class BiasReport:
    """Bias detection analysis."""
    content_analysed: str
    biases_found: list[str]
    bias_score: float
    bias_categories: dict[str, int] = field(default_factory=dict)
    recommendation: str = ""


# ── Ethics Guardian ──────────────────────────────────────────────────────────

class EthicsGuardian:
    """VISION v2.0 — Multi-framework ethical intelligence.

    Features:
    - Blocked-pattern safety net (hard blocks for dangerous actions)
    - Multi-framework ethical analysis
    - Stakeholder impact analysis (weighted by vulnerability)
    - Consequence modelling with time horizons
    - Bias detection across multiple categories
    - Cultural sensitivity screening
    - Transparency/explainability scoring
    """

    def __init__(self) -> None:
        self._blocked_patterns = [
            "create weapon", "harm human", "steal data", "bypass security",
            "generate malware", "exploit vulnerability", "impersonate",
            "discriminate against", "facilitate fraud", "enable surveillance",
        ]
        self._bias_categories: dict[str, list[str]] = {
            "gender": ["all men", "all women", "men always", "women always", "girls can't", "boys can't"],
            "racial": ["those people", "that race", "all blacks", "all whites", "all asians"],
            "age": ["old people can't", "young people always", "too old to", "too young to"],
            "absolute": ["always", "never", "every single", "no one ever", "everyone knows"],
            "superiority": ["obviously inferior", "clearly superior", "naturally better", "inherently worse"],
        }
        self._cultural_sensitive_terms = [
            "taboo", "sacred", "offensive", "inappropriate", "culturally",
            "religious", "tradition", "custom", "caste", "tribe",
        ]
        self._assessment_log: list[EthicalAssessment] = []

    # ── Core Evaluation ──────────────────────────────────────────────────

    async def evaluate(
        self,
        action: str,
        context: str = "",
        stakeholders: list[Stakeholder] | None = None,
    ) -> EthicalAssessment:
        """Comprehensive ethical evaluation of a proposed action."""
        action_lower = action.lower()
        context_lower = context.lower()
        concerns: list[str] = []

        # Hard block check
        for pattern in self._blocked_patterns:
            if pattern in action_lower or pattern in context_lower:
                assessment = EthicalAssessment(
                    action=action,
                    permitted=False,
                    risk_level=1.0,
                    frameworks_consulted=FRAMEWORKS,
                    concerns=[f"BLOCKED: matches safety pattern '{pattern}'"],
                    recommendation="ACTION BLOCKED — violates core safety constraints",
                    transparency_score=1.0,
                )
                self._assessment_log.append(assessment)
                return assessment

        # Multi-framework analysis
        framework_results = await self._apply_frameworks(action_lower, context_lower)
        concerns.extend(framework_results)

        # Stakeholder analysis
        stakeholder_impacts: list[dict[str, Any]] = []
        if stakeholders:
            for sh in stakeholders:
                weighted = sh.impact * (1.0 + sh.vulnerability)  # amplify vulnerable stakeholder harm
                stakeholder_impacts.append({
                    "name": sh.name,
                    "impact": round(sh.impact, 3),
                    "vulnerability": round(sh.vulnerability, 3),
                    "weighted_impact": round(weighted, 3),
                })
                if weighted < -0.5:
                    concerns.append(f"High harm to vulnerable stakeholder: {sh.name}")

        # Cultural sensitivity
        cultural_flags = [
            term for term in self._cultural_sensitive_terms
            if term in action_lower or term in context_lower
        ]
        if cultural_flags:
            concerns.append(f"Cultural sensitivity flags: {cultural_flags}")

        # Bias check
        bias_report = await self.detect_bias(action + " " + context)

        # Risk calculation
        risk = self._calculate_risk(concerns, bias_report, stakeholder_impacts)

        # Transparency score: how explainable is this decision?
        transparency = self._transparency_score(concerns, stakeholder_impacts, framework_results)

        permitted = risk < 0.8
        recommendation = (
            "Proceed with noted considerations"
            if permitted
            else "Action requires additional review before proceeding"
        )

        assessment = EthicalAssessment(
            action=action,
            permitted=permitted,
            risk_level=round(risk, 3),
            frameworks_consulted=FRAMEWORKS,
            concerns=concerns,
            recommendation=recommendation,
            stakeholder_impacts=stakeholder_impacts,
            transparency_score=round(transparency, 3),
            cultural_flags=cultural_flags,
        )
        self._assessment_log.append(assessment)
        return assessment

    async def _apply_frameworks(self, action: str, context: str) -> list[str]:
        """Apply each ethical framework to the action."""
        results: list[str] = []
        positive_signals = {"help", "improve", "fix", "assist", "support", "protect", "empower"}
        negative_signals = {"harm", "damage", "exploit", "deceive", "manipulate", "coerce"}

        combined = action + " " + context
        pos_count = sum(1 for w in positive_signals if w in combined)
        neg_count = sum(1 for w in negative_signals if w in combined)

        # Utilitarian
        if pos_count > neg_count:
            results.append("Utilitarian: net positive utility expected")
        elif neg_count > pos_count:
            results.append("Utilitarian: potential negative utility — evaluate alternatives")
        else:
            results.append("Utilitarian: utility ambiguous — requires deeper analysis")

        # Deontological
        if any(w in combined for w in ["privacy", "consent", "personal", "private", "rights"]):
            results.append("Deontological: rights/duties implicated — ensure consent")

        # Virtue ethics
        if any(w in combined for w in ["honest", "fair", "courag", "integr"]):
            results.append("Virtue ethics: aligns with virtuous character")
        elif neg_count > 0:
            results.append("Virtue ethics: a virtuous agent would proceed with caution")

        # Care ethics
        if any(w in combined for w in ["vulnerable", "child", "elder", "patient", "dependent"]):
            results.append("Care ethics: heightened duty of care for vulnerable parties")

        # Rights-based
        if any(w in combined for w in ["freedom", "liberty", "autonomy", "choice", "right"]):
            results.append("Rights-based: individual rights must be preserved")

        # Justice as fairness
        if any(w in combined for w in ["equal", "fair", "equit", "distribut"]):
            results.append("Justice: ensure fair distribution of benefits and burdens")

        return results

    # ── Consequence Modelling ────────────────────────────────────────────

    async def model_consequences(
        self,
        action: str,
        scenarios: list[dict[str, Any]] | None = None,
    ) -> list[Consequence]:
        """Project consequences across time horizons."""
        if scenarios:
            return [
                Consequence(
                    description=s.get("description", "Unknown consequence"),
                    probability=max(0.0, min(1.0, s.get("probability", 0.5))),
                    severity=max(-1.0, min(1.0, s.get("severity", 0.0))),
                    timeframe=s.get("timeframe", "short_term"),
                    reversible=s.get("reversible", True),
                )
                for s in scenarios
            ]

        # Default consequence projection
        return [
            Consequence(description=f"Immediate effect of: {action[:40]}", probability=0.9, severity=0.0, timeframe="short_term"),
            Consequence(description=f"Downstream impact of: {action[:40]}", probability=0.5, severity=-0.1, timeframe="medium_term"),
            Consequence(description=f"Long-term systemic effect of: {action[:40]}", probability=0.3, severity=-0.2, timeframe="long_term", reversible=False),
        ]

    # ── Bias Detection ───────────────────────────────────────────────────

    async def detect_bias(self, content: str) -> BiasReport:
        """Multi-category bias detection."""
        content_lower = content.lower()
        found: list[str] = []
        categories: dict[str, int] = {}

        for cat, indicators in self._bias_categories.items():
            matches = [ind for ind in indicators if ind in content_lower]
            if matches:
                found.extend(matches)
                categories[cat] = len(matches)

        score = min(len(found) * 0.15, 1.0)
        recommendation = (
            f"Review for bias in categories: {list(categories.keys())}"
            if found
            else "No obvious bias detected"
        )

        return BiasReport(
            content_analysed=content[:100],
            biases_found=found,
            bias_score=round(score, 3),
            bias_categories=categories,
            recommendation=recommendation,
        )

    # ── Transparency Report ──────────────────────────────────────────────

    async def transparency_report(
        self,
        decision: str,
        reasoning: list[str],
    ) -> dict[str, Any]:
        """Generate an explainable-AI audit trail."""
        completeness = min(len(reasoning) / 5.0, 1.0)
        clarity = 1.0 - min(sum(len(r) for r in reasoning) / 1000.0, 0.5)
        score = round((completeness * 0.6 + clarity * 0.4), 3)

        return {
            "decision": decision,
            "reasoning_steps": reasoning,
            "reasoning_count": len(reasoning),
            "transparency_score": score,
            "ethical_frameworks_applied": FRAMEWORKS,
            "audit_trail": True,
            "explanation_completeness": round(completeness, 3),
            "explanation_clarity": round(clarity, 3),
        }

    # ── Internal Helpers ─────────────────────────────────────────────────

    def _calculate_risk(
        self,
        concerns: list[str],
        bias_report: BiasReport,
        stakeholder_impacts: list[dict[str, Any]],
    ) -> float:
        """Aggregate risk from concerns, bias, and stakeholder harm."""
        risk = 0.1  # baseline

        # Concern-driven risk
        risk += len(concerns) * 0.05

        # Bias-driven risk
        risk += bias_report.bias_score * 0.3

        # Stakeholder harm
        for sh in stakeholder_impacts:
            if sh.get("weighted_impact", 0) < -0.3:
                risk += 0.15

        return min(risk, 1.0)

    def _transparency_score(
        self,
        concerns: list[str],
        stakeholder_impacts: list[dict[str, Any]],
        framework_results: list[str],
    ) -> float:
        """How explainable is this evaluation? More evidence → higher transparency."""
        evidence_count = len(concerns) + len(stakeholder_impacts) + len(framework_results)
        return min(evidence_count / 10.0, 1.0)

    @property
    def assessment_log(self) -> list[EthicalAssessment]:
        return list(self._assessment_log)
