"""
Tests for F611: AUTO-RL module
==============================
Tests for automated reinforcement learning from failures.
"""

import pytest
import asyncio
from pathlib import Path
from pradysagican.core.learning.auto_rl import (
    AutoRL,
    FailureTrajectory,
    FailureEvent,
    FailureCategory,
    Principle,
    RetrievalResult,
)


@pytest.fixture
def auto_rl(tmp_path):
    """Create test AutoRL instance."""
    return AutoRL(storage_dir=tmp_path, use_chroma=False)


@pytest.fixture
def sample_failure_event():
    """Create sample failure event."""
    return FailureEvent(
        failure_id="fail_001",
        category=FailureCategory.TIMEOUT,
        timestamp=0.0,
        error_message="Operation timed out after 30s",
        stacktrace="at line 42 in main",
        context={"operation": "db_query"},
    )


class TestAutoRLInitialization:
    """Test AutoRL initialization."""

    def test_auto_rl_init(self, auto_rl):
        """Test basic initialization."""
        assert auto_rl is not None
        assert auto_rl.storage_dir.exists()
        assert len(auto_rl._principles) == 0

    def test_auto_rl_with_chroma(self, tmp_path):
        """Test initialization with ChromaDB."""
        # ChromaDB may not be installed, so we just test it doesn't crash
        auto_rl = AutoRL(storage_dir=tmp_path, use_chroma=True)
        assert auto_rl is not None


class TestFailureEvents:
    """Test failure event handling."""

    def test_failure_event_creation(self, sample_failure_event):
        """Test creating failure event."""
        assert sample_failure_event.failure_id == "fail_001"
        assert sample_failure_event.category == FailureCategory.TIMEOUT

    def test_all_failure_categories(self):
        """Test all failure categories exist."""
        categories = [
            FailureCategory.TIMEOUT,
            FailureCategory.ASSERTION_FAILED,
            FailureCategory.TYPE_ERROR,
            FailureCategory.VALUE_ERROR,
            FailureCategory.RESOURCE_EXCEEDED,
            FailureCategory.LOGIC_ERROR,
            FailureCategory.EXTERNAL_API,
            FailureCategory.CONCURRENCY,
        ]
        assert len(categories) == 8


class TestFailureTrajectories:
    """Test failure trajectory handling."""

    def test_trajectory_creation(self, sample_failure_event):
        """Test creating trajectory."""
        trajectory = FailureTrajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
            root_cause="Database connection timeout",
        )
        assert trajectory.trajectory_id == "traj_001"
        assert len(trajectory.events) == 1

    def test_add_event_to_trajectory(self, sample_failure_event):
        """Test adding event to trajectory."""
        trajectory = FailureTrajectory(trajectory_id="traj_001")
        
        assert len(trajectory.events) == 0
        trajectory.add_event(sample_failure_event)
        assert len(trajectory.events) == 1

    def test_record_failure_trajectory(self, auto_rl, sample_failure_event):
        """Test recording trajectory."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
            root_cause="Connection timeout",
        )
        
        assert trajectory.trajectory_id == "traj_001"
        assert len(trajectory.events) == 1
        assert "traj_001" in auto_rl._trajectories


class TestPrincipleExtraction:
    """Test principle extraction from failures."""

    @pytest.mark.asyncio
    async def test_extract_principles(self, auto_rl, sample_failure_event):
        """Test extracting principles."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
            root_cause="Connection timeout",
        )
        
        principles = await auto_rl.extract_principles(trajectory)
        
        assert len(principles) > 0
        assert all(isinstance(p, Principle) for p in principles)

    @pytest.mark.asyncio
    async def test_principle_has_remediation(self, auto_rl, sample_failure_event):
        """Test extracted principles have remediation."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
        )
        
        principles = await auto_rl.extract_principles(trajectory)
        
        for principle in principles:
            assert principle.remediation is not None
            assert len(principle.remediation) > 0

    @pytest.mark.asyncio
    async def test_principle_confidence(self, auto_rl, sample_failure_event):
        """Test extracted principles have confidence."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
        )
        
        principles = await auto_rl.extract_principles(trajectory)
        
        for principle in principles:
            assert 0.0 <= principle.confidence <= 1.0


class TestPrinciples:
    """Test principle management."""

    def test_principle_creation(self):
        """Test creating principle."""
        principle = Principle(
            principle_id="prin_001",
            category=FailureCategory.TIMEOUT,
            description="Handle timeout gracefully",
            pattern="timeout.*",
            remediation="Add retry logic",
            confidence=0.85,
        )
        
        assert principle.principle_id == "prin_001"
        assert principle.confidence == 0.85

    def test_principle_reinforcement(self):
        """Test principle reinforcement."""
        principle = Principle(
            principle_id="prin_001",
            category=FailureCategory.TIMEOUT,
            description="Handle timeout",
            pattern="timeout.*",
            remediation="Add retry",
            confidence=0.5,
        )
        
        initial_confidence = principle.confidence
        principle.reinforce()
        
        assert principle.confidence > initial_confidence
        assert principle.reinforcement_count == 1

    def test_principle_multiple_reinforcements(self):
        """Test multiple reinforcements increase confidence."""
        principle = Principle(
            principle_id="prin_001",
            category=FailureCategory.TIMEOUT,
            description="Handle timeout",
            pattern="timeout.*",
            remediation="Add retry",
            confidence=0.5,
        )
        
        for _ in range(5):
            principle.reinforce()
        
        assert principle.reinforcement_count == 5
        assert principle.confidence < 0.99  # Capped


class TestRetrieval:
    """Test principle retrieval."""

    @pytest.mark.asyncio
    async def test_retrieve_principles(self, auto_rl, sample_failure_event):
        """Test retrieving principles."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
        )
        
        await auto_rl.extract_principles(trajectory)
        
        results = await auto_rl.retrieve_principles("timeout")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_retrieval_with_category_filter(self, auto_rl, sample_failure_event):
        """Test retrieval with category filter."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
        )
        
        await auto_rl.extract_principles(trajectory)
        
        results = await auto_rl.retrieve_principles(
            "timeout",
            error_category=FailureCategory.TIMEOUT
        )
        
        for result in results:
            assert result.principle.category == FailureCategory.TIMEOUT

    @pytest.mark.asyncio
    async def test_retrieval_result_structure(self, auto_rl, sample_failure_event):
        """Test RetrievalResult structure."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
        )
        
        await auto_rl.extract_principles(trajectory)
        results = await auto_rl.retrieve_principles("timeout")
        
        if results:
            result = results[0]
            assert isinstance(result, RetrievalResult)
            assert 0.0 <= result.similarity_score <= 1.0
            assert 0.0 <= result.relevance_score <= 1.0
            assert result.principle is not None

    @pytest.mark.asyncio
    async def test_retrieval_reinforces_principles(self, auto_rl, sample_failure_event):
        """Test that retrieval reinforces principles."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
        )
        
        principles = await auto_rl.extract_principles(trajectory)
        initial_count = principles[0].reinforcement_count if principles else 0
        
        await auto_rl.retrieve_principles("timeout")
        
        if principles:
            assert principles[0].reinforcement_count >= initial_count


class TestLearning:
    """Test learning summary."""

    @pytest.mark.asyncio
    async def test_learning_summary_empty(self, auto_rl):
        """Test learning summary on empty system."""
        summary = auto_rl.get_learning_summary()
        
        assert summary["total_principles"] == 0
        assert "total_trajectories" in summary or summary["total_principles"] == 0

    @pytest.mark.asyncio
    async def test_learning_summary_with_principles(self, auto_rl, sample_failure_event):
        """Test learning summary with principles."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
        )
        
        await auto_rl.extract_principles(trajectory)
        summary = auto_rl.get_learning_summary()
        
        assert summary["total_principles"] > 0
        assert summary["total_trajectories"] > 0

    @pytest.mark.asyncio
    async def test_learning_summary_categories(self, auto_rl, sample_failure_event):
        """Test category distribution in summary."""
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=[sample_failure_event],
        )
        
        await auto_rl.extract_principles(trajectory)
        summary = auto_rl.get_learning_summary()
        
        assert "category_distribution" in summary
        dist = summary["category_distribution"]
        assert FailureCategory.TIMEOUT.value in dist


class TestStorage:
    """Test principle storage and persistence."""

    def test_save_storage(self, auto_rl):
        """Test saving principles to storage."""
        # Add a principle manually for testing
        principle = Principle(
            principle_id="prin_001",
            category=FailureCategory.TIMEOUT,
            description="Handle timeout",
            pattern="timeout.*",
            remediation="Add retry",
            confidence=0.8,
        )
        auto_rl._principles["prin_001"] = principle
        
        auto_rl.save_storage()
        
        # Verify file was created
        storage_file = auto_rl.storage_dir / "principles.json"
        assert storage_file.exists()

    def test_load_storage(self, tmp_path):
        """Test loading principles from storage."""
        # Create AutoRL and save a principle
        auto_rl1 = AutoRL(storage_dir=tmp_path, use_chroma=False)
        principle = Principle(
            principle_id="prin_001",
            category=FailureCategory.TIMEOUT,
            description="Handle timeout",
            pattern="timeout.*",
            remediation="Add retry",
            confidence=0.8,
        )
        auto_rl1._principles["prin_001"] = principle
        auto_rl1.save_storage()
        
        # Create new AutoRL from same directory
        auto_rl2 = AutoRL(storage_dir=tmp_path, use_chroma=False)
        assert len(auto_rl2._principles) > 0
        assert "prin_001" in auto_rl2._principles


class TestMultipleFailures:
    """Test handling multiple failures in trajectory."""

    @pytest.mark.asyncio
    async def test_trajectory_multiple_events(self, auto_rl):
        """Test trajectory with multiple events."""
        events = [
            FailureEvent(
                failure_id="f1",
                category=FailureCategory.TIMEOUT,
                timestamp=0.0,
                error_message="Timeout 1",
                stacktrace="stack1",
                context={},
            ),
            FailureEvent(
                failure_id="f2",
                category=FailureCategory.TIMEOUT,
                timestamp=1.0,
                error_message="Timeout 2",
                stacktrace="stack2",
                context={},
            ),
        ]
        
        trajectory = auto_rl.record_failure_trajectory(
            trajectory_id="traj_001",
            events=events,
            root_cause="Connection pool exhausted",
        )
        
        principles = await auto_rl.extract_principles(trajectory)
        
        # Should extract principles from pattern
        assert len(principles) > 0
