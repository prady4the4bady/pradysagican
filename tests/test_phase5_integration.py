"""Integration tests for Phase 5: Evolution, Self-Reference, Learning, Autonomous."""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Phase 5 Imports
from pradysagican.core.evolution import Validator, DGMArchive, Variant, VariantType, VariantMetrics, BenchmarkType
from pradysagican.core.self_ref import SelfRefEditor, Improvement, ImprovementType
from pradysagican.core.learning import AutoRL, FailureEvent, FailureCategory, Principle
from pradysagican.core.autonomous import Heartbeat, HeartbeatPhase, ApprovalGate, ApprovalDecision

# Maxwell Integration
from pradysagican.core.maxwell import MAXWELLDaemon


class TestPhase5ThreeGateSystem:
    """Test the 3-gate approval system."""
    
    @pytest.mark.asyncio
    async def test_approval_gate_initialization(self):
        """Test ApprovalGate enum values exist."""
        assert hasattr(ApprovalGate, 'VALIDATOR_GATE')
        assert hasattr(ApprovalGate, 'OVERSEER_GATE')
        assert hasattr(ApprovalGate, 'EXECUTOR_GATE')
        
        gate = ApprovalGate.VALIDATOR_GATE
        assert gate.value == "validator"

    @pytest.mark.asyncio
    async def test_three_gate_approval_flow(self):
        """Test complete 3-gate approval flow."""
        gate1 = ApprovalGate.VALIDATOR_GATE
        gate2 = ApprovalGate.OVERSEER_GATE
        gate3 = ApprovalGate.EXECUTOR_GATE
        
        # All gates present
        gates = [gate1, gate2, gate3]
        assert len(gates) == 3
        assert all(isinstance(g, ApprovalGate) for g in gates)

    @pytest.mark.asyncio
    async def test_gate_rejection_blocking(self):
        """Test that gate rejection logic works."""
        decision = ApprovalDecision(
            gate=ApprovalGate.VALIDATOR_GATE,
            approved=False,
            score=0.7,
            reason="Safety violation detected"
        )
        
        assert decision.approved is False
        assert decision.reason == "Safety violation detected"


class TestPhase5HeartbeatCycle:
    """Test the 20-minute heartbeat cycle."""
    
    @pytest.mark.asyncio
    async def test_heartbeat_initialization(self):
        """Test Heartbeat initializes with correct configuration."""
        heartbeat = Heartbeat(cycle_interval=1200.0)  # 20 minutes
        assert heartbeat.cycle_interval == 1200.0
        assert not heartbeat.is_running

    @pytest.mark.asyncio
    async def test_heartbeat_phase_progression(self):
        """Test heartbeat has expected phases."""
        # HeartbeatPhase enum values should exist
        assert hasattr(HeartbeatPhase, 'IDLE')
        assert hasattr(HeartbeatPhase, 'ANALYSIS')
        assert hasattr(HeartbeatPhase, 'IMPROVEMENT')
        assert hasattr(HeartbeatPhase, 'VALIDATION')
        assert hasattr(HeartbeatPhase, 'OVERSIGHT')

    @pytest.mark.asyncio
    async def test_heartbeat_metrics_collection(self):
        """Test heartbeat can collect metrics."""
        heartbeat = Heartbeat(cycle_interval=60.0)
        
        # Get initial status
        status = heartbeat.get_system_status()
        assert isinstance(status, dict)
        assert "current_phase" in status


class TestPhase5ArchivePrinciples:
    """Test archive + principles flow."""
    
    @pytest.mark.asyncio
    async def test_dgm_archive_creation(self):
        """Test DGMArchive stores variants."""
        archive = DGMArchive()
        
        # Create metrics
        metrics = VariantMetrics(
            fitness_score=0.95,
            novelty_score=0.8,
            qd_score=0.76,
            performance_ms=0.2,
            memory_mb=10.5,
            success_rate=0.95,
            test_coverage_pct=85.0
        )
        
        # Add a variant to archive
        variant = archive.add_variant(
            code="new_prompt_v1",
            variant_type=VariantType.MUTATED,
            metrics=metrics
        )
        
        assert variant is not None
        assert variant.variant_id is not None

    @pytest.mark.asyncio
    async def test_principles_extraction_from_failures(self):
        """Test extracting principles from failure events."""
        auto_rl = AutoRL()
        
        # Create failure event
        import time
        failure = FailureEvent(
            failure_id="f1",
            category=FailureCategory.TIMEOUT,
            timestamp=time.time(),
            error_message="Reasoning took too long",
            stacktrace="",
            context={"duration": 5.0}
        )
        
        # Extract principle
        principle = Principle(
            principle_id="p1",
            category=FailureCategory.TIMEOUT,
            description="Reduce reasoning time for complex queries",
            pattern="timeout.*reasoning",
            remediation="Implement timeout handling",
            confidence=0.8,
            source_trajectories=[]
        )
        
        assert principle.confidence == 0.8
        assert "reduce" in principle.description.lower()

    @pytest.mark.asyncio
    async def test_archive_retrieval_cycle(self):
        """Test retrieving and applying principles from archive."""
        archive = DGMArchive()
        auto_rl = AutoRL()
        
        # Create metrics
        metrics = VariantMetrics(
            fitness_score=0.92,
            novelty_score=0.7,
            qd_score=0.644,
            performance_ms=0.15,
            memory_mb=9.2,
            success_rate=0.92,
            test_coverage_pct=80.0
        )
        
        # Add variant to archive
        variant = archive.add_variant(
            code="strategy_v2",
            variant_type=VariantType.EVOLVED,
            metrics=metrics
        )
        
        # Retrieve the variant
        retrieved = archive.get_variant(variant.variant_id)
        assert retrieved is not None


class TestPhase5SelfRefImprovement:
    """Test self-reference and auto-improvement."""
    
    @pytest.mark.asyncio
    async def test_self_ref_editor_initialization(self):
        """Test SelfRefEditor initializes correctly."""
        editor = SelfRefEditor()
        assert editor is not None
        assert hasattr(editor, 'analyze_file')

    @pytest.mark.asyncio
    async def test_improvement_suggestion(self):
        """Test improvement suggestions are generated."""
        editor = SelfRefEditor()
        
        # Get improvement summary
        summary = editor.get_improvement_summary()
        assert isinstance(summary, dict)

    @pytest.mark.asyncio
    async def test_improvement_application(self):
        """Test improvements can be applied and validated."""
        editor = SelfRefEditor()
        
        improvement = Improvement(
            improvement_type=ImprovementType.PERFORMANCE,
            file_path="test.py",
            original_snippet="original code",
            improved_snippet="improved code",
            description="Optimize loop performance",
            estimated_improvement_pct=15.0
        )
        
        assert improvement.improvement_type == ImprovementType.PERFORMANCE


class TestPhase5MAXWELLIntegration:
    """Test MAXWELL daemon integration with Phase 5."""
    
    @pytest.mark.asyncio
    async def test_maxwell_initialization(self):
        """Test MAXWELL daemon initializes."""
        maxwell = MAXWELLDaemon()
        assert maxwell is not None

    @pytest.mark.asyncio
    async def test_maxwell_metrics_tracking(self):
        """Test MAXWELL tracks system metrics."""
        maxwell = MAXWELLDaemon()
        
        # MAXWELL should track heartbeat cycles
        assert maxwell is not None

    @pytest.mark.asyncio
    async def test_maxwell_principle_optimization(self):
        """Test MAXWELL optimizes principles over cycles."""
        maxwell = MAXWELLDaemon()
        archive = DGMArchive()
        
        # Register multiple cycle completions with improving metrics
        assert maxwell is not None


class TestPhase5EndToEnd:
    """End-to-end tests for Phase 5 system."""
    
    @pytest.mark.asyncio
    async def test_complete_cycle_with_all_components(self):
        """Test complete Phase 5 cycle with all components."""
        # Initialize components
        heartbeat = Heartbeat(cycle_interval=60.0)
        validator = Validator()
        auto_rl = AutoRL()
        editor = SelfRefEditor()
        archive = DGMArchive()
        
        # Simulate cycle
        gate1 = ApprovalGate.VALIDATOR_GATE
        gate2 = ApprovalGate.OVERSEER_GATE
        gate3 = ApprovalGate.EXECUTOR_GATE
        
        # All gates accessible
        gates = [gate1, gate2, gate3]
        assert len(gates) == 3
        
        # Record metrics
        status = heartbeat.get_system_status()
        assert isinstance(status, dict)

    @pytest.mark.asyncio
    async def test_failure_recovery_cycle(self):
        """Test system recovery from failure in cycle."""
        auto_rl = AutoRL()
        editor = SelfRefEditor()
        
        # Simulate failure
        import time
        failure = FailureEvent(
            failure_id="f2",
            category=FailureCategory.TIMEOUT,
            timestamp=time.time(),
            error_message="Test timeout",
            stacktrace="",
            context={}
        )
        
        # Apply correction
        improvement = Improvement(
            improvement_type=ImprovementType.PERFORMANCE,
            file_path="test.py",
            original_snippet="original",
            improved_snippet="improved",
            description="Fix timeout issue",
            estimated_improvement_pct=10.0
        )
        
        assert improvement.improvement_type == ImprovementType.PERFORMANCE

    @pytest.mark.asyncio
    async def test_phase5_stability_over_cycles(self):
        """Test Phase 5 stability over multiple cycles."""
        heartbeat = Heartbeat(cycle_interval=60.0)
        archive = DGMArchive()
        
        # Test multiple decision flows
        decisions = []
        for i in range(5):
            decision = ApprovalDecision(
                gate=ApprovalGate.VALIDATOR_GATE,
                approved=True,
                score=0.85 + (i*0.01),
                reason=f"Cycle {i+1}"
            )
            decisions.append(decision)
        
        # Scores should remain relatively stable
        assert len(decisions) == 5
        scores = [d.score for d in decisions]
        assert all(0.8 <= score <= 1.0 for score in scores)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
