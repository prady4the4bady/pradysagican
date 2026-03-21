"""
Intuition System — PRADYSAGICAN (NOVEL INVENTION)
Based on Kahneman\'s "Thinking Fast and Slow" dual-process theory.
Implements System 1 rapid pattern matching via compressed experience representations.
"""
from __future__ import annotations
import logging, time, math
from dataclasses import dataclass, field
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class GutFeeling:
    assessment: str
    confidence: float
    basis: str  # what triggered this feeling
    is_alarm: bool = False
    processing_time_ms: float = 0.0

@dataclass
class AnomalySignal:
    description: str
    severity: float  # 0-1
    surprise_score: float  # Bayesian surprise
    context: str = ""

class IntuitionEngine:
    """System 1 rapid cognition: gut feelings, pattern matching, anomaly detection."""

    def __init__(self, experience_window: int = 1000) -> None:
        self._experience_buffer: list[dict[str, Any]] = []
        self._pattern_cache: dict[str, float] = {}
        self._baseline_stats: dict[str, float] = {}
        self._window = experience_window

    async def gut_feeling(self, situation: str) -> GutFeeling:
        """Rapid assessment without explicit reasoning (System 1)."""
        start = time.monotonic()
        # Hash-based rapid pattern lookup
        words = set(situation.lower().split())
        danger_words = {"error", "fail", "crash", "danger", "warning", "critical", "urgent", "broken"}
        positive_words = {"success", "good", "great", "working", "complete", "solved", "improved"}
        danger_overlap = len(words & danger_words)
        positive_overlap = len(words & positive_words)

        if danger_overlap > positive_overlap:
            assessment = "negative — potential risk detected"
            confidence = min(0.5 + danger_overlap * 0.15, 0.9)
            is_alarm = danger_overlap >= 2
        elif positive_overlap > danger_overlap:
            assessment = "positive — situation appears favorable"
            confidence = min(0.5 + positive_overlap * 0.15, 0.9)
            is_alarm = False
        else:
            assessment = "neutral — insufficient signal for rapid judgment"
            confidence = 0.3
            is_alarm = False

        elapsed = (time.monotonic() - start) * 1000
        return GutFeeling(
            assessment=assessment, confidence=confidence,
            basis=f"pattern_match on {len(words)} tokens",
            is_alarm=is_alarm, processing_time_ms=elapsed,
        )

    async def pattern_recognition_fast(self, data: list[float]) -> dict[str, Any]:
        """Instant pattern detection from numerical data (System 1)."""
        arr = np.array(data)
        return {
            "trend": "increasing" if arr[-1] > arr[0] else "decreasing" if arr[-1] < arr[0] else "stable",
            "volatility": float(np.std(arr)),
            "mean": float(np.mean(arr)),
            "outliers": int(np.sum(np.abs(arr - np.mean(arr)) > 2 * np.std(arr))),
            "monotonic": bool(np.all(np.diff(arr) >= 0) or np.all(np.diff(arr) <= 0)),
        }

    async def anomaly_detection(self, baseline: list[float], current: list[float]) -> AnomalySignal:
        """Bayesian surprise-based anomaly detection."""
        b, c = np.array(baseline), np.array(current)
        b_mean, b_std = float(np.mean(b)), float(np.std(b)) + 1e-8
        c_mean = float(np.mean(c))
        z_score = abs(c_mean - b_mean) / b_std
        # Bayesian surprise = KL divergence approximation
        surprise = 0.5 * ((b_std / (np.std(c) + 1e-8))**2 + (c_mean - b_mean)**2 / b_std**2 - 1 + 2 * math.log((np.std(c) + 1e-8) / b_std))
        severity = min(z_score / 5.0, 1.0)

        return AnomalySignal(
            description=f"Deviation: z={z_score:.2f}, mean shifted {b_mean:.2f}→{c_mean:.2f}",
            severity=severity,
            surprise_score=float(max(surprise, 0)),
            context=f"baseline_n={len(baseline)} current_n={len(current)}",
        )

    async def predictive_intuition(self, context: str) -> list[str]:
        """Anticipate likely developments from context."""
        predictions = []
        lower = context.lower()
        if "deadline" in lower or "due" in lower:
            predictions.append("Time pressure likely — prioritise essential tasks")
        if "error" in lower or "bug" in lower:
            predictions.append("Technical issue may cascade — investigate root cause")
        if "meeting" in lower or "review" in lower:
            predictions.append("Social interaction upcoming — prepare key points")
        if "new" in lower or "start" in lower:
            predictions.append("Novel situation — allocate extra exploration time")
        if not predictions:
            predictions.append("Situation appears routine — maintain standard operations")
        return predictions

    async def creative_leap(self, known_facts: list[str]) -> str:
        """Find non-obvious connections between facts (creative System 1)."""
        if len(known_facts) < 2:
            return "Need at least 2 facts for creative connection"
        # Find shared and unique concepts
        word_sets = [set(f.lower().split()) for f in known_facts]
        shared = word_sets[0]
        for ws in word_sets[1:]:
            shared &= ws
        unique_per_fact = [ws - shared for ws in word_sets]
        bridges = []
        for i, uniq in enumerate(unique_per_fact):
            for j, other_uniq in enumerate(unique_per_fact):
                if i < j:
                    # Look for conceptual bridges
                    combined = uniq | other_uniq
                    bridges.append(f"Connecting concept_{i} and concept_{j} through {len(combined)} unique terms")
        return bridges[0] if bridges else "No creative bridge found — facts may be unrelated"
