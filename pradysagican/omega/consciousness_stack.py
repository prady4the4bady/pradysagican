"""OMEGA Consciousness Stack: IIT + GWT + Predictive Coding scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConsciousnessMetric:
    phi: float
    gw_ignition_rate: float
    prediction_error_entropy: float

    @property
    def c_score(self) -> float:
        # Higher phi/gw is good; lower error entropy is good.
        return round((0.4 * self.phi) + (0.4 * self.gw_ignition_rate) + (0.2 * (1.0 - self.prediction_error_entropy)), 4)


class StrangeLoopDetector:
    """Detects self-referential self-model loops."""

    def detect(self, self_model_text: str) -> bool:
        text = self_model_text.lower()
        return "self-model" in text and ("myself" in text or "self-reference" in text or "about itself" in text)


class ElevationTrigger:
    """Elevates metacognitive mode when C-score is too low."""

    def __init__(self, threshold: float = 0.45) -> None:
        self.threshold = threshold

    def should_elevate(self, c_score: float) -> bool:
        return c_score < self.threshold


class CScoreMaximizer:
    """Secondary reward shaping utility for C-score optimization."""

    def reward_bonus(self, c_score: float, scale: float = 0.1) -> float:
        return round(max(0.0, c_score) * scale, 6)


class OmegaConsciousnessStack:
    """Five-layer consciousness scaffold with integration hooks."""

    def __init__(self) -> None:
        self.layer1_specialists: list[str] = []
        self.layer2_surprises: list[str] = []
        self.layer3_phi_monitor: float = 0.0
        self.layer4_workspace_payload: dict[str, Any] = {}
        self.layer5_self_model: str = ""
        self._loop_detector = StrangeLoopDetector()
        self._elevation = ElevationTrigger()

    def update(
        self,
        specialists: list[str],
        surprises: list[str],
        phi: float,
        gw_ignition_rate: float,
        prediction_error_entropy: float,
        self_model: str,
    ) -> dict[str, Any]:
        self.layer1_specialists = specialists
        self.layer2_surprises = surprises
        self.layer3_phi_monitor = phi
        self.layer4_workspace_payload = {"surprises": surprises[:10], "broadcast": bool(surprises)}
        self.layer5_self_model = self_model

        metric = ConsciousnessMetric(phi=phi, gw_ignition_rate=gw_ignition_rate, prediction_error_entropy=prediction_error_entropy)
        c_score = metric.c_score
        return {
            "c_score": c_score,
            "strange_loop": self._loop_detector.detect(self_model),
            "elevation_triggered": self._elevation.should_elevate(c_score),
            "workspace_broadcast": self.layer4_workspace_payload.get("broadcast", False),
        }

