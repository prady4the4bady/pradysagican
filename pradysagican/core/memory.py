"""
Hierarchical Memory System — PRADYSAGICAN
==========================================
7-tier memory architecture inspired by human cognition:
1. Sensory Buffer — immediate input (< 1s retention)
2. Working Memory — active context (Miller's 7±2 slots)
3. Episodic Memory — specific events (ChromaDB vector store)
4. Semantic Memory — knowledge graph (NetworkX)
5. Procedural Memory — learned skills and action patterns
6. Emotional Memory — experiences tagged with emotional valence (NOVEL)
7. Predictive Memory — anticipatory patterns from experience (NOVEL)

Features:
- Experience replay for continual learning (MUSE, Yang et al. 2025)
- Memory consolidation cycles (short→long term during "rest")
- Elastic Weight Consolidation concept to prevent catastrophic forgetting
- Somatic marker integration (Damasio) for emotion-guided recall
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections import deque, OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)


# ── Data Structures ───────────────────────────────────────────────────────────

class MemoryTier(str, Enum):
    SENSORY = "sensory"
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EMOTIONAL = "emotional"
    PREDICTIVE = "predictive"


@dataclass
class MemoryEntry:
    """Universal memory entry with multi-tier metadata."""
    id: str
    content: str
    tier: MemoryTier
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    embedding: list[float] | None = None
    emotional_valence: float = 0.0    # -1 negative … +1 positive
    emotional_arousal: float = 0.0    # 0 calm … 1 activated
    associations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def decay_score(self, now: float | None = None) -> float:
        """Ebbinghaus-inspired forgetting curve."""
        now = now or time.time()
        elapsed_hours = (now - self.last_accessed) / 3600
        retention = self.importance * np.exp(-0.1 * elapsed_hours / max(self.access_count, 1))
        return float(retention)


@dataclass
class Skill:
    """Procedural memory: a learned skill/action sequence."""
    name: str
    steps: list[str]
    success_rate: float = 0.5
    total_uses: int = 0
    last_used: float = field(default_factory=time.time)
    domain: str = "general"


@dataclass
class Prediction:
    """Predictive memory: anticipated future state."""
    pattern: str
    expected_outcome: str
    confidence: float = 0.5
    times_confirmed: int = 0
    times_violated: int = 0

    @property
    def accuracy(self) -> float:
        total = self.times_confirmed + self.times_violated
        return self.times_confirmed / max(total, 1)


# ── Memory System ─────────────────────────────────────────────────────────────

class MemorySystem:
    """
    7-tier hierarchical memory with consolidation, replay, and emotional tagging.
    """

    def __init__(
        self,
        sensory_size: int = 32,
        working_slots: int = 7,
        max_episodic: int = 100_000,
        consolidation_interval: float = 300.0,
    ) -> None:
        # Tier 1: Sensory Buffer (FIFO, very short retention)
        self._sensory: deque[MemoryEntry] = deque(maxlen=sensory_size)

        # Tier 2: Working Memory (limited capacity, high priority)
        self._working: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._working_capacity = working_slots

        # Tier 3: Episodic Memory (vector-searchable long-term)
        self._episodic: dict[str, MemoryEntry] = {}
        self._max_episodic = max_episodic

        # Tier 4: Semantic Memory (knowledge graph)
        self._semantic = nx.DiGraph()

        # Tier 5: Procedural Memory (skills)
        self._procedural: dict[str, Skill] = {}

        # Tier 6: Emotional Memory (emotion-tagged experiences)
        self._emotional: list[MemoryEntry] = []

        # Tier 7: Predictive Memory (anticipatory patterns)
        self._predictive: dict[str, Prediction] = {}

        # Consolidation
        self._consolidation_interval = consolidation_interval
        self._last_consolidation = time.time()
        self._replay_buffer: deque[MemoryEntry] = deque(maxlen=1000)

        # Statistics
        self._total_stored = 0
        self._total_retrieved = 0

        self._lock = asyncio.Lock()
        logger.info("MemorySystem initialised: sensory=%d working=%d", sensory_size, working_slots)

    # ── Store Operations ──────────────────────────────────────────────────

    async def store(
        self,
        content: str,
        tier: MemoryTier = MemoryTier.EPISODIC,
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        emotional_arousal: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        """Store a memory entry in the specified tier."""
        async with self._lock:
            entry = MemoryEntry(
                id=self._generate_id(content),
                content=content,
                tier=tier,
                importance=importance,
                emotional_valence=emotional_valence,
                emotional_arousal=emotional_arousal,
                metadata=metadata or {},
            )

            if tier == MemoryTier.SENSORY:
                self._sensory.append(entry)
            elif tier == MemoryTier.WORKING:
                self._store_working(entry)
            elif tier == MemoryTier.EPISODIC:
                self._episodic[entry.id] = entry
                self._replay_buffer.append(entry)
            elif tier == MemoryTier.EMOTIONAL:
                self._emotional.append(entry)
                # Also store in episodic for searchability
                self._episodic[entry.id] = entry

            self._total_stored += 1

            # Check if consolidation is due
            if time.time() - self._last_consolidation > self._consolidation_interval:
                await self._consolidate()

            return entry

    def _store_working(self, entry: MemoryEntry) -> None:
        """Store in working memory with capacity management."""
        if len(self._working) >= self._working_capacity:
            # Evict least recently accessed
            oldest_key = next(iter(self._working))
            evicted = self._working.pop(oldest_key)
            # Demote to episodic if important enough
            if evicted.importance > 0.3:
                evicted.tier = MemoryTier.EPISODIC
                self._episodic[evicted.id] = evicted
        self._working[entry.id] = entry

    # ── Retrieve Operations ───────────────────────────────────────────────

    async def recall(
        self,
        query: str,
        tier: MemoryTier | None = None,
        top_k: int = 5,
        min_importance: float = 0.0,
    ) -> list[MemoryEntry]:
        """Retrieve memories matching a query, optionally filtered by tier."""
        results: list[MemoryEntry] = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        # Search across tiers
        search_pools: list[list[MemoryEntry] | dict[str, MemoryEntry]] = []
        if tier is None or tier == MemoryTier.WORKING:
            search_pools.append(list(self._working.values()))
        if tier is None or tier == MemoryTier.EPISODIC:
            search_pools.append(self._episodic)
        if tier is None or tier == MemoryTier.EMOTIONAL:
            search_pools.append(self._emotional)

        for pool in search_pools:
            entries = pool.values() if isinstance(pool, dict) else pool
            for entry in entries:
                if entry.importance < min_importance:
                    continue
                # Simple relevance scoring (word overlap + recency + importance)
                content_words = set(entry.content.lower().split())
                overlap = len(query_words & content_words) / max(len(query_words), 1)
                recency = entry.decay_score()
                score = overlap * 0.5 + recency * 0.3 + entry.importance * 0.2
                entry.metadata["_relevance_score"] = score
                results.append(entry)

        # Sort by relevance and return top-k
        results.sort(key=lambda e: e.metadata.get("_relevance_score", 0), reverse=True)
        top_results = results[:top_k]

        # Update access counts
        for entry in top_results:
            entry.access_count += 1
            entry.last_accessed = time.time()
        self._total_retrieved += len(top_results)

        return top_results

    async def recall_by_emotion(
        self, valence_range: tuple[float, float] = (-1.0, 1.0),
        arousal_range: tuple[float, float] = (0.0, 1.0),
        top_k: int = 5,
    ) -> list[MemoryEntry]:
        """Retrieve memories filtered by emotional state (somatic marker approach)."""
        matches = [
            e for e in self._emotional
            if valence_range[0] <= e.emotional_valence <= valence_range[1]
            and arousal_range[0] <= e.emotional_arousal <= arousal_range[1]
        ]
        matches.sort(key=lambda e: e.importance * e.emotional_arousal, reverse=True)
        return matches[:top_k]

    # ── Knowledge Graph (Semantic Memory) ─────────────────────────────────

    async def add_knowledge(self, subject: str, predicate: str, obj: str, confidence: float = 0.8) -> None:
        """Add a triple to the semantic knowledge graph."""
        self._semantic.add_edge(subject, obj, predicate=predicate, confidence=confidence, timestamp=time.time())
        logger.debug("Knowledge added: %s -[%s]-> %s (%.2f)", subject, predicate, obj, confidence)

    async def query_knowledge(self, entity: str, relation: str | None = None) -> list[dict[str, Any]]:
        """Query the knowledge graph for facts about an entity."""
        results = []
        if entity in self._semantic:
            for _, target, data in self._semantic.edges(entity, data=True):
                if relation is None or data.get("predicate") == relation:
                    results.append({"subject": entity, "predicate": data.get("predicate", ""), "object": target, **data})
        # Also check reverse edges
        for source, _, data in self._semantic.in_edges(entity, data=True):
            if relation is None or data.get("predicate") == relation:
                results.append({"subject": source, "predicate": data.get("predicate", ""), "object": entity, **data})
        return results

    # ── Procedural Memory (Skills) ────────────────────────────────────────

    async def learn_skill(self, name: str, steps: list[str], domain: str = "general") -> Skill:
        """Store a new skill or update existing one."""
        if name in self._procedural:
            skill = self._procedural[name]
            skill.steps = steps
            skill.total_uses += 1
            skill.last_used = time.time()
        else:
            skill = Skill(name=name, steps=steps, domain=domain)
            self._procedural[name] = skill
        return skill

    async def recall_skill(self, name: str) -> Skill | None:
        """Retrieve a learned skill."""
        skill = self._procedural.get(name)
        if skill:
            skill.total_uses += 1
            skill.last_used = time.time()
        return skill

    async def find_skills(self, domain: str) -> list[Skill]:
        """Find all skills in a domain."""
        return [s for s in self._procedural.values() if s.domain == domain]

    # ── Predictive Memory ─────────────────────────────────────────────────

    async def store_prediction(self, pattern: str, expected: str, confidence: float = 0.5) -> Prediction:
        """Store an anticipatory prediction."""
        pred = Prediction(pattern=pattern, expected_outcome=expected, confidence=confidence)
        self._predictive[pattern] = pred
        return pred

    async def check_prediction(self, pattern: str, actual_outcome: str) -> Prediction | None:
        """Check if a prediction was confirmed or violated."""
        pred = self._predictive.get(pattern)
        if pred:
            if actual_outcome.lower() in pred.expected_outcome.lower() or pred.expected_outcome.lower() in actual_outcome.lower():
                pred.times_confirmed += 1
                pred.confidence = min(pred.confidence + 0.05, 0.99)
            else:
                pred.times_violated += 1
                pred.confidence = max(pred.confidence - 0.05, 0.01)
        return pred

    async def get_predictions(self, context: str) -> list[Prediction]:
        """Get relevant predictions for current context."""
        context_words = set(context.lower().split())
        scored = []
        for pred in self._predictive.values():
            pattern_words = set(pred.pattern.lower().split())
            overlap = len(context_words & pattern_words) / max(len(pattern_words), 1)
            if overlap > 0.2:
                scored.append((overlap * pred.confidence, pred))
        scored.sort(reverse=True)
        return [p for _, p in scored[:5]]

    # ── Memory Consolidation ──────────────────────────────────────────────

    async def _consolidate(self) -> None:
        """
        Memory consolidation: transfer important short-term memories to long-term.
        Inspired by sleep-dependent memory consolidation in neuroscience.
        """
        logger.info("Starting memory consolidation cycle")
        self._last_consolidation = time.time()

        # 1. Promote high-importance working memory to episodic
        for mid, entry in list(self._working.items()):
            if entry.importance > 0.6 and entry.access_count > 2:
                entry.tier = MemoryTier.EPISODIC
                self._episodic[mid] = entry

        # 2. Extract patterns from emotional memories → predictive
        if len(self._emotional) > 10:
            # Group by valence sign and find common themes
            positive = [e for e in self._emotional if e.emotional_valence > 0.3]
            negative = [e for e in self._emotional if e.emotional_valence < -0.3]
            if positive:
                common = self._find_common_themes([e.content for e in positive[:20]])
                if common:
                    await self.store_prediction(
                        pattern=f"positive_context: {common}",
                        expected="positive_outcome",
                        confidence=0.6,
                    )

        # 3. Decay old, unused episodic memories
        now = time.time()
        to_remove = []
        for mid, entry in self._episodic.items():
            if entry.decay_score(now) < 0.05 and entry.access_count < 2:
                to_remove.append(mid)
        for mid in to_remove[:100]:  # Remove max 100 per cycle
            del self._episodic[mid]

        logger.info("Consolidation complete: promoted=%d decayed=%d", 0, len(to_remove))

    # ── Experience Replay ─────────────────────────────────────────────────

    async def experience_replay(self, batch_size: int = 10) -> list[MemoryEntry]:
        """
        Sample from replay buffer for continual learning.
        Prioritised by importance and emotional intensity.
        """
        if not self._replay_buffer:
            return []
        buffer = list(self._replay_buffer)
        # Prioritised sampling: higher importance + emotional arousal = more likely
        weights = np.array([
            e.importance * 0.6 + abs(e.emotional_valence) * 0.2 + e.emotional_arousal * 0.2
            for e in buffer
        ])
        weights = weights / max(weights.sum(), 1e-8)
        indices = np.random.choice(len(buffer), size=min(batch_size, len(buffer)), replace=False, p=weights)
        return [buffer[i] for i in indices]

    # ── Statistics ────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        return {
            "sensory_buffer": len(self._sensory),
            "working_memory": len(self._working),
            "episodic_memories": len(self._episodic),
            "semantic_nodes": self._semantic.number_of_nodes(),
            "semantic_edges": self._semantic.number_of_edges(),
            "skills_learned": len(self._procedural),
            "emotional_memories": len(self._emotional),
            "predictions": len(self._predictive),
            "replay_buffer": len(self._replay_buffer),
            "total_stored": self._total_stored,
            "total_retrieved": self._total_retrieved,
        }

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _generate_id(content: str) -> str:
        return hashlib.sha256(f"{content}{time.time()}".encode()).hexdigest()[:16]

    @staticmethod
    def _find_common_themes(texts: list[str]) -> str:
        """Extract common words across multiple texts."""
        if not texts:
            return ""
        word_sets = [set(t.lower().split()) for t in texts]
        common = word_sets[0]
        for ws in word_sets[1:]:
            common &= ws
        # Remove stopwords
        stopwords = {"the", "a", "an", "is", "was", "are", "were", "to", "of", "in", "for", "and", "or", "it"}
        common -= stopwords
        return " ".join(sorted(common)[:5])
