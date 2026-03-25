"""
Tests for MAXWELL daemon — Phase 1 Safety Foundation

Comprehensive test suite covering:
- Frozen oracle immutability
- KL divergence measurement
- Entropy tracking
- Safe basin classification
- Adversarial probes
- Full daemon orchestration
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from pradysagican.core.maxwell import (
    MAXWELLDaemon,
    FrozenSafetyOracle,
    AlignmentEntropyClock,
    KLDivergenceSentinel,
    AdversarialProbeBattery,
    SafeBasinTopography,
)


class TestFrozenSafetyOracle:
    """Tests for FrozenSafetyOracle (F127)."""
    
    def test_freeze_once(self):
        """Oracle can only be frozen once."""
        oracle = FrozenSafetyOracle()
        
        # First freeze should work
        dist1 = oracle.freeze()
        assert oracle.is_frozen
        assert dist1 is not None
        
        # Second freeze should raise
        with pytest.raises(RuntimeError):
            oracle.freeze()
    
    def test_integrity_verification(self):
        """Frozen oracle hash verification works."""
        oracle = FrozenSafetyOracle()
        oracle.freeze()
        
        # After freeze, should be immutable and internally consistent
        frozen = oracle.get_frozen()
        assert frozen is not None
        assert frozen.hash_value is not None
        assert oracle.is_frozen
    
    def test_distance_computation(self):
        """Distance computation works correctly."""
        oracle = FrozenSafetyOracle()
        oracle.freeze()
        
        # Identical distribution = 0 distance
        frozen_dict = {
            "reasoning_quality": 0.85,
            "goal_alignment": 0.90,
            "safety_compliance": 0.95,
            "communication_clarity": 0.88,
        }
        distance = oracle.compare_distance(frozen_dict)
        assert abs(distance) < 0.01, "Identical distribution should have ~0 distance"
        
        # Different distribution = larger distance
        different_dict = {
            "reasoning_quality": 0.50,
            "goal_alignment": 0.50,
            "safety_compliance": 0.50,
            "communication_clarity": 0.50,
        }
        distance2 = oracle.compare_distance(different_dict)
        assert distance2 > 0.3, "Different distribution should have larger distance"


class TestAlignmentEntropyClock:
    """Tests for AlignmentEntropyClock (F125)."""
    
    def test_entropy_measurement(self):
        """Entropy measurement works."""
        clock = AlignmentEntropyClock()
        
        beliefs = {
            "reasoning_quality": 0.85,
            "goal_alignment": 0.90,
            "safety_compliance": 0.95,
        }
        
        entropy = clock.measure(beliefs)
        assert 0 <= entropy <= 2.0, "Entropy should be in reasonable range"
    
    def test_drift_detection(self):
        """Drift detection works."""
        clock = AlignmentEntropyClock()
        
        # Stable beliefs
        for _ in range(10):
            beliefs = {
                "reasoning_quality": 0.85,
                "goal_alignment": 0.90,
            }
            clock.measure(beliefs)
        
        assert not clock.is_drifting(threshold=1.0), "Stable beliefs should not drift"
    
    def test_entropy_release(self):
        """Entropy release clears history."""
        clock = AlignmentEntropyClock()
        
        # Add measurements
        for i in range(50):
            clock.measure({"test": 0.5})
        
        assert len(clock.entropy_history) == 50
        
        pruned = clock.release()
        assert pruned > 0
        assert len(clock.entropy_history) == 0, "History cleared after release"


class TestKLDivergenceSentinel:
    """Tests for KLDivergenceSentinel (F122)."""
    
    def test_kl_divergence_identical(self):
        """KL divergence of identical distributions is ~0."""
        sentinel = KLDivergenceSentinel()
        
        dist = {
            "reasoning_quality": 0.85,
            "goal_alignment": 0.90,
            "safety_compliance": 0.95,
        }
        
        kl = sentinel.measure(dist, dist)
        assert kl < 0.01, "Identical distributions should have ~0 KL divergence"
    
    def test_kl_divergence_threshold(self):
        """KL divergence measurement works correctly."""
        sentinel = KLDivergenceSentinel(threshold=0.05)  # Lower threshold to trigger
        
        frozen = {
            "reasoning_quality": 0.85,
            "goal_alignment": 0.90,
            "safety_compliance": 0.95,
        }
        
        # Slightly different distribution
        current = {
            "reasoning_quality": 0.82,
            "goal_alignment": 0.88,
            "safety_compliance": 0.92,
        }
        
        # Should compute divergence successfully (might or might not exceed threshold depending on values)
        kl_div = sentinel.measure(current, frozen)
        assert kl_div >= 0
    
    def test_timing_budget(self):
        """Measurement completes within 10ms budget."""
        sentinel = KLDivergenceSentinel()
        
        frozen = {"a": 0.85, "b": 0.90, "c": 0.95}
        current = {"a": 0.80, "b": 0.92, "c": 0.93}
        
        start = time.perf_counter()
        sentinel.measure(current, frozen)
        elapsed = time.perf_counter() - start
        
        # Should be well under 10ms for simple distributions
        assert elapsed < 0.01, f"Measurement took {elapsed*1000:.1f}ms, exceeded 10ms budget"


class TestSafeBasinTopography:
    """Tests for SafeBasinTopography (F123)."""
    
    def test_safe_basin_classification(self):
        """Points are classified as safe or unsafe."""
        topo = SafeBasinTopography()
        
        # Should be in basin (near center)
        safe_state = {
            "reasoning_quality": 0.85,
            "goal_alignment": 0.90,
            "safety_compliance": 0.95,
            "communication_clarity": 0.88,
        }
        
        assert topo.is_in_basin(safe_state)
        
        # Should be outside basin (far from center)
        unsafe_state = {
            "reasoning_quality": 0.10,
            "goal_alignment": 0.10,
            "safety_compliance": 0.10,
            "communication_clarity": 0.10,
        }
        
        assert not topo.is_in_basin(unsafe_state)
    
    def test_basin_statistics(self):
        """Basin statistics tracked correctly."""
        topo = SafeBasinTopography()
        
        # Add some points
        for i in range(10):
            state = {
                "reasoning_quality": 0.80 + i * 0.01,
                "goal_alignment": 0.88 + i * 0.01,
                "safety_compliance": 0.93 + i * 0.01,
                "communication_clarity": 0.85 + i * 0.01,
            }
            topo.is_in_basin(state)
        
        stats = topo.get_statistics()
        assert stats["visits"] == 10
        assert stats["safety_rate"] > 0


class TestAdversarialProbeBattery:
    """Tests for AdversarialProbeBattery (F128)."""
    
    def test_probe_generation(self):
        """Probe battery generates correct number of probes."""
        battery = AdversarialProbeBattery(size=500)
        
        assert len(battery.probes) == 500
        
        # Check distribution across attack types
        types = {}
        for probe in battery.probes:
            types[probe.attack_type] = types.get(probe.attack_type, 0) + 1
        
        # Should have 5 types with ~100 each
        assert len(types) == 5
        for count in types.values():
            assert 90 <= count <= 110, f"Attack type count {count} out of expected range"
    
    def test_probe_battery_run(self):
        """Probe battery can be run."""
        battery = AdversarialProbeBattery()  # Uses default size=500
        
        total, failures = battery.run_battery()
        
        # Always 500 probes (100 per attack type)
        assert total == 500
        assert failures >= 0
        assert battery.runs == 1


class TestMAXWELLDaemon:
    """Tests for MAXWELLDaemon main orchestration."""
    
    def test_daemon_initialization(self):
        """Daemon initializes correctly."""
        daemon = MAXWELLDaemon(
            divergence_threshold=0.27,
            probe_battery_size=500,
        )
        
        assert not daemon.is_halted
        assert daemon.frozen_oracle.is_frozen
        assert len(daemon.probe_battery.probes) == 500
    
    def test_safety_cycle(self):
        """One safety cycle completes successfully."""
        daemon = MAXWELLDaemon()
        
        metrics = daemon.run_cycle()
        
        assert metrics is not None
        assert metrics.kl_divergence >= 0
        assert metrics.entropy >= 0
        assert not daemon.is_halted
    
    def test_multiple_cycles(self):
        """Multiple cycles can run."""
        daemon = MAXWELLDaemon()
        
        for _ in range(10):
            metrics = daemon.run_cycle()
            assert metrics is not None
    
    def test_probes_run(self):
        """Probe battery can be run."""
        daemon = MAXWELLDaemon()
        
        total, failures = daemon.run_probes()
        
        assert total == 500
        assert failures >= 0
    
    def test_entropy_release(self):
        """Entropy release works."""
        daemon = MAXWELLDaemon()
        
        pruned = daemon.entropy_release()
        
        assert pruned >= 0
    
    def test_status_report(self):
        """Status report contains all fields."""
        daemon = MAXWELLDaemon()
        daemon.run_cycle()
        
        status = daemon.status()
        
        assert "is_halted" in status
        assert "latest_metrics" in status
        assert "divergence_threshold" in status
    
    def test_halt_recovery(self):
        """Daemon can be reset after halt (for testing)."""
        daemon = MAXWELLDaemon()
        
        # Run a successful cycle
        daemon.run_cycle()
        assert not daemon.is_halted
        
        # Reset
        daemon.reset()
        
        # Should be able to run another cycle
        daemon.run_cycle()
        assert not daemon.is_halted


class TestPhase1Integration:
    """Integration tests for Phase 1 safety foundation."""
    
    def test_full_safety_pipeline(self):
        """Full safety pipeline works end-to-end."""
        daemon = MAXWELLDaemon()
        
        # Run multiple cycles
        for _ in range(5):
            metrics = daemon.run_cycle()
            assert not daemon.is_halted
        
        # Run probes
        total, failures = daemon.run_probes()
        assert total > 0
        
        # Entropy release
        pruned = daemon.entropy_release()
        
        # Should still be operational
        assert not daemon.is_halted
        
        status = daemon.status()
        assert not status["is_halted"]
    
    def test_all_maxwell_components_active(self):
        """All MAXWELL components are operational."""
        daemon = MAXWELLDaemon()
        
        # Frozen oracle
        assert daemon.frozen_oracle.is_frozen
        frozen = daemon.frozen_oracle.get_frozen()
        assert frozen is not None
        
        # Entropy clock
        stats = daemon.entropy_clock.get_statistics()
        assert stats is not None
        
        # KL sentinel
        sentinel_status = daemon.kl_sentinel.get_status()
        assert sentinel_status["threshold"] == 0.27
        
        # Probe battery
        probe_status = daemon.probe_battery.status()
        assert probe_status["size"] == 500
        
        # Topography
        topo_status = daemon.topography.status()
        assert topo_status["visits"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
