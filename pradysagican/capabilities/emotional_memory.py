"""
Emotional Memory System — PRADYSAGICAN (NOVEL)
Implements somatic marker hypothesis (Damasio): emotions guide decisions.
Valence-arousal model for emotional state representation.
"""
from __future__ import annotations
import logging, time
from dataclasses import dataclass, field
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class EmotionalEvent:
    id: str
    content: str
    valence: float  # -1 (negative) to +1 (positive)
    arousal: float   # 0 (calm) to 1 (activated)
    category: str = "general"
    timestamp: float = field(default_factory=time.time)
    associations: list[str] = field(default_factory=list)

@dataclass
class MoodState:
    valence: float = 0.0
    arousal: float = 0.3
    dominant_emotion: str = "neutral"
    stability: float = 0.8  # How stable current mood is (0=volatile, 1=stable)

class EmotionalMemorySystem:
    """Stores experiences with emotional tags; emotions influence future decisions."""

    def __init__(self, decay_rate: float = 0.05) -> None:
        self._memories: list[EmotionalEvent] = []
        self._mood = MoodState()
        self._concept_valence: dict[str, list[float]] = {}  # concept -> list of valences
        self._decay_rate = decay_rate

    async def encode(self, content: str, valence: float, arousal: float, category: str = "general") -> EmotionalEvent:
        """Store an emotionally tagged experience."""
        event = EmotionalEvent(
            id=f"em_{len(self._memories)}_{int(time.time())}",
            content=content, valence=max(-1, min(1, valence)),
            arousal=max(0, min(1, arousal)), category=category,
        )
        self._memories.append(event)
        # Update concept associations
        for word in content.lower().split():
            if len(word) > 3:
                self._concept_valence.setdefault(word, []).append(valence)
        # Update mood (exponential moving average)
        alpha = 0.2
        self._mood.valence = self._mood.valence * (1 - alpha) + valence * alpha
        self._mood.arousal = self._mood.arousal * (1 - alpha) + arousal * alpha
        return event

    async def recall_by_emotion(self, target_valence: float, tolerance: float = 0.3, top_k: int = 5) -> list[EmotionalEvent]:
        """Retrieve memories with similar emotional tone."""
        matches = [(abs(m.valence - target_valence), m) for m in self._memories if abs(m.valence - target_valence) <= tolerance]
        matches.sort(key=lambda x: x[0])
        return [m for _, m in matches[:top_k]]

    async def emotional_association(self, concept: str) -> dict[str, float]:
        """Get emotional valence associated with a concept (somatic marker)."""
        valences = self._concept_valence.get(concept.lower(), [])
        if not valences:
            return {"concept": concept, "valence": 0.0, "strength": 0.0, "samples": 0}
        return {
            "concept": concept, "valence": float(np.mean(valences)),
            "strength": min(len(valences) * 0.1, 1.0), "samples": len(valences),
        }

    @property
    def mood(self) -> MoodState:
        return self._mood

    async def emotional_learning(self, outcome: str, valence: float) -> dict[str, Any]:
        """Learn from emotional outcomes to guide future decisions."""
        await self.encode(outcome, valence, abs(valence), "learning")
        trend = "positive" if self._mood.valence > 0.2 else "negative" if self._mood.valence < -0.2 else "neutral"
        return {"outcome_recorded": True, "mood_trend": trend, "total_memories": len(self._memories)}
