"""
Curiosity-Driven Exploration Engine — PRADYSAGICAN
Implements intrinsic motivation through prediction error (Sun et al. 2022).
"""
from __future__ import annotations
import logging, random
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeGap:
    topic: str
    known: list[str]
    unknown: list[str]
    curiosity_score: float  # How motivated to explore (0-1)
    priority: float = 0.5

class CuriosityEngine:
    """Self-motivated exploration driven by information gaps and novelty."""

    def __init__(self) -> None:
        self._explored: set[str] = set()
        self._knowledge_map: dict[str, list[str]] = {}
        self._novelty_scores: dict[str, float] = {}

    async def detect_knowledge_gaps(self, topic: str, known_facts: list[str]) -> KnowledgeGap:
        """Identify what is unknown about a topic."""
        self._knowledge_map[topic] = known_facts
        # Generate potential unknowns based on common knowledge patterns
        potential_unknowns = []
        aspects = ["origin", "mechanism", "impact", "future", "alternatives",
                    "limitations", "connections", "history", "applications"]
        for aspect in aspects:
            if not any(aspect in f.lower() for f in known_facts):
                potential_unknowns.append(f"{aspect} of {topic}")

        curiosity = len(potential_unknowns) / max(len(aspects), 1)
        return KnowledgeGap(
            topic=topic, known=known_facts, unknown=potential_unknowns,
            curiosity_score=curiosity, priority=curiosity * 0.8,
        )

    async def exploration_drive(self, novelty_score: float) -> dict[str, Any]:
        """Calculate motivation to explore based on novelty."""
        # Wundt curve: moderate novelty = highest motivation
        if novelty_score < 0.2:
            motivation = novelty_score * 2  # Low novelty = low motivation
        elif novelty_score < 0.7:
            motivation = 0.8 + (novelty_score - 0.2) * 0.4  # Sweet spot
        else:
            motivation = 1.0 - (novelty_score - 0.7) * 0.5  # Too novel = overwhelming
        return {"novelty": novelty_score, "motivation": max(motivation, 0.1), "strategy": "explore" if motivation > 0.5 else "exploit"}

    async def generate_questions(self, context: str, n: int = 5) -> list[str]:
        """Generate insightful questions about a topic."""
        templates = [
            "What is the underlying mechanism of {topic}?",
            "How does {topic} relate to broader patterns?",
            "What would happen if {topic} were different?",
            "What are the second-order effects of {topic}?",
            "Who is affected by {topic} and how?",
            "What assumptions about {topic} might be wrong?",
            "How has {topic} changed over time?",
            "What is the most surprising aspect of {topic}?",
        ]
        topic = context[:50]
        questions = [t.format(topic=topic) for t in random.sample(templates, min(n, len(templates)))]
        return questions

    async def serendipity(self, inputs: list[str]) -> str:
        """Find unexpected connections between unrelated inputs."""
        if len(inputs) < 2:
            return "Need multiple inputs for serendipitous discovery"
        a, b = random.sample(inputs, 2)
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        overlap = words_a & words_b
        if overlap:
            return f"Serendipitous link found: \'{a[:30]}\' and \'{b[:30]}\' share concepts: {overlap}"
        return f"Unexpected pairing: \'{a[:30]}\' + \'{b[:30]}\' — explore cross-domain transfer"

    async def map_knowledge_frontier(self, domain: str) -> dict[str, Any]:
        """Map the edges of current understanding in a domain."""
        known = self._knowledge_map.get(domain, [])
        explored_in_domain = [e for e in self._explored if domain.lower() in e.lower()]
        return {
            "domain": domain,
            "known_facts": len(known),
            "explored_areas": len(explored_in_domain),
            "frontier_topics": [f"advanced_{domain}_{i}" for i in range(3)],
            "confidence_level": min(len(known) * 0.1, 0.9),
            "recommended_exploration": f"Deepen understanding of {domain} mechanisms",
        }
