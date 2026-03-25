"""Sparse-autoencoder interpretability scaffolds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ActivationSAE:
    """Placeholder sparse feature encoder/decoder."""

    def encode(self, activations: list[float]) -> list[float]:
        return [a for a in activations if abs(a) > 0.1]

    def decode(self, sparse: list[float], size: int = 8) -> list[float]:
        out = [0.0] * size
        for i, v in enumerate(sparse[:size]):
            out[i] = v
        return out


@dataclass
class FeatureSteeringVectors:
    vectors: dict[str, list[float]] = field(default_factory=lambda: {
        "confidence": [0.1, 0.2, 0.3],
        "uncertainty": [-0.1, 0.05, 0.2],
        "creativity": [0.3, 0.1, -0.05],
        "caution": [0.2, -0.1, 0.15],
    })


class SteeringController:
    def apply(self, residual: list[float], steering: list[float], alpha: float = 0.5) -> list[float]:
        out = list(residual)
        for i in range(min(len(out), len(steering))):
            out[i] += alpha * steering[i]
        return out


class CircuitTracer:
    def trace(self, capability: str) -> dict[str, Any]:
        return {"capability": capability, "attention_heads": [0, 3, 7], "mlp_blocks": [2, 5]}


class FeatureAttribution:
    def attribute(self, tokens: list[str], features: list[str]) -> dict[str, list[str]]:
        return {tok: features[:2] for tok in tokens[:20]}


class HallucinationCircuit:
    def suppressible_components(self) -> list[str]:
        return ["head_3_7", "mlp_11", "residual_feature_hallucination_12"]

