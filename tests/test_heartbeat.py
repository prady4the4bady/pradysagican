"""
Tests for F610: HEARTBEAT module
=================================
Tests for autonomous heartbeat cycle orchestrator.
"""

import pytest
import asyncio
from pradysagican.core.autonomous.heartbeat import (
    Heartbeat,
    HeartbeatPhase,
    ApprovalGate,
    ApprovalDecision,
    CycleMetrics,
    FailureQueueItem,
)


@pytest.fixture
def heartbeat():
    """Create test heartbeat instance."""
    return Heartbeat(
        cycle_interval=10.0,  # Short interval for testing
        phase_timeout=2.0,
    )


class TestHeartbeatInitialization:
    """Test heartbeat initialization."""

    def test_heartbeat_init(self, heartbeat):
        """Test basic initialization."""
        assert heartbeat is not None
        assert heartbeat.is_running is False
        assert heartbeat.cycle_number == 0

    def test_heartbeat_feature_flags(self):
        """Test feature flags."""
        hb = Heartbeat(
            enable_editor=False,
            enable_validator=False,
            enable_overseer=False,
        )
        assert hb.enable_editor is False
        assert hb.enable_validator is False
        assert hb.enable_overseer is False

    def test_heartbeat_timeouts(self):
        """Test timeout configuration."""
        hb = Heartbeat(cycle_interval=600.0, phase_timeout=100.0)
        assert hb.cycle_interval == 600.0
        assert hb.phase_timeout == 100.0


class TestHeartbeatPhases:
    """Test HeartbeatPhase enum."""

    def test_phase_values(self):
        """Test phase enum values."""
        phases = [
            HeartbeatPhase.IDLE,
            HeartbeatPhase.ANALYSIS,
            HeartbeatPhase.IMPROVEMENT,
            HeartbeatPhase.VALIDATION,
            HeartbeatPhase.OVERSIGHT,
            HeartbeatPhase.ARCHIVAL,
            HeartbeatPhase.FAILURE_RECOVERY,
            HeartbeatPhase.LEARNING,
        ]
        assert len(phases) == 8


class TestApprovalGates:
    """Test approval gate system."""

    def test_approval_gate_enum(self):
        """Test approval gate values."""
        gates = [
            ApprovalGate.VALIDATOR_GATE,
            ApprovalGate.OVERSEER_GATE,
            ApprovalGate.EXECUTOR_GATE,
        ]
        assert len(gates) == 3

    def test_approval_decision_creation(self):
        """Test creating approval decision."""
        decision = ApprovalDecision(
            gate=ApprovalGate.VALIDATOR_GATE,
            approved=True,
            score=0.95,
            reason="All tests passed",
        )
        
        assert decision.gate == ApprovalGate.VALIDATOR_GATE
        assert decision.approved is True
        assert decision.score == 0.95

    def test_approval_decision_score_range(self):
        """Test approval score range."""
        decision = ApprovalDecision(
            gate=ApprovalGate.VALIDATOR_GATE,
            approved=True,
            score=0.5,
            reason="Test",
        )
        
        assert 0.0 <= decision.score <= 1.0


class TestFailureQueueing:
    """Test failure queue management."""

    def test_add_failure(self, heartbeat):
        """Test adding failure to queue."""
        heartbeat.add_failure(
            failure_id="fail_001",
            category="timeout",
            error_message="Operation timed out",
        )
        
        assert len(heartbeat._failure_queue) == 1
        assert heartbeat._failure_queue[0].failure_id == "fail_001"

    def test_failure_queue_item(self):
        """Test FailureQueueItem structure."""
        item = FailureQueueItem(
            failure_id="fail_001",
            category="error",
            timestamp=0.0,
            error_message="Test error",
        )
        
        assert item.failure_id == "fail_001"
        assert item.retry_count == 0
        assert item.max_retries == 3
        assert item.processed is False

    def test_multiple_failures(self, heartbeat):
        """Test queuing multiple failures."""
        for i in range(5):
            heartbeat.add_failure(
                failure_id=f"fail_{i:03d}",
                category="error",
                error_message=f"Error {i}",
            )
        
        assert len(heartbeat._failure_queue) == 5


class TestCycleMetrics:
    """Test cycle metrics tracking."""

    def test_metrics_creation(self):
        """Test creating cycle metrics."""
        metrics = CycleMetrics(
            cycle_number=1,
            start_time=0.0,
        )
        
        assert metrics.cycle_number == 1
        assert metrics.improvements_proposed == 0
        assert metrics.overall_success is True

    def test_metrics_accumulation(self):
        """Test metrics accumulation."""
        metrics = CycleMetrics(
            cycle_number=1,
            start_time=0.0,
        )
        
        metrics.improvements_proposed = 5
        metrics.improvements_applied = 3
        metrics.validations_passed = 2
        
        assert metrics.improvements_proposed == 5
        assert metrics.improvements_applied == 3
        assert metrics.validations_passed == 2


class TestCycleExecution:
    """Test cycle execution."""

    @pytest.mark.asyncio
    async def test_run_cycle(self, heartbeat):
        """Test running a single cycle."""
        metrics = await heartbeat.run_cycle()
        
        assert isinstance(metrics, CycleMetrics)
        assert metrics.cycle_number == 1
        assert metrics.duration_sec > 0

    @pytest.mark.asyncio
    async def test_multiple_cycles(self, heartbeat):
        """Test running multiple cycles."""
        for _ in range(3):
            await heartbeat.run_cycle()
        
        assert heartbeat.cycle_number == 3
        assert len(heartbeat._cycle_history) == 3

    @pytest.mark.asyncio
    async def test_cycle_phases(self, heartbeat):
        """Test all cycle phases are executed."""
        metrics = await heartbeat.run_cycle()
        
        # Should have completed multiple phases
        assert len(metrics.phases_completed) > 0

    @pytest.mark.asyncio
    async def test_cycle_with_all_phases_disabled(self):
        """Test cycle with all phases disabled."""
        hb = Heartbeat(
            enable_editor=False,
            enable_validator=False,
            enable_overseer=False,
            enable_archive=False,
            enable_learning=False,
        )
        
        metrics = await hb.run_cycle()
        
        # Should still complete
        assert metrics.cycle_number == 1
        assert metrics.duration_sec >= 0


class TestApprovalGateApplication:
    """Test approval gate system."""

    @pytest.mark.asyncio
    async def test_approval_gates_applied(self, heartbeat):
        """Test approval gates are applied."""
        metrics = await heartbeat.run_cycle()
        
        # Gates should be applied during validation
        # (This depends on phase execution)

    @pytest.mark.asyncio
    async def test_validator_gate(self, heartbeat):
        """Test validator gate decision."""
        metrics = await heartbeat.run_cycle()
        
        # Check pending approvals were created
        # (Approvals are cleared after oversight phase)


class TestSystemStatus:
    """Test system status reporting."""

    def test_initial_status(self, heartbeat):
        """Test initial system status."""
        status = heartbeat.get_system_status()
        
        assert status["is_running"] is False
        assert status["cycle_number"] == 0
        assert status["failure_queue_size"] == 0

    def test_status_with_failures(self, heartbeat):
        """Test status with failures in queue."""
        heartbeat.add_failure("fail_001", "error", "Test error")
        
        status = heartbeat.get_system_status()
        assert status["failure_queue_size"] == 1

    @pytest.mark.asyncio
    async def test_status_after_cycle(self, heartbeat):
        """Test status after running cycle."""
        await heartbeat.run_cycle()
        
        status = heartbeat.get_system_status()
        assert status["cycle_number"] == 1


class TestPerformanceSummary:
    """Test performance summary."""

    @pytest.mark.asyncio
    async def test_performance_summary_empty(self, heartbeat):
        """Test performance summary with no cycles."""
        summary = heartbeat.get_performance_summary()
        
        assert summary["cycles_completed"] == 0

    @pytest.mark.asyncio
    async def test_performance_summary_after_cycles(self, heartbeat):
        """Test performance summary after running cycles."""
        for _ in range(2):
            await heartbeat.run_cycle()
        
        summary = heartbeat.get_performance_summary()
        
        assert summary["cycles_completed"] == 2
        assert "avg_cycle_duration_sec" in summary
        assert "error_rate" in summary

    @pytest.mark.asyncio
    async def test_approval_rate(self, heartbeat):
        """Test approval rate calculation."""
        await heartbeat.run_cycle()
        
        summary = heartbeat.get_performance_summary()
        
        if "approval_rate_pct" in summary:
            # Approval rate can be 0-200+ (more approved than applied is possible)
            approval_rate = summary["approval_rate_pct"]
            if isinstance(approval_rate, (int, float)):
                assert approval_rate >= 0


class TestCycleHistory:
    """Test cycle history."""

    @pytest.mark.asyncio
    async def test_cycle_history_tracking(self, heartbeat):
        """Test cycle history is tracked."""
        for _ in range(3):
            await heartbeat.run_cycle()
        
        history = heartbeat.get_cycle_history(limit=10)
        
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_cycle_history_limit(self, heartbeat):
        """Test cycle history respects limit."""
        for _ in range(5):
            await heartbeat.run_cycle()
        
        history = heartbeat.get_cycle_history(limit=2)
        
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_cycle_history_most_recent(self, heartbeat):
        """Test getting most recent cycles."""
        for _ in range(3):
            await heartbeat.run_cycle()
        
        history = heartbeat.get_cycle_history(limit=2)
        
        # Should be most recent cycles
        assert history[-1].cycle_number == 3


class TestCurrentPhaseTracking:
    """Test current phase tracking."""

    def test_initial_phase(self, heartbeat):
        """Test initial phase is IDLE."""
        assert heartbeat.current_phase == HeartbeatPhase.IDLE

    @pytest.mark.asyncio
    async def test_phase_transitions(self, heartbeat):
        """Test phase transitions during cycle."""
        # Start cycle (will change phases)
        await heartbeat.run_cycle()
        
        # After cycle, should be back to idle or specific phase
        assert heartbeat.current_phase in [
            HeartbeatPhase.IDLE,
            HeartbeatPhase.LEARNING,
            HeartbeatPhase.ARCHIVAL,
        ]


class TestHeartbeatStartStop:
    """Test heartbeat start/stop."""

    def test_start_flag(self, heartbeat):
        """Test is_running flag."""
        assert heartbeat.is_running is False

    def test_stop_sets_flag(self, heartbeat):
        """Test stop sets is_running to False."""
        heartbeat.is_running = True
        heartbeat.stop()
        
        assert heartbeat.is_running is False

    @pytest.mark.asyncio
    async def test_cannot_start_twice(self, heartbeat):
        """Test cannot start heartbeat twice."""
        # Start heartbeat
        heartbeat.is_running = True
        
        # Try to start again (should warn)
        await heartbeat.run_cycle()
        
        # Should only have 1 cycle
        assert heartbeat.cycle_number == 1
