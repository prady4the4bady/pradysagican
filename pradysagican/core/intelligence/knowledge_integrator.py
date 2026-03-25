"""
Phase 7 - Knowledge Integration Engine (F636-F640)
====================================================
Merge multiple knowledge sources, resolve contradictions, and update world models.

Features:
- Knowledge source integration
- Contradiction detection and resolution
- Confidence-weighted merging
- World model updates
- Source credibility tracking
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Enums ─────────────────────────────────────────────────────────────────────

class SourceType(Enum):
    """Types of knowledge sources."""
    OBSERVATION = "observation"
    INFERENCE = "inference"
    EXPERT = "expert"
    CROWD = "crowd"
    EXTERNAL = "external"
    INTERNAL = "internal"


class ResolutionStrategy(Enum):
    """Strategies for resolving contradictions."""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_CONFIDENCE = "weighted_confidence"
    TEMPORAL_PRIORITY = "temporal_priority"
    SOURCE_CREDIBILITY = "source_credibility"
    EXPERT_OVERRIDE = "expert_override"


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class KnowledgeSource:
    """Represents a source of knowledge."""
    source_id: str
    source_type: SourceType
    name: str
    credibility: float = 0.5  # 0.0 = completely unreliable, 1.0 = perfectly reliable
    reliability_history: list[bool] = field(default_factory=list)
    last_updated: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_credibility(self) -> float:
        """Calculate dynamic credibility based on history."""
        if not self.reliability_history:
            return self.credibility

        recent_hits = sum(self.reliability_history[-10:])
        recent_count = min(len(self.reliability_history), 10)
        empirical_credibility = recent_hits / recent_count if recent_count > 0 else 0.5

        return 0.7 * self.credibility + 0.3 * empirical_credibility

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "name": self.name,
            "credibility": self.get_credibility(),
            "reliability_count": len(self.reliability_history),
            "last_updated": self.last_updated,
            "metadata": self.metadata,
        }


@dataclass
class KnowledgeFact:
    """Represents a fact from a knowledge source."""
    fact_id: str
    content: str
    source_id: str
    confidence: float = 0.5
    timestamp: float = 0.0
    properties: dict[str, Any] = field(default_factory=dict)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "content": self.content,
            "source_id": self.source_id,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "properties": self.properties,
            "evidence": self.evidence,
        }


@dataclass
class Contradiction:
    """Represents a contradiction between facts."""
    contradiction_id: str
    fact_ids: list[str]
    severity: float = 0.5  # 0.0 = minor, 1.0 = critical
    resolution: Optional[str] = None
    resolved: bool = False
    resolution_timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "contradiction_id": self.contradiction_id,
            "fact_ids": self.fact_ids,
            "severity": self.severity,
            "resolution": self.resolution,
            "resolved": self.resolved,
            "resolution_timestamp": self.resolution_timestamp,
        }


# ── Knowledge Integrator ───────────────────────────────────────────────────────

class KnowledgeIntegrator:
    """
    Integrates knowledge from multiple sources with conflict resolution.
    """

    def __init__(self) -> None:
        self._sources: dict[str, KnowledgeSource] = {}
        self._facts: dict[str, KnowledgeFact] = {}
        self._contradictions: dict[str, Contradiction] = {}
        self._merged_knowledge: dict[str, dict[str, Any]] = {}
        self._world_model: dict[str, Any] = {}
        logger.info("Initialized KnowledgeIntegrator")

    def register_source(
        self,
        name: str,
        source_type: SourceType,
        credibility: float = 0.5,
        metadata: Optional[dict[str, Any]] = None,
        source_id: Optional[str] = None,
    ) -> str:
        """Register a new knowledge source."""
        source_id = source_id or str(uuid.uuid4())[:8]

        if source_id in self._sources:
            logger.warning(f"Source {source_id} already registered")
            return source_id

        source = KnowledgeSource(
            source_id=source_id,
            source_type=source_type,
            name=name,
            credibility=credibility,
            metadata=metadata or {},
        )

        self._sources[source_id] = source
        logger.info(f"Registered source {source_id}: {name}")
        return source_id

    def add_fact(
        self,
        source_id: str,
        content: str,
        confidence: float = 0.5,
        properties: Optional[dict[str, Any]] = None,
        evidence: Optional[list[str]] = None,
        timestamp: float = 0.0,
    ) -> str:
        """Add a fact from a source."""
        if source_id not in self._sources:
            logger.error(f"Source {source_id} not found")
            return ""

        import time

        fact_id = str(uuid.uuid4())[:8]
        fact = KnowledgeFact(
            fact_id=fact_id,
            content=content,
            source_id=source_id,
            confidence=confidence,
            timestamp=timestamp or time.time(),
            properties=properties or {},
            evidence=evidence or [],
        )

        self._facts[fact_id] = fact
        logger.debug(f"Added fact {fact_id} from source {source_id}")
        return fact_id

    def get_fact(self, fact_id: str) -> Optional[KnowledgeFact]:
        """Retrieve a fact by ID."""
        return self._facts.get(fact_id)

    def integrate_sources(self) -> dict[str, Any]:
        """
        Integrate all sources into a unified knowledge representation.
        Returns merged facts grouped by content similarity.
        """
        logger.info("Integrating knowledge sources")

        self._detect_contradictions()

        grouped_facts = self._group_similar_facts()
        self._merged_knowledge = {}

        for group_id, facts in grouped_facts.items():
            merged = self._merge_facts(facts)
            self._merged_knowledge[group_id] = merged

        logger.info(
            f"Integration completed: {len(self._merged_knowledge)} merged fact groups"
        )

        return {
            "merged_facts": self._merged_knowledge,
            "contradictions_detected": len(self._contradictions),
            "resolved_contradictions": sum(
                1 for c in self._contradictions.values() if c.resolved
            ),
            "integration_confidence": self._calculate_integration_confidence(),
        }

    def _group_similar_facts(self) -> dict[str, list[KnowledgeFact]]:
        """Group facts with similar content."""
        groups: dict[str, list[KnowledgeFact]] = {}

        for fact in self._facts.values():
            found_group = False
            for group_id, group_facts in groups.items():
                similarity = self._calculate_content_similarity(fact.content, group_facts[0].content)
                if similarity > 0.7:
                    group_facts.append(fact)
                    found_group = True
                    break

            if not found_group:
                new_group_id = str(uuid.uuid4())[:8]
                groups[new_group_id] = [fact]

        return groups

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings."""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _merge_facts(self, facts: list[KnowledgeFact]) -> dict[str, Any]:
        """Merge multiple facts into a single representation."""
        if not facts:
            return {}

        weighted_confidence = sum(
            f.confidence * self._sources[f.source_id].get_credibility() for f in facts
        ) / sum(self._sources[f.source_id].get_credibility() for f in facts)

        sources_used = list(set(f.source_id for f in facts))
        all_evidence = []
        for f in facts:
            all_evidence.extend(f.evidence)

        return {
            "content": facts[0].content,
            "merged_confidence": min(1.0, weighted_confidence),
            "fact_count": len(facts),
            "sources": sources_used,
            "evidence": list(set(all_evidence)),
            "timestamp": max(f.timestamp for f in facts),
        }

    def detect_contradictions(self) -> dict[str, Any]:
        """Detect contradictions in the knowledge base."""
        return self._detect_contradictions()

    def _detect_contradictions(self) -> dict[str, Any]:
        """Internal method to detect contradictions."""
        contradictions_found = 0

        facts_list = list(self._facts.values())
        for i in range(len(facts_list)):
            for j in range(i + 1, len(facts_list)):
                fact1 = facts_list[i]
                fact2 = facts_list[j]

                if self._are_contradictory(fact1, fact2):
                    contradiction_id = str(uuid.uuid4())[:8]
                    contradiction = Contradiction(
                        contradiction_id=contradiction_id,
                        fact_ids=[fact1.fact_id, fact2.fact_id],
                        severity=abs(fact1.confidence - fact2.confidence),
                    )
                    self._contradictions[contradiction_id] = contradiction
                    contradictions_found += 1

        logger.info(f"Detected {contradictions_found} contradictions")
        return {
            "contradictions_detected": contradictions_found,
            "contradiction_ids": list(self._contradictions.keys()),
        }

    def _are_contradictory(self, fact1: KnowledgeFact, fact2: KnowledgeFact) -> bool:
        """Check if two facts are contradictory."""
        words1 = set(fact1.content.lower().split())
        words2 = set(fact2.content.lower().split())

        common_words = words1 & words2

        negations = {"not", "no", "cannot", "false", "deny", "reject"}

        fact1_negated = any(neg in fact1.content.lower() for neg in negations)
        fact2_negated = any(neg in fact2.content.lower() for neg in negations)

        return (
            len(common_words) > 2
            and fact1_negated != fact2_negated
            and abs(fact1.confidence - fact2.confidence) > 0.3
        )

    def resolve_contradictions(
        self, strategy: ResolutionStrategy = ResolutionStrategy.WEIGHTED_CONFIDENCE
    ) -> dict[str, Any]:
        """
        Resolve detected contradictions using specified strategy.
        """
        logger.info(f"Resolving contradictions using strategy: {strategy.value}")

        resolved_count = 0

        for contradiction in self._contradictions.values():
            if contradiction.resolved:
                continue

            if strategy == ResolutionStrategy.WEIGHTED_CONFIDENCE:
                resolved = self._resolve_by_confidence(contradiction)
            elif strategy == ResolutionStrategy.TEMPORAL_PRIORITY:
                resolved = self._resolve_by_temporal_priority(contradiction)
            elif strategy == ResolutionStrategy.SOURCE_CREDIBILITY:
                resolved = self._resolve_by_source_credibility(contradiction)
            elif strategy == ResolutionStrategy.EXPERT_OVERRIDE:
                resolved = self._resolve_by_expert_override(contradiction)
            else:
                resolved = self._resolve_by_majority_vote(contradiction)

            if resolved:
                contradiction.resolved = True
                resolved_count += 1

        logger.info(f"Resolved {resolved_count} contradictions")
        return {
            "resolution_strategy": strategy.value,
            "resolved_count": resolved_count,
            "total_contradictions": len(self._contradictions),
        }

    def _resolve_by_confidence(self, contradiction: Contradiction) -> bool:
        """Resolve by selecting the fact with highest confidence."""
        fact_ids = contradiction.fact_ids
        facts = [self._facts.get(fid) for fid in fact_ids if fid in self._facts]

        if facts:
            highest_confidence_fact = max(facts, key=lambda f: f.confidence)
            contradiction.resolution = f"Selected: {highest_confidence_fact.content}"
            return True

        return False

    def _resolve_by_temporal_priority(self, contradiction: Contradiction) -> bool:
        """Resolve by selecting the most recent fact."""
        fact_ids = contradiction.fact_ids
        facts = [self._facts.get(fid) for fid in fact_ids if fid in self._facts]

        if facts:
            most_recent = max(facts, key=lambda f: f.timestamp)
            contradiction.resolution = f"Selected (most recent): {most_recent.content}"
            return True

        return False

    def _resolve_by_source_credibility(self, contradiction: Contradiction) -> bool:
        """Resolve by selecting the fact from the most credible source."""
        fact_ids = contradiction.fact_ids
        facts = [self._facts.get(fid) for fid in fact_ids if fid in self._facts]

        if facts:
            most_credible = max(
                facts,
                key=lambda f: self._sources.get(f.source_id, KnowledgeSource(
                    "unknown", SourceType.EXTERNAL, "Unknown", 0.5
                )).get_credibility(),
            )
            contradiction.resolution = f"Selected (most credible source): {most_credible.content}"
            return True

        return False

    def _resolve_by_expert_override(self, contradiction: Contradiction) -> bool:
        """Resolve by preferring facts from expert sources."""
        fact_ids = contradiction.fact_ids
        facts = [self._facts.get(fid) for fid in fact_ids if fid in self._facts]

        for fact in facts:
            source = self._sources.get(fact.source_id)
            if source and source.source_type == SourceType.EXPERT:
                contradiction.resolution = f"Expert override: {fact.content}"
                return True

        if facts:
            contradiction.resolution = f"Default selection: {facts[0].content}"
            return True

        return False

    def _resolve_by_majority_vote(self, contradiction: Contradiction) -> bool:
        """Resolve by majority vote among similar facts."""
        fact_ids = contradiction.fact_ids
        facts = [self._facts.get(fid) for fid in fact_ids if fid in self._facts]

        if facts:
            highest_count_fact = max(facts, key=lambda f: f.confidence)
            contradiction.resolution = f"Majority: {highest_count_fact.content}"
            return True

        return False

    def _calculate_integration_confidence(self) -> float:
        """Calculate overall confidence of the integrated knowledge."""
        if not self._merged_knowledge:
            return 0.0

        confidences = [
            m.get("merged_confidence", 0.5) for m in self._merged_knowledge.values()
        ]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def update_world_model(self) -> dict[str, Any]:
        """
        Update the world model based on integrated knowledge.
        Returns the updated world model.
        """
        logger.info("Updating world model")

        self._world_model = {
            "merged_facts": len(self._merged_knowledge),
            "total_facts": len(self._facts),
            "total_sources": len(self._sources),
            "contradictions": len(
                [c for c in self._contradictions.values() if not c.resolved]
            ),
            "integrity_score": self._calculate_integrity_score(),
            "last_updated": len(self._facts) > 0,
        }

        logger.info("World model updated")
        return self._world_model

    def _calculate_integrity_score(self) -> float:
        """Calculate integrity score of the world model."""
        if not self._facts:
            return 0.5

        avg_confidence = sum(f.confidence for f in self._facts.values()) / len(self._facts)
        unresolved_contradictions = sum(
            1 for c in self._contradictions.values() if not c.resolved
        )
        contradiction_penalty = unresolved_contradictions * 0.1

        return max(0.0, min(1.0, avg_confidence - contradiction_penalty))

    def get_world_model(self) -> dict[str, Any]:
        """Get the current world model."""
        return self._world_model
