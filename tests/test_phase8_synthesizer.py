"""Test suite for Phase 8 System Synthesizer (F646-F650)."""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch

from pradysagican.core.godmode.synthesizer import (
    SystemSynthesizer,
    CapabilityRegistry,
    FeatureRouter,
    Capability,
    RoutingDecision,
    PipelineOptimization,
    PerformanceEstimate,
    FeaturePhase,
    CapabilityType,
    RequestType,
)


class TestCapabilityRegistry:
    """Test CapabilityRegistry functionality."""

    def test_registry_initialization(self):
        """Test registry initializes with all capabilities."""
        registry = CapabilityRegistry()
        assert registry.get_capability_count() >= 45  # At least phases 1-7
        assert registry.get_capability_count() <= 60  # Max F601-F660

    def test_register_capability(self):
        """Test registering a new capability."""
        registry = CapabilityRegistry()
        initial_count = registry.get_capability_count()

        cap = Capability(
            capability_id="test_cap",
            feature_code="F999",
            name="TestCapability",
            phase=FeaturePhase.PHASE8,
            capability_type=CapabilityType.LEARNING,
            module_path="test.module",
            primary_function="Test function",
        )

        registry.register_capability(cap)
        assert registry.get_capability_count() == initial_count + 1

    def test_get_capability_by_feature(self):
        """Test retrieving capability by feature code."""
        registry = CapabilityRegistry()
        cap = registry.get_capability_by_feature("F601")
        assert cap is not None
        assert cap.feature_code == "F601"

    def test_get_capabilities_by_type(self):
        """Test retrieving capabilities by type."""
        registry = CapabilityRegistry()
        learning_caps = registry.get_capabilities_by_type(CapabilityType.LEARNING)
        assert len(learning_caps) > 0
        assert all(c.capability_type == CapabilityType.LEARNING for c in learning_caps)

    def test_get_capabilities_by_phase(self):
        """Test retrieving capabilities by phase."""
        registry = CapabilityRegistry()
        phase1_caps = registry.get_capabilities_by_phase(FeaturePhase.PHASE1)
        assert len(phase1_caps) > 0
        assert all(c.phase == FeaturePhase.PHASE1 for c in phase1_caps)

    def test_all_phases_have_capabilities(self):
        """Test all phases have at least one capability."""
        registry = CapabilityRegistry()
        phases = [FeaturePhase.PHASE1, FeaturePhase.PHASE2, FeaturePhase.PHASE3,
                  FeaturePhase.PHASE4, FeaturePhase.PHASE5, FeaturePhase.PHASE6,
                  FeaturePhase.PHASE7]
        for phase in phases:
            caps = registry.get_capabilities_by_phase(phase)
            assert len(caps) > 0, f"Phase {phase.value} has no capabilities"

    def test_get_all_capabilities(self):
        """Test getting all capabilities."""
        registry = CapabilityRegistry()
        all_caps = registry.get_all_capabilities()
        assert len(all_caps) >= 45
        assert all(isinstance(c, Capability) for c in all_caps)


class TestFeatureRouter:
    """Test FeatureRouter functionality."""

    def test_router_initialization(self):
        """Test router initializes."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)
        assert router.registry is not None
        assert len(router.routing_history) == 0

    def test_route_query_request(self):
        """Test routing query request."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        decision = router.route_request(
            RequestType.QUERY,
            {"domain": "test"},
        )

        assert decision is not None
        assert decision.request_type == RequestType.QUERY
        assert len(decision.selected_capabilities) > 0
        assert len(decision.pipeline_order) > 0

    def test_route_learning_request(self):
        """Test routing learning request."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        decision = router.route_request(
            RequestType.LEARNING,
            {"data": "test"},
        )

        assert decision.request_type == RequestType.LEARNING
        assert all(
            c.capability_type == CapabilityType.LEARNING
            for c in decision.selected_capabilities
        )

    def test_route_evolution_request(self):
        """Test routing evolution request."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        decision = router.route_request(
            RequestType.EVOLUTION,
            {"population_size": 50},
        )

        assert decision.request_type == RequestType.EVOLUTION
        assert all(
            c.capability_type == CapabilityType.EVOLUTION
            for c in decision.selected_capabilities
        )

    def test_route_synthesis_request(self):
        """Test routing synthesis request uses all capabilities."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        decision = router.route_request(
            RequestType.SYNTHESIS,
            {"full": True},
        )

        assert decision.request_type == RequestType.SYNTHESIS
        # Should select many/all capabilities
        assert len(decision.selected_capabilities) >= 30

    def test_routing_confidence_score(self):
        """Test routing decision has reasonable confidence."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        decision = router.route_request(
            RequestType.QUERY,
            {},
        )

        assert 0.0 <= decision.confidence_score <= 1.0

    def test_routing_performance_estimation(self):
        """Test routing estimates performance."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        decision = router.route_request(
            RequestType.QUERY,
            {},
        )

        assert decision.estimated_latency_ms > 0

    def test_record_usage(self):
        """Test recording usage statistics."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        router.record_usage("F601", success=True, latency_ms=100.0)
        router.record_usage("F601", success=True, latency_ms=95.0)
        router.record_usage("F601", success=False, latency_ms=150.0)

        stats = router.get_routing_stats()
        assert stats["feature_stats"]["F601"]["count"] == 3
        assert stats["feature_stats"]["F601"]["success"] == 2
        assert stats["feature_stats"]["F601"]["failures"] == 1

    def test_routing_history(self):
        """Test routing history is maintained."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        for _ in range(5):
            router.route_request(RequestType.QUERY, {})

        assert len(router.routing_history) == 5


class TestSystemSynthesizer:
    """Test SystemSynthesizer functionality."""

    def test_synthesizer_initialization(self):
        """Test synthesizer initializes."""
        synth = SystemSynthesizer()
        assert synth.registry is not None
        assert synth.router is not None
        assert synth.registry.get_capability_count() >= 45

    def test_get_system_status(self):
        """Test getting system status."""
        synth = SystemSynthesizer()
        status = synth.get_system_status()

        assert "total_capabilities" in status
        assert status["total_capabilities"] >= 45
        assert "capabilities_by_phase" in status
        assert "capabilities_by_type" in status

    def test_get_all_features(self):
        """Test getting all features."""
        synth = SystemSynthesizer()
        features = synth.get_all_features()

        assert len(features) >= 45
        assert "F601" in features  # Phase 1
        assert "F645" in features  # Phase 7

    def test_validate_system(self):
        """Test system validation."""
        synth = SystemSynthesizer()
        validation = synth.validate_system()

        assert validation["is_complete"] is True
        assert validation["total_capabilities"] >= 45
        assert validation["capability_types_covered"] > 0
        assert validation["phases_covered"] > 0

    @pytest.mark.asyncio
    async def test_process_request(self):
        """Test processing a request."""
        synth = SystemSynthesizer()
        result = await synth.process_request(
            RequestType.QUERY,
            {"query": "test"},
        )

        assert result is not None
        assert "success" in result
        assert "latency_ms" in result
        assert "pipeline_results" in result

    def test_optimize_pipeline(self):
        """Test pipeline optimization."""
        synth = SystemSynthesizer()
        all_caps = synth.registry.get_capabilities_by_type(CapabilityType.LEARNING)
        pipeline = all_caps[:3]

        optimization = synth.optimize_pipeline(pipeline)

        assert optimization is not None
        assert optimization.batch_size > 0
        assert optimization.timeout_ms > 0
        assert 1.0 <= optimization.estimated_speedup <= 2.5

    def test_select_capabilities(self):
        """Test capability selection."""
        synth = SystemSynthesizer()

        selected = synth.select_capabilities({
            "capability_types": [CapabilityType.REASONING],
            "min_performance": 0.4,
        })

        assert len(selected) > 0
        assert all(c.capability_type == CapabilityType.REASONING for c in selected)

    def test_estimate_performance(self):
        """Test performance estimation."""
        synth = SystemSynthesizer()
        all_caps = synth.registry.get_capabilities_by_type(CapabilityType.LEARNING)
        pipeline = all_caps[:3]

        estimate = synth.estimate_performance(pipeline)

        assert estimate is not None
        assert estimate.latency_p50_ms > 0
        assert estimate.latency_p99_ms >= estimate.latency_p50_ms
        assert estimate.throughput_rps > 0
        assert 0.0 <= estimate.error_rate <= 1.0
        assert 0.0 <= estimate.confidence_level <= 1.0


class TestPipelineOptimization:
    """Test pipeline optimization."""

    def test_pipeline_optimization_caching(self):
        """Test optimization results are cached."""
        synth = SystemSynthesizer()
        all_caps = synth.registry.get_capabilities_by_type(CapabilityType.LEARNING)
        pipeline = all_caps[:2]

        opt1 = synth.optimize_pipeline(pipeline)
        opt2 = synth.optimize_pipeline(pipeline)

        # Should be same object due to caching
        assert opt1.optimization_id == opt2.optimization_id

    def test_performance_caching(self):
        """Test performance estimates are cached."""
        synth = SystemSynthesizer()
        all_caps = synth.registry.get_capabilities_by_type(CapabilityType.REASONING)
        pipeline = all_caps[:2]

        est1 = synth.estimate_performance(pipeline)
        est2 = synth.estimate_performance(pipeline)

        # Should be same ID due to caching
        assert est1.estimate_id == est2.estimate_id


class TestCapabilityIntegration:
    """Test integration of capabilities."""

    def test_all_capability_types_present(self):
        """Test all capability types are represented."""
        synth = SystemSynthesizer()
        status = synth.get_system_status()

        capability_types = status["capabilities_by_type"]
        assert len(capability_types) >= 5  # Multiple types

    def test_phases_1_through_7_coverage(self):
        """Test all phases 1-7 are covered."""
        synth = SystemSynthesizer()
        features = synth.get_all_features()

        phases = {
            (1, "F601", "F605"),
            (2, "F606", "F610"),
            (3, "F611", "F615"),
            (4, "F616", "F620"),
            (5, "F621", "F625"),
            (6, "F626", "F630"),
            (7, "F631", "F645"),
        }

        for phase_num, start, end in phases:
            start_num = int(start[1:])
            end_num = int(end[1:])
            phase_features = [f for f in features if start_num <= int(f[1:]) <= end_num]
            assert len(phase_features) > 0, f"Phase {phase_num} not covered"

    def test_routing_to_all_capability_types(self):
        """Test router can route to all capability types."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        request_types = [
            (RequestType.QUERY, CapabilityType.REASONING),
            (RequestType.LEARNING, CapabilityType.LEARNING),
            (RequestType.EVOLUTION, CapabilityType.EVOLUTION),
        ]

        for req_type, expected_cap_type in request_types:
            decision = router.route_request(req_type, {})
            assert len(decision.selected_capabilities) > 0
            if req_type != RequestType.SYNTHESIS:
                assert all(
                    c.capability_type == expected_cap_type
                    for c in decision.selected_capabilities
                )


class TestPerformanceMetrics:
    """Test performance metrics and monitoring."""

    def test_capability_performance_scoring(self):
        """Test capability performance scoring."""
        cap = Capability(
            capability_id="test",
            feature_code="F999",
            name="Test",
            phase=FeaturePhase.PHASE1,
            capability_type=CapabilityType.LEARNING,
            module_path="test",
            primary_function="test",
            performance_score=0.75,
        )

        assert 0.0 <= cap.performance_score <= 1.0

    def test_latency_estimation(self):
        """Test latency estimation."""
        synth = SystemSynthesizer()
        registry = synth.registry

        # All capabilities should have reasonable latency
        for cap in registry.get_all_capabilities():
            assert cap.latency_ms >= 0
            assert cap.latency_ms <= 10000  # Reasonable upper bound

    def test_success_rate_tracking(self):
        """Test success rate tracking."""
        registry = CapabilityRegistry()
        router = FeatureRouter(registry)

        # Record series of successes and failures
        for i in range(10):
            success = i % 2 == 0
            router.record_usage("F601", success=success, latency_ms=100.0)

        stats = router.get_routing_stats()
        f601_stats = stats["feature_stats"]["F601"]
        assert f601_stats["count"] == 10
        assert f601_stats["success"] == 5
        assert f601_stats["failures"] == 5
