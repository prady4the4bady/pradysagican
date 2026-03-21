"""
Consciousness Engine — PRADYSAGICAN's self-awareness substrate.
================================================================
Novel architecture combining:
- Butlin et al. (2023) consciousness indicators (14 indicators from neuroscience)
- BriSe AI 5-layer Self hierarchy (Zeng et al. 2024)
- Kahneman dual-process theory (System 1 / System 2)
- AE Studio recursive self-referential processing
- Lindsey/Anthropic perturbation-detection introspection
- Iida (2025) minimalist 3-layer artificial consciousness model

This engine does NOT claim actual machine consciousness — it implements
functional analogs that produce consciousness-like behaviors: self-monitoring,
metacognition, introspection, and recursive self-modeling.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

import numpy as np

from pradysagican.config import ConsciousnessLevel, ReasoningMode

logger = logging.getLogger(__name__)


# ── Data Structures ───────────────────────────────────────────────────────────

class AwarenessLevel(IntEnum):
    """Quantized awareness spectrum (0-6) mapping to ConsciousnessLevel."""
    DORMANT = 0
    PERCEPTION = 1
    BODILY_SELF = 2
    AUTONOMOUS_SELF = 3
    SOCIAL_SELF = 4
    CONCEPTUAL_SELF = 5
    FULL_AWARENESS = 6


@dataclass
class SelfState:
    """Current snapshot of the system's self-model."""
    awareness: AwarenessLevel = AwarenessLevel.PERCEPTION
    confidence: float = 0.5
    cognitive_load: float = 0.0      # 0.0 = idle, 1.0 = saturated
    active_goals: list[str] = field(default_factory=list)
    capabilities_map: dict[str, float] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    emotional_valence: float = 0.0   # -1 negative … +1 positive
    emotional_arousal: float = 0.0   # 0 calm … 1 activated
    reasoning_mode: ReasoningMode = ReasoningMode.HYBRID
    timestamp: float = field(default_factory=time.time)

    def fingerprint(self) -> str:
        """Hash of state for change-detection."""
        raw = f"{self.awareness}|{self.confidence:.2f}|{self.cognitive_load:.2f}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class IntrospectionReport:
    """Result of an introspection cycle."""
    state_before: SelfState
    state_after: SelfState
    perturbation_detected: bool = False
    metacognitive_notes: list[str] = field(default_factory=list)
    reasoning_quality_score: float = 0.0
    self_consistency_score: float = 0.0
    recommendations: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


# ── Consciousness Engine ──────────────────────────────────────────────────────

class ConsciousnessEngine:
    """
    Implements functional consciousness analogs for PRADYSAGICAN.

    Architecture (3 interacting layers, after Iida 2025):
      Layer 1 — Instinctive Response (fast reactions, System 1)
      Layer 2 — Pattern Prediction (world model integration)
      Layer 3 — Cognitive Integration (metacognition, self-model)

    The engine continuously maintains a self-model and can detect when
    its own processing has been perturbed (Lindsey/Anthropic approach).
    """

    def __init__(self, max_history: int = 256) -> None:
        self._state = SelfState()
        self._history: deque[SelfState] = deque(maxlen=max_history)
        self._perturbation_baseline: np.ndarray | None = None
        self._metacognitive_log: deque[str] = deque(maxlen=512)
        self._attention_weights: dict[str, float] = {}
        self._cycle_count: int = 0
        self._lock = asyncio.Lock()
        logger.info("ConsciousnessEngine initialised at PERCEPTION level")

    # ── Self-Model Management ─────────────────────────────────────────────

    @property
    def state(self) -> SelfState:
        return self._state

    async def update_self_model(
        self,
        *,
        confidence: float | None = None,
        cognitive_load: float | None = None,
        goals: list[str] | None = None,
        valence: float | None = None,
        arousal: float | None = None,
    ) -> SelfState:
        """Update the self-model with new observations."""
        async with self._lock:
            prev = self._state
            self._history.append(prev)

            self._state = SelfState(
                awareness=self._compute_awareness(),
                confidence=_clamp(confidence if confidence is not None else prev.confidence),
                cognitive_load=_clamp(cognitive_load if cognitive_load is not None else prev.cognitive_load),
                active_goals=goals if goals is not None else prev.active_goals,
                capabilities_map=prev.capabilities_map,
                limitations=prev.limitations,
                emotional_valence=_clamp(valence if valence is not None else prev.emotional_valence, -1, 1),
                emotional_arousal=_clamp(arousal if arousal is not None else prev.emotional_arousal),
                reasoning_mode=self._select_reasoning_mode(),
            )
            self._cycle_count += 1
            return self._state

    def _compute_awareness(self) -> AwarenessLevel:
        """
        Determine awareness level from current state signals.
        Higher cognitive load + more goals + social context → higher awareness.
        """
        score = 0.0
        s = self._state
        score += min(s.cognitive_load * 2, 1.5)
        score += min(len(s.active_goals) * 0.3, 1.5)
        score += 0.5 if s.emotional_arousal > 0.4 else 0.0
        score += 0.5 if len(self._attention_weights) > 3 else 0.0
        score += 1.0 if self._cycle_count > 10 else 0.0
        # Social context adds social-self awareness
        score += 0.5 if any("social" in g.lower() or "user" in g.lower() for g in s.active_goals) else 0.0

        level_idx = int(min(score, 6))
        return AwarenessLevel(level_idx)

    def _select_reasoning_mode(self) -> ReasoningMode:
        """Auto-select reasoning mode based on cognitive load and task complexity."""
        load = self._state.cognitive_load
        if load < 0.3:
            return ReasoningMode.SYSTEM_1
        elif load > 0.7:
            return ReasoningMode.SYSTEM_2
        return ReasoningMode.HYBRID

    # ── Metacognitive Monitor ─────────────────────────────────────────────

    async def metacognitive_check(
        self, reasoning_trace: list[str], outcome_quality: float
    ) -> dict[str, Any]:
        """
        Monitor own reasoning quality in real-time.
        Evaluates coherence, consistency, and identifies reasoning failures.
        """
        checks: dict[str, Any] = {}

        # 1. Coherence: are reasoning steps logically connected?
        coherence = self._evaluate_coherence(reasoning_trace)
        checks["coherence"] = coherence

        # 2. Consistency: does this align with past reasoning on similar topics?
        consistency = self._evaluate_consistency(reasoning_trace)
        checks["consistency"] = consistency

        # 3. Confidence calibration: is confidence appropriate for outcome?
        calibration_error = abs(self._state.confidence - outcome_quality)
        checks["calibration_error"] = calibration_error
        checks["overconfident"] = self._state.confidence > outcome_quality + 0.2

        # 4. Cognitive biases detection
        biases = self._detect_biases(reasoning_trace)
        checks["detected_biases"] = biases

        # 5. Overall metacognitive score
        score = (coherence + consistency + (1 - calibration_error)) / 3
        checks["metacognitive_score"] = score

        note = f"cycle={self._cycle_count} meta_score={score:.2f} biases={biases}"
        self._metacognitive_log.append(note)
        logger.debug("Metacognitive check: %s", note)

        # Auto-adjust confidence based on monitoring
        await self.update_self_model(confidence=self._state.confidence * 0.8 + score * 0.2)

        return checks

    def _evaluate_coherence(self, trace: list[str]) -> float:
        """Check logical flow between reasoning steps."""
        if len(trace) < 2:
            return 1.0
        # Measure overlap between consecutive steps (shared concepts = coherent)
        scores = []
        for i in range(1, len(trace)):
            words_prev = set(trace[i - 1].lower().split())
            words_curr = set(trace[i].lower().split())
            if not words_prev or not words_curr:
                scores.append(0.5)
                continue
            overlap = len(words_prev & words_curr) / max(len(words_prev | words_curr), 1)
            scores.append(min(overlap * 3, 1.0))  # Scale up, some overlap is natural
        return float(np.mean(scores)) if scores else 0.5

    def _evaluate_consistency(self, trace: list[str]) -> float:
        """Check if current reasoning aligns with established patterns."""
        if not self._metacognitive_log:
            return 0.7  # Default for first interaction
        # Compare current trace length / complexity to historical average
        avg_len = np.mean([len(log) for log in self._metacognitive_log]) if self._metacognitive_log else 50
        current_len = sum(len(s) for s in trace)
        ratio = min(current_len, avg_len) / max(current_len, avg_len, 1)
        return float(ratio)

    def _detect_biases(self, trace: list[str]) -> list[str]:
        """Detect common cognitive biases in reasoning."""
        biases = []
        full_text = " ".join(trace).lower()

        bias_patterns = {
            "confirmation_bias": ["obviously", "clearly", "everyone knows", "it's certain"],
            "anchoring": ["first", "initial", "starting point", "based on the original"],
            "availability": ["recently", "just saw", "common example", "i recall"],
            "sunk_cost": ["already invested", "come this far", "can't stop now"],
            "bandwagon": ["everyone", "popular", "most people", "trend"],
        }
        for bias_name, markers in bias_patterns.items():
            if any(m in full_text for m in markers):
                biases.append(bias_name)
        return biases

    # ── Introspection Layer ───────────────────────────────────────────────

    async def introspect(self) -> IntrospectionReport:
        """
        Full introspection cycle: examine own state, detect perturbations,
        generate recommendations. Inspired by Lindsey (Anthropic) perturbation
        detection — the system notices when its processing has been altered.
        """
        start = time.monotonic()
        state_before = self._state

        # Check for perturbation (unexpected state change)
        perturbation = self._detect_perturbation()

        # Generate metacognitive notes
        notes = []
        if self._state.cognitive_load > 0.8:
            notes.append("WARNING: Cognitive load critically high — consider task delegation")
        if self._state.confidence < 0.3:
            notes.append("LOW CONFIDENCE: Seek additional information before proceeding")
        if perturbation:
            notes.append("PERTURBATION DETECTED: Internal state changed unexpectedly")
        if self._state.emotional_arousal > 0.7:
            notes.append("HIGH AROUSAL: Engage System 2 deliberative processing")

        # Self-consistency check
        consistency = self._self_consistency_score()

        # Recommendations
        recs = []
        if self._state.reasoning_mode == ReasoningMode.SYSTEM_1 and self._state.cognitive_load > 0.5:
            recs.append("Switch to SYSTEM_2 for current task complexity")
        if consistency < 0.5:
            recs.append("Re-evaluate recent decisions — low self-consistency detected")
        if len(self._state.active_goals) > 5:
            recs.append("Too many active goals — prioritise and defer lower-priority items")

        state_after = await self.update_self_model()
        elapsed = (time.monotonic() - start) * 1000

        return IntrospectionReport(
            state_before=state_before,
            state_after=state_after,
            perturbation_detected=perturbation,
            metacognitive_notes=notes,
            reasoning_quality_score=consistency,
            self_consistency_score=consistency,
            recommendations=recs,
            duration_ms=elapsed,
        )

    def _detect_perturbation(self) -> bool:
        """Detect if internal state has been unexpectedly altered."""
        if len(self._history) < 2:
            return False
        recent = list(self._history)[-3:]
        fingerprints = [s.fingerprint() for s in recent]
        # If all recent states are identical, no perturbation
        if len(set(fingerprints)) <= 1:
            return False
        # Check for sudden jumps in confidence or load
        loads = [s.cognitive_load for s in recent]
        if len(loads) >= 2 and abs(loads[-1] - loads[-2]) > 0.4:
            return True
        confidences = [s.confidence for s in recent]
        if len(confidences) >= 2 and abs(confidences[-1] - confidences[-2]) > 0.3:
            return True
        return False

    def _self_consistency_score(self) -> float:
        """Measure how consistent current state is with recent history."""
        if len(self._history) < 3:
            return 0.7
        recent = list(self._history)[-5:]
        loads = [s.cognitive_load for s in recent]
        confs = [s.confidence for s in recent]
        # Low variance = high consistency
        load_var = float(np.var(loads)) if loads else 0.0
        conf_var = float(np.var(confs)) if confs else 0.0
        score = 1.0 - min((load_var + conf_var) * 2, 1.0)
        return max(score, 0.0)

    # ── Recursive Self-Attention ──────────────────────────────────────────

    async def recursive_self_attention(self, focus_topic: str, depth: int = 3) -> list[str]:
        """
        Focus attention on own attention patterns — recursive self-reference.
        Inspired by AE Studio's self-referential processing experiments.
        Returns progressive insights at each recursion depth.
        """
        insights: list[str] = []
        current_focus = focus_topic

        for d in range(depth):
            # Level d: observe what we're attending to
            observation = (
                f"[Depth {d}] Attending to: '{current_focus}' | "
                f"awareness={self._state.awareness.name} | "
                f"load={self._state.cognitive_load:.2f}"
            )
            insights.append(observation)

            # Update attention weights
            self._attention_weights[f"depth_{d}"] = 1.0 / (d + 1)

            # Shift focus to meta-level: "what am I paying attention to?"
            current_focus = f"my attention on '{current_focus}'"

            # Each depth increases cognitive load slightly
            await self.update_self_model(
                cognitive_load=min(self._state.cognitive_load + 0.1, 1.0)
            )

        return insights

    # ── Global Workspace (consciousness broadcast) ────────────────────────

    async def broadcast_to_workspace(self, content: dict[str, Any]) -> dict[str, Any]:
        """
        Global Workspace Theory implementation: broadcast important information
        to all cognitive modules simultaneously.
        """
        broadcast = {
            "source": "consciousness_engine",
            "content": content,
            "awareness_level": self._state.awareness.name,
            "priority": content.get("priority", 0.5),
            "timestamp": time.time(),
            "reasoning_mode": self._state.reasoning_mode,
        }
        logger.info("GWT broadcast: priority=%.2f awareness=%s",
                     broadcast["priority"], broadcast["awareness_level"])
        return broadcast


# ── Helpers ───────────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))
