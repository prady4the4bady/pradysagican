"""Test suite for Phase 7 Temporal Reasoning (F626-F630)."""

import pytest
import time
from unittest.mock import Mock, patch

from pradysagican.core.intelligence.temporal_reasoning import (
    TemporalReasoner,
    TemporalEvent,
    EventType,
    TemporalRelation,
    CausalLink,
    CausalChain,
    TemporalConstraint,
    CounterfactualWorld,
)


class TestTemporalEvent:
    """Test TemporalEvent data structure."""

    def test_event_creation(self):
        """Test creating a temporal event."""
        current_time = time.time()
        event = TemporalEvent(
            id="e1",
            name="Event A",
            event_type=EventType.ACTION,
            timestamp=current_time,
            duration=5.0,
        )
        assert event.id == "e1"
        assert event.name == "Event A"
        assert event.event_type == EventType.ACTION
        assert event.timestamp == current_time
        assert event.duration == 5.0

    def test_event_uncertainty(self):
        """Test event uncertainty."""
        event = TemporalEvent(
            id="e1",
            name="Uncertain Event",
            event_type=EventType.OBSERVATION,
            timestamp=time.time(),
            uncertainty=0.7,
        )
        assert event.uncertainty == 0.7

    def test_event_serialization(self):
        """Test event serialization."""
        event = TemporalEvent(
            id="e1",
            name="Test",
            event_type=EventType.OUTCOME,
            timestamp=100.0,
        )
        event_dict = event.to_dict()
        assert event_dict["id"] == "e1"
        assert event_dict["type"] == "outcome"
        assert event_dict["timestamp"] == 100.0


class TestCausalLink:
    """Test CausalLink data structure."""

    def test_causal_link_creation(self):
        """Test creating a causal link."""
        link = CausalLink(
            id="c1",
            cause_id="e1",
            effect_id="e2",
            strength=0.8,
            mechanism="Direct causation",
        )
        assert link.cause_id == "e1"
        assert link.effect_id == "e2"
        assert link.strength == 0.8
        assert link.mechanism == "Direct causation"

    def test_causal_link_evidence(self):
        """Test causal link with evidence."""
        evidence = ["Observation 1", "Observation 2"]
        link = CausalLink(
            id="c1",
            cause_id="e1",
            effect_id="e2",
            evidence=evidence,
        )
        assert link.evidence == evidence


class TestTemporalReasoner:
    """Test TemporalReasoner functionality."""

    def test_reasoner_initialization(self):
        """Test initializing temporal reasoner."""
        reasoner = TemporalReasoner()
        assert len(reasoner._events) == 0
        assert len(reasoner._causal_links) == 0

    def test_add_event(self):
        """Test adding events."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        event_id = reasoner.add_event(
            name="Event A",
            event_type=EventType.ACTION,
            timestamp=current_time,
        )
        assert event_id in reasoner._events
        assert reasoner._events[event_id].name == "Event A"

    def test_add_multiple_events(self):
        """Test adding multiple events."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("E1", EventType.ACTION, current_time)
        e2 = reasoner.add_event("E2", EventType.OUTCOME, current_time + 1.0)
        e3 = reasoner.add_event("E3", EventType.OBSERVATION, current_time + 2.0)

        assert len(reasoner._events) == 3

    def test_add_causal_link(self):
        """Test adding causal links."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("Cause", EventType.ACTION, current_time)
        e2 = reasoner.add_event("Effect", EventType.OUTCOME, current_time + 1.0)

        link_id = reasoner.add_causal_link(e1, e2, strength=0.8)
        assert link_id in reasoner._causal_links
        assert reasoner._causal_links[link_id].strength == 0.8

    def test_add_temporal_constraint(self):
        """Test adding temporal constraints."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("E1", EventType.ACTION, current_time)
        e2 = reasoner.add_event("E2", EventType.OUTCOME, current_time + 2.0)

        constraint_id = reasoner.add_temporal_constraint(
            e1, e2, TemporalRelation.IMMEDIATELY_BEFORE, min_interval=1.0, max_interval=3.0
        )
        assert constraint_id in reasoner._constraints

    def test_get_event(self):
        """Test retrieving events."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        event_id = reasoner.add_event("Test", EventType.ACTION, current_time)
        event = reasoner.get_event(event_id)

        assert event is not None
        assert event.name == "Test"

    def test_find_causal_paths(self):
        """Test finding causal paths."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("E1", EventType.ACTION, current_time)
        e2 = reasoner.add_event("E2", EventType.OUTCOME, current_time + 1.0)
        e3 = reasoner.add_event("E3", EventType.OUTCOME, current_time + 2.0)

        reasoner.add_causal_link(e1, e2)
        reasoner.add_causal_link(e2, e3)

        paths = reasoner.find_causal_paths(e1, max_depth=3)
        assert len(paths) > 0

    def test_resolve_constraints_satisfied(self):
        """Test constraint resolution with satisfied constraints."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("E1", EventType.ACTION, current_time)
        e2 = reasoner.add_event("E2", EventType.OUTCOME, current_time + 2.0)

        reasoner.add_temporal_constraint(
            e1, e2, TemporalRelation.BEFORE
        )

        result = reasoner.resolve_constraints()
        assert result["consistency_score"] >= 0.0

    def test_resolve_constraints_violated(self):
        """Test constraint resolution with violated constraints."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("E1", EventType.ACTION, current_time)
        e2 = reasoner.add_event("E2", EventType.OUTCOME, current_time - 1.0)

        reasoner.add_temporal_constraint(e1, e2, TemporalRelation.BEFORE)

        result = reasoner.resolve_constraints()
        assert "violations" in result

    def test_simulate_counterfactual(self):
        """Test counterfactual simulation."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("Action", EventType.ACTION, current_time)
        e2 = reasoner.add_event("Effect", EventType.OUTCOME, current_time + 1.0)

        reasoner.add_causal_link(e1, e2, strength=0.8)

        modifications = {"timestamp": current_time + 10.0}
        result = reasoner.simulate_counterfactual(e1, modifications)

        assert "original_event" in result
        assert "predicted_effects" in result
        assert "modifications" in result

    def test_temporal_relations(self):
        """Test various temporal relations."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        base = reasoner.add_event("Base", EventType.ACTION, current_time)

        before_event = reasoner.add_event("Before", EventType.ACTION, current_time - 1.0)
        after_event = reasoner.add_event("After", EventType.ACTION, current_time + 1.0)

        reasoner.add_temporal_constraint(before_event, base, TemporalRelation.BEFORE)
        reasoner.add_temporal_constraint(base, after_event, TemporalRelation.BEFORE)

        result = reasoner.resolve_constraints()
        assert result["total_constraints"] >= 2

    def test_event_properties(self):
        """Test event properties."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        properties = {"location": "Boston", "participant": "Alice"}
        event_id = reasoner.add_event(
            "Meeting",
            EventType.ACTION,
            current_time,
            properties=properties,
        )

        event = reasoner.get_event(event_id)
        assert event.properties == properties

    def test_causal_chain_strength(self):
        """Test causal chain with strength tracking."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("E1", EventType.ACTION, current_time)
        e2 = reasoner.add_event("E2", EventType.OUTCOME, current_time + 1.0)
        e3 = reasoner.add_event("E3", EventType.OUTCOME, current_time + 2.0)

        link1 = reasoner.add_causal_link(e1, e2, strength=0.9)
        link2 = reasoner.add_causal_link(e2, e3, strength=0.7)

        links = [reasoner._causal_links[link1], reasoner._causal_links[link2]]
        chain = CausalChain(links)

        assert chain.length == 2
        assert chain.total_strength == 0.8


class TestCausalChain:
    """Test CausalChain functionality."""

    def test_chain_creation(self):
        """Test creating a causal chain."""
        links = [
            CausalLink(id="c1", cause_id="e1", effect_id="e2", strength=0.8),
            CausalLink(id="c2", cause_id="e2", effect_id="e3", strength=0.7),
        ]
        chain = CausalChain(links)
        assert chain.length == 2

    def test_chain_total_strength(self):
        """Test calculating total chain strength."""
        links = [
            CausalLink(id="c1", cause_id="e1", effect_id="e2", strength=0.9),
            CausalLink(id="c2", cause_id="e2", effect_id="e3", strength=0.8),
        ]
        chain = CausalChain(links)
        assert 0.8 < chain.total_strength <= 0.9

    def test_chain_mechanisms(self):
        """Test extracting mechanisms from chain."""
        links = [
            CausalLink(id="c1", cause_id="e1", effect_id="e2", mechanism="Direct"),
            CausalLink(id="c2", cause_id="e2", effect_id="e3", mechanism="Indirect"),
        ]
        chain = CausalChain(links)
        mechanisms = chain.get_mechanisms()
        assert len(mechanisms) == 2
        assert "Direct" in mechanisms

    def test_weakest_link(self):
        """Test finding weakest link in chain."""
        links = [
            CausalLink(id="c1", cause_id="e1", effect_id="e2", strength=0.9),
            CausalLink(id="c2", cause_id="e2", effect_id="e3", strength=0.4),
            CausalLink(id="c3", cause_id="e3", effect_id="e4", strength=0.7),
        ]
        chain = CausalChain(links)
        weakest = chain.get_weakest_link()
        assert weakest.strength == 0.4


class TestCounterfactualWorld:
    """Test CounterfactualWorld functionality."""

    def test_counterfactual_creation(self):
        """Test creating a counterfactual world."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("Event", EventType.ACTION, current_time)

        modifications = {"timestamp": current_time + 5.0}
        world = CounterfactualWorld(reasoner, {e1: modifications})

        assert world._base == reasoner
        assert world._modifications[e1] == modifications

    def test_apply_modifications(self):
        """Test applying counterfactual modifications."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("Event", EventType.ACTION, current_time)
        e2 = reasoner.add_event("Effect", EventType.OUTCOME, current_time + 1.0)
        reasoner.add_causal_link(e1, e2, strength=0.8)

        modifications = {e1: {"timestamp": current_time + 10.0}}
        world = CounterfactualWorld(reasoner, modifications)

        result = world.apply_modifications()
        assert "consequences" in result
        assert "feasibility" in result

    def test_counterfactual_feasibility(self):
        """Test feasibility assessment of counterfactual."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("Event", EventType.ACTION, current_time, uncertainty=0.1)
        reasoner.add_causal_link(e1, "nonexistent", strength=0.9)

        modifications = {e1: {"timestamp": current_time + 5.0}}
        world = CounterfactualWorld(reasoner, modifications)

        result = world.apply_modifications()
        feasibility = result["feasibility"]
        assert 0.0 <= feasibility <= 1.0


class TestTemporalConstraint:
    """Test TemporalConstraint data structure."""

    def test_constraint_creation(self):
        """Test creating a constraint."""
        constraint = TemporalConstraint(
            id="tc1",
            event1_id="e1",
            event2_id="e2",
            relation=TemporalRelation.BEFORE,
            min_interval=1.0,
            max_interval=5.0,
        )
        assert constraint.relation == TemporalRelation.BEFORE
        assert constraint.min_interval == 1.0


# Integration Tests

class TestTemporalIntegration:
    """Integration tests for temporal reasoning."""

    def test_complex_temporal_scenario(self):
        """Test complex temporal reasoning scenario."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        # Build a temporal scenario
        cause = reasoner.add_event("Cause", EventType.ACTION, current_time)
        intermediate = reasoner.add_event("Intermediate", EventType.OUTCOME, current_time + 1.0)
        effect = reasoner.add_event("Effect", EventType.OUTCOME, current_time + 2.0)

        reasoner.add_causal_link(cause, intermediate, strength=0.9)
        reasoner.add_causal_link(intermediate, effect, strength=0.8)

        reasoner.add_temporal_constraint(cause, intermediate, TemporalRelation.BEFORE)
        reasoner.add_temporal_constraint(intermediate, effect, TemporalRelation.BEFORE)

        paths = reasoner.find_causal_paths(cause)
        assert len(paths) > 0

        resolution = reasoner.resolve_constraints()
        assert resolution["consistency_score"] >= 0.0

    def test_causal_inference_with_uncertainty(self):
        """Test causal inference with uncertainty."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("Uncertain1", EventType.ACTION, current_time, uncertainty=0.5)
        e2 = reasoner.add_event("Uncertain2", EventType.OUTCOME, current_time + 1.0, uncertainty=0.3)

        reasoner.add_causal_link(e1, e2, strength=0.7)

        result = reasoner.simulate_counterfactual(e1, {"uncertainty": 0.1})
        assert "predicted_effects" in result

    def test_counterfactual_chain_reaction(self):
        """Test counterfactual with chain reactions."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        events = [
            reasoner.add_event(f"E{i}", EventType.ACTION if i == 0 else EventType.OUTCOME, current_time + i)
            for i in range(4)
        ]

        for i in range(len(events) - 1):
            reasoner.add_causal_link(events[i], events[i + 1], strength=0.8)

        modifications = {events[0]: {"timestamp": current_time + 10.0}}
        world = CounterfactualWorld(reasoner, modifications)

        result = world.apply_modifications()
        assert result["feasibility"] >= 0.0
