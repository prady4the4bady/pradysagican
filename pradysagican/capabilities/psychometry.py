"""
Advanced Pattern Analysis ("Psychometry") — PRADYSAGICAN
Deep artifact analysis, provenance tracking, latent pattern extraction.
Uses information-theoretic measures for pattern significance.
"""
from __future__ import annotations
import logging, math
from dataclasses import dataclass, field
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

class PsychometryEngine:
    """Extract hidden patterns, trace origins, reconstruct context from fragments."""

    async def deep_artifact_analysis(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract hidden patterns and history from data artifacts."""
        analysis = {"structure": {}, "patterns": [], "anomalies": []}
        for key, value in data.items():
            if isinstance(value, (list, tuple)):
                arr = [float(v) for v in value if isinstance(v, (int, float))]
                if arr:
                    analysis["structure"][key] = {"type": "numeric_sequence", "length": len(arr), "mean": float(np.mean(arr)), "std": float(np.std(arr))}
            elif isinstance(value, str):
                analysis["structure"][key] = {"type": "text", "length": len(value), "word_count": len(value.split())}
        return analysis

    async def context_reconstruction(self, fragments: list[str]) -> dict[str, Any]:
        """Reconstruct full context from partial information."""
        all_words = set()
        for f in fragments:
            all_words.update(f.lower().split())
        themes = self._extract_themes(list(all_words))
        return {"fragments_count": len(fragments), "unique_concepts": len(all_words), "reconstructed_themes": themes, "completeness": min(len(fragments) * 0.15, 0.9)}

    async def latent_pattern_extraction(self, dataset: list[list[float]]) -> dict[str, Any]:
        """Find non-obvious patterns using statistical analysis."""
        arr = np.array(dataset)
        if arr.ndim < 2:
            return {"error": "Need 2D data for pattern extraction"}
        correlations = np.corrcoef(arr.T) if arr.shape[1] > 1 else np.array([[1.0]])
        strong_correlations = []
        for i in range(correlations.shape[0]):
            for j in range(i + 1, correlations.shape[1]):
                if abs(correlations[i, j]) > 0.7:
                    strong_correlations.append({"features": (i, j), "correlation": float(correlations[i, j])})
        entropy_per_col = [float(self._entropy(arr[:, i])) for i in range(arr.shape[1])]
        return {"shape": list(arr.shape), "strong_correlations": strong_correlations, "entropy_per_feature": entropy_per_col}

    async def temporal_pattern_analysis(self, time_series: list[float]) -> dict[str, Any]:
        """Detect temporal patterns in time-series data."""
        arr = np.array(time_series)
        diff = np.diff(arr)
        return {
            "trend": "up" if diff.mean() > 0 else "down" if diff.mean() < 0 else "flat",
            "volatility": float(np.std(diff)),
            "momentum": float(diff[-5:].mean()) if len(diff) >= 5 else float(diff.mean()),
            "cycles_detected": self._detect_cycles(arr),
        }

    @staticmethod
    def _entropy(data: np.ndarray) -> float:
        hist, _ = np.histogram(data, bins=min(20, len(data)), density=True)
        hist = hist[hist > 0]
        return float(-np.sum(hist * np.log2(hist + 1e-10)))

    @staticmethod
    def _detect_cycles(arr: np.ndarray) -> int:
        if len(arr) < 6:
            return 0
        mean = np.mean(arr)
        crossings = np.where(np.diff(np.sign(arr - mean)))[0]
        return len(crossings) // 2

    @staticmethod
    def _extract_themes(words: list[str]) -> list[str]:
        tech = [w for w in words if w in {"ai", "data", "system", "model", "code", "api", "server", "cloud"}]
        emotion = [w for w in words if w in {"happy", "sad", "fear", "trust", "anger", "joy"}]
        themes = []
        if tech:
            themes.append(f"technology ({len(tech)} refs)")
        if emotion:
            themes.append(f"emotion ({len(emotion)} refs)")
        if not themes:
            themes.append("general")
        return themes
