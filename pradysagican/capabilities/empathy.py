"""
Deep Empathy System — PRADYSAGICAN
Implements Plutchik's wheel of emotions, perspective-taking, Theory of Mind.
"""
from __future__ import annotations
import logging, time
from dataclasses import dataclass, field
from typing import Any
import numpy as np

logger = logging.getLogger(__name__)

# Plutchik's 8 primary emotions with opposing pairs
PLUTCHIK_WHEEL: dict[str, dict[str, Any]] = {
    "joy": {"opposite": "sadness", "intensity_low": "serenity", "intensity_high": "ecstasy"},
    "trust": {"opposite": "disgust", "intensity_low": "acceptance", "intensity_high": "admiration"},
    "fear": {"opposite": "anger", "intensity_low": "apprehension", "intensity_high": "terror"},
    "surprise": {"opposite": "anticipation", "intensity_low": "distraction", "intensity_high": "amazement"},
    "sadness": {"opposite": "joy", "intensity_low": "pensiveness", "intensity_high": "grief"},
    "disgust": {"opposite": "trust", "intensity_low": "boredom", "intensity_high": "loathing"},
    "anger": {"opposite": "fear", "intensity_low": "annoyance", "intensity_high": "rage"},
    "anticipation": {"opposite": "surprise", "intensity_low": "interest", "intensity_high": "vigilance"},
}

# Compound emotions (Plutchik dyads)
COMPOUND_EMOTIONS = {
    "love": ("joy", "trust"), "submission": ("trust", "fear"),
    "awe": ("fear", "surprise"), "disapproval": ("surprise", "sadness"),
    "remorse": ("sadness", "disgust"), "contempt": ("disgust", "anger"),
    "aggressiveness": ("anger", "anticipation"), "optimism": ("anticipation", "joy"),
}

EMOTION_KEYWORDS: dict[str, list[str]] = {
    "joy": ["happy", "glad", "excited", "wonderful", "great", "love", "amazing", "pleased"],
    "sadness": ["sad", "unhappy", "depressed", "miserable", "sorry", "disappointed", "hurt"],
    "anger": ["angry", "furious", "annoyed", "frustrated", "mad", "outraged", "irritated"],
    "fear": ["afraid", "scared", "anxious", "worried", "nervous", "terrified", "panicked"],
    "surprise": ["surprised", "shocked", "unexpected", "wow", "astonished", "amazed"],
    "disgust": ["disgusted", "revolted", "sick", "gross", "appalled", "repulsed"],
    "trust": ["trust", "believe", "reliable", "confident", "safe", "secure", "faith"],
    "anticipation": ["expect", "hope", "looking forward", "eager", "anticipate", "await"],
}

@dataclass
class EmotionState:
    primary: str = "neutral"
    intensity: float = 0.5
    secondary: str | None = None
    compound: str | None = None
    valence: float = 0.0
    arousal: float = 0.0
    confidence: float = 0.5

@dataclass
class Perspective:
    agent_id: str
    believed_emotions: EmotionState
    believed_goals: list[str] = field(default_factory=list)
    believed_knowledge: list[str] = field(default_factory=list)
    empathy_score: float = 0.0

class EmpathyEngine:
    """Emotional intelligence with Plutchik model and Theory of Mind."""

    def __init__(self) -> None:
        self._emotion_history: list[EmotionState] = []
        self._perspective_cache: dict[str, Perspective] = {}

    async def recognize_emotions(self, text: str) -> EmotionState:
        """Detect emotions from text using keyword analysis + valence model."""
        text_lower = text.lower()
        scores: dict[str, float] = {}
        for emotion, keywords in EMOTION_KEYWORDS.items():
            score = sum(1.0 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[emotion] = score

        if not scores:
            return EmotionState(primary="neutral", intensity=0.1, confidence=0.3)

        primary = max(scores, key=scores.get)
        intensity = min(scores[primary] / 3.0, 1.0)

        # Check for compound emotions
        sorted_emotions = sorted(scores.keys(), key=lambda e: scores[e], reverse=True)
        compound = None
        if len(sorted_emotions) >= 2:
            pair = (sorted_emotions[0], sorted_emotions[1])
            for comp_name, comp_pair in COMPOUND_EMOTIONS.items():
                if set(pair) == set(comp_pair):
                    compound = comp_name
                    break

        # Valence: positive emotions > 0, negative < 0
        positive = {"joy", "trust", "anticipation", "surprise"}
        negative = {"sadness", "anger", "fear", "disgust"}
        valence = sum(scores.get(e, 0) for e in positive) - sum(scores.get(e, 0) for e in negative)
        valence = max(-1.0, min(1.0, valence / 3.0))

        state = EmotionState(
            primary=primary, intensity=intensity, compound=compound,
            valence=valence, arousal=intensity, confidence=min(0.5 + intensity * 0.3, 0.95),
        )
        self._emotion_history.append(state)
        return state

    async def perspective_taking(self, agent_id: str, context: str) -> Perspective:
        """Model another entity\'s viewpoint (Theory of Mind)."""
        emotion = await self.recognize_emotions(context)
        perspective = Perspective(
            agent_id=agent_id, believed_emotions=emotion,
            empathy_score=emotion.intensity * 0.8,
        )
        self._perspective_cache[agent_id] = perspective
        return perspective

    async def compassionate_response(self, emotion: EmotionState) -> dict[str, str]:
        """Generate empathetic action plan based on detected emotion."""
        strategies = {
            "joy": {"action": "celebrate_with", "tone": "warm and enthusiastic"},
            "sadness": {"action": "comfort_and_support", "tone": "gentle and understanding"},
            "anger": {"action": "de_escalate", "tone": "calm and validating"},
            "fear": {"action": "reassure", "tone": "steady and protective"},
            "surprise": {"action": "clarify_and_orient", "tone": "informative and grounding"},
            "disgust": {"action": "acknowledge_and_redirect", "tone": "respectful and measured"},
            "trust": {"action": "reinforce_bond", "tone": "reliable and consistent"},
            "anticipation": {"action": "guide_forward", "tone": "encouraging and structured"},
        }
        return strategies.get(emotion.primary, {"action": "listen_actively", "tone": "neutral and attentive"})

    async def moral_reasoning(self, dilemma: str) -> dict[str, str]:
        """Evaluate ethical dilemma through multiple frameworks."""
        return {
            "utilitarian": f"Maximise total wellbeing: evaluate net happiness from '{dilemma[:50]}'",
            "deontological": f"Apply universal moral rules: check duties and rights in '{dilemma[:50]}'",
            "virtue_ethics": f"What would a virtuous person do regarding '{dilemma[:50]}'",
            "care_ethics": f"Prioritise relationships and care obligations in '{dilemma[:50]}'",
            "recommendation": "Synthesise all frameworks for balanced ethical judgment",
        }
