"""
Phase 7 - Temporal Reasoning Engine (F626-F630)
=================================================
Temporal constraint satisfaction, causal inference, and counterfactual reasoning.

Features:
- Temporal event modeling and scheduling
- Causal chain discovery and inference
- Counterfactual simulation
- Temporal constraint resolution
- Causality strength measurement
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ── Enums ─────────────────────────────────────────────────────────────────────

class EventType(Enum):
    """Types of temporal events."""
    ACTION = "action"
    STATE = "state"
    OUTCOME = "outcome"
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"


class TemporalRelation(Enum):
    """Temporal relationships between events."""
    BEFORE = "before"
    AFTER = "after"
    CONCURRENT = "concurrent"
    OVERLAPS = "overlaps"
    DURING = "during"
    IMMEDIATELY_BEFORE = "immediately_before"
    IMMEDIATELY_AFTER = "immediately_after"


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class TemporalEvent:
    """Representation of a temporal event."""
    id: str
    name: str
    event_type: EventType
    timestamp: float
    duration: float = 0.0
    properties: dict[str, Any] = field(default_factory=dict)
    uncertainty: float = 0.0  # 0.0 = certain, 1.0 = completely uncertain
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.event_type.value,
            "timestamp": self.timestamp,
            "duration": self.duration,
            "properties": self.properties,
            "uncertainty": self.uncertainty,
            "confidence": self.confidence,
        }


@dataclass
class CausalLink:
    """Causal relationship between events."""
    id: str
    cause_id: str
    effect_id: str
    strength: float = 0.5  # 0.0 = no causality, 1.0 = definite causality
    mechanism: Optional[str] = None
    evidence: list[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "cause_id": self.cause_id,
            "effect_id": self.effect_id,
            "strength": self.strength,
            "mechanism": self.mechanism,
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


@dataclass
class TemporalConstraint:
    """Constraint on temporal relationships."""
    id: str
    event1_id: str
    event2_id: str
    relation: TemporalRelation
    min_interval: float = 0.0
    max_interval: float = float("inf")
    flexibility: float = 0.5  # How flexible the constraint is

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "event1_id": self.event1_id,
            "event2_id": self.event2_id,
            "relation": self.relation.value,
            "min_interval": self.min_interval,
            "max_interval": self.max_interval,
            "flexibility": self.flexibility,
        }


# ── Temporal Event Management ──────────────────────────────────────────────────

class TemporalReasoner:
    """
    Manages temporal events, causal relationships, and constraint satisfaction.
    """

    def __init__(self) -> None:
        self._events: dict[str, TemporalEvent] = {}
        self._causal_links: dict[str, CausalLink] = {}
        self._constraints: dict[str, TemporalConstraint] = {}
        self._event_index: dict[float, list[str]] = {}  # timestamp -> event_ids
        logger.info("Initialized TemporalReasoner")

    def add_event(
        self,
        name: str,
        event_type: EventType,
        timestamp: float,
        duration: float = 0.0,
        properties: Optional[dict[str, Any]] = None,
        uncertainty: float = 0.0,
        event_id: Optional[str] = None,
    ) -> str:
        """Add a temporal event."""
        event_id = event_id or str(uuid.uuid4())[:8]

        if event_id in self._events:
            logger.warning(f"Event {event_id} already exists")
            return event_id

        event = TemporalEvent(
            id=event_id,
            name=name,
            event_type=event_type,
            timestamp=timestamp,
            duration=duration,
            properties=properties or {},
            uncertainty=uncertainty,
        )

        self._events[event_id] = event

        if timestamp not in self._event_index:
            self._event_index[timestamp] = []
        self._event_index[timestamp].append(event_id)

        logger.debug(f"Added event {event_id}: {name} at {timestamp}")
        return event_id

    def add_causal_link(
        self,
        cause_id: str,
        effect_id: str,
        strength: float = 0.5,
        mechanism: Optional[str] = None,
        evidence: Optional[list[str]] = None,
    ) -> str:
        """Add a causal relationship between two events."""
        if cause_id not in self._events or effect_id not in self._events:
            logger.error("Cause or effect event not found")
            return ""

        link_id = str(uuid.uuid4())[:8]
        link = CausalLink(
            id=link_id,
            cause_id=cause_id,
            effect_id=effect_id,
            strength=strength,
            mechanism=mechanism,
            evidence=evidence or [],
        )

        self._causal_links[link_id] = link
        logger.debug(f"Added causal link {link_id}: {cause_id} -> {effect_id}")
        return link_id

    def add_temporal_constraint(
        self,
        event1_id: str,
        event2_id: str,
        relation: TemporalRelation,
        min_interval: float = 0.0,
        max_interval: float = float("inf"),
    ) -> str:
        """Add a temporal constraint between events."""
        if event1_id not in self._events or event2_id not in self._events:
            logger.error("Event not found")
            return ""

        constraint_id = str(uuid.uuid4())[:8]
        constraint = TemporalConstraint(
            id=constraint_id,
            event1_id=event1_id,
            event2_id=event2_id,
            relation=relation,
            min_interval=min_interval,
            max_interval=max_interval,
        )

        self._constraints[constraint_id] = constraint
        logger.debug(f"Added constraint {constraint_id}: {event1_id} {relation.value} {event2_id}")
        return constraint_id

    def get_event(self, event_id: str) -> Optional[TemporalEvent]:
        """Retrieve an event by ID."""
        return self._events.get(event_id)

    def find_causal_paths(
        self, start_event_id: str, max_depth: int = 5
    ) -> list[list[CausalLink]]:
        """
        Find all causal paths starting from an event.
        Returns chains of causality.
        """
        logger.info(f"Finding causal paths from {start_event_id}")

        if start_event_id not in self._events:
            logger.error(f"Event {start_event_id} not found")
            return []

        paths = []
        visited_per_path = {start_event_id}
        queue = [(start_event_id, [], visited_per_path)]

        while queue:
            current_id, current_path, visited = queue.pop(0)

            if len(current_path) >= max_depth:
                continue

            for link in self._causal_links.values():
                if link.cause_id == current_id and link.effect_id not in visited:
                    new_visited = visited.copy()
                    new_visited.add(link.effect_id)
                    new_path = current_path + [link]

                    if len(new_path) >= 1:
                        paths.append(new_path)

                    queue.append((link.effect_id, new_path, new_visited))

        logger.info(f"Found {len(paths)} causal paths")
        return paths

    def resolve_constraints(self) -> dict[str, Any]:
        """
        Resolve temporal constraints using constraint satisfaction.
        Returns schedule consistency and any violations.
        """
        logger.info("Resolving temporal constraints")

        violations = []
        satisfied = 0

        for constraint in self._constraints.values():
            event1 = self._events.get(constraint.event1_id)
            event2 = self._events.get(constraint.event2_id)

            if not event1 or not event2:
                continue

            time_diff = event2.timestamp - event1.timestamp

            is_satisfied = self._check_temporal_relation(
                time_diff, constraint.relation, constraint.min_interval, constraint.max_interval
            )

            if is_satisfied:
                satisfied += 1
            else:
                violations.append(
                    {
                        "constraint_id": constraint.id,
                        "event1": event1.name,
                        "event2": event2.name,
                        "expected": constraint.relation.value,
                        "actual_diff": time_diff,
                    }
                )

        result = {
            "total_constraints": len(self._constraints),
            "satisfied": satisfied,
            "violations": violations,
            "consistency_score": satisfied / max(len(self._constraints), 1),
        }

        logger.info(
            f"Constraints resolved: {satisfied}/{len(self._constraints)} satisfied"
        )
        return result

    def _check_temporal_relation(
        self,
        time_diff: float,
        relation: TemporalRelation,
        min_interval: float,
        max_interval: float,
    ) -> bool:
        """Check if a temporal relationship is satisfied."""
        epsilon = 0.001

        if relation == TemporalRelation.BEFORE:
            return time_diff > epsilon
        elif relation == TemporalRelation.AFTER:
            return time_diff < -epsilon
        elif relation == TemporalRelation.CONCURRENT:
            return abs(time_diff) < epsilon
        elif relation == TemporalRelation.OVERLAPS:
            return min_interval <= abs(time_diff) <= max_interval
        elif relation == TemporalRelation.IMMEDIATELY_BEFORE:
            return 0 < time_diff <= min_interval
        elif relation == TemporalRelation.IMMEDIATELY_AFTER:
            return -min_interval <= time_diff < 0
        else:
            return True

    def simulate_counterfactual(
        self, event_id: str, modified_properties: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Simulate what would happen if an event were different.
        Returns predicted consequences.
        """
        logger.info(f"Simulating counterfactual for event {event_id}")

        if event_id not in self._events:
            logger.error(f"Event {event_id} not found")
            return {}

        original_event = self._events[event_id]

        predictions = {
            "original_event": original_event.to_dict(),
            "modifications": modified_properties,
            "predicted_effects": [],
            "confidence": 1.0,
        }

        for link in self._causal_links.values():
            if link.cause_id == event_id:
                effect_event = self._events.get(link.effect_id)
                if effect_event:
                    predictions["predicted_effects"].append(
                        {
                            "effect": effect_event.name,
                            "strength": link.strength,
                            "mechanism": link.mechanism,
                            "confidence": link.confidence,
                        }
                    )

        if predictions["predicted_effects"]:
            confidences = [e["confidence"] for e in predictions["predicted_effects"]]
            predictions["confidence"] = sum(confidences) / len(confidences)

        logger.info(
            f"Counterfactual simulation completed: {len(predictions['predicted_effects'])} effects"
        )
        return predictions


# ── Causal Chain Analysis ──────────────────────────────────────────────────────

class CausalChain:
    """
    Represents a chain of causal relationships.
    Analyzes causality strength and mechanisms.
    """

    def __init__(self, links: list[CausalLink]) -> None:
        self._links = links

    @property
    def length(self) -> int:
        """Number of links in the chain."""
        return len(self._links)

    @property
    def total_strength(self) -> float:
        """Cumulative causal strength of the chain."""
        if not self._links:
            return 0.0
        return sum(l.strength for l in self._links) / len(self._links)

    @property
    def total_confidence(self) -> float:
        """Cumulative confidence of the chain."""
        if not self._links:
            return 0.0
        return sum(l.confidence for l in self._links) / len(self._links)

    def get_mechanisms(self) -> list[str]:
        """Get all causal mechanisms in the chain."""
        return [link.mechanism for link in self._links if link.mechanism]

    def get_weakest_link(self) -> Optional[CausalLink]:
        """Find the weakest link in the causal chain."""
        if not self._links:
            return None
        return min(self._links, key=lambda l: l.strength)

    def to_dict(self) -> dict[str, Any]:
        return {
            "links": [link.to_dict() for link in self._links],
            "length": self.length,
            "total_strength": self.total_strength,
            "total_confidence": self.total_confidence,
            "mechanisms": self.get_mechanisms(),
        }


# ── Counterfactual World ───────────────────────────────────────────────────────

class CounterfactualWorld:
    """
    Represents an alternate timeline with modified events.
    Used for "what-if" reasoning and consequence exploration.
    """

    def __init__(self, base_reasoner: TemporalReasoner, modifications: dict[str, Any]) -> None:
        self._base = base_reasoner
        self._modifications = modifications
        self._alternative_events: dict[str, TemporalEvent] = {}
        self._alternative_causal_links: dict[str, CausalLink] = {}
        self._consequences: list[dict[str, Any]] = []

    def apply_modifications(self) -> dict[str, Any]:
        """
        Apply modifications and compute consequences.
        Returns the results of the counterfactual world.
        """
        logger.info(f"Applying counterfactual modifications: {len(self._modifications)}")

        for event_id, props in self._modifications.items():
            if event_id in self._base._events:
                original = self._base._events[event_id]
                modified = TemporalEvent(
                    id=original.id,
                    name=original.name,
                    event_type=original.event_type,
                    timestamp=props.get("timestamp", original.timestamp),
                    duration=props.get("duration", original.duration),
                    properties={**original.properties, **props.get("properties", {})},
                    uncertainty=props.get("uncertainty", original.uncertainty),
                    confidence=props.get("confidence", original.confidence),
                )
                self._alternative_events[event_id] = modified

        self._propagate_consequences()

        result = {
            "modifications": self._modifications,
            "alternative_events": {k: v.to_dict() for k, v in self._alternative_events.items()},
            "consequences": self._consequences,
            "feasibility": self._assess_feasibility(),
        }

        logger.info(f"Counterfactual analysis completed: {len(self._consequences)} consequences")
        return result

    def _propagate_consequences(self) -> None:
        """Propagate consequences through causal chains."""
        for link in self._base._causal_links.values():
            if link.cause_id in self._alternative_events:
                effect = self._base._events.get(link.effect_id)
                if effect:
                    self._consequences.append(
                        {
                            "event": effect.name,
                            "type": effect.event_type.value,
                            "causal_mechanism": link.mechanism,
                            "strength": link.strength,
                            "confidence": link.confidence,
                        }
                    )

    def _assess_feasibility(self) -> float:
        """Assess how feasible this counterfactual world is."""
        if not self._consequences:
            return 0.5

        confidence_scores = [c.get("confidence", 0.5) for c in self._consequences]
        return sum(confidence_scores) / len(confidence_scores)

    def to_dict(self) -> dict[str, Any]:
        return {
            "modifications": self._modifications,
            "consequences": self._consequences,
            "feasibility": self._assess_feasibility(),
        }
