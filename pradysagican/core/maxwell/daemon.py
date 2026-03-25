"""
MAXWELLDaemon — Main safety orchestration

Runs at 100Hz during BUS-0 (Survival Bus) execution.
Continuously monitors belief drift and can halt execution immediately if unsafe.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from .oracle import FrozenSafetyOracle
from .entropy import AlignmentEntropyClock
from .sentinel import KLDivergenceSentinel
from .probes import AdversarialProbeBattery
from .topography import SafeBasinTopography

logger = logging.getLogger(__name__)


@dataclass
class SafetyMetrics:
    """Current safety state metrics."""
    timestamp: float
    kl_divergence: float
    entropy: float
    probe_failures: int
    in_safe_basin: bool
    last_halt_reason: Optional[str] = None
    consecutive_safe_cycles: int = 0


class MAXWELLDaemon:
    """
    Main safety daemon.
    
    Runs continuously on BUS-0 (100Hz). Monitors all safety metrics and can:
    1. Detect belief drift via KL divergence sentinel
    2. Track alignment entropy (monotonic drift counter)
    3. Run adversarial probe battery nightly
    4. Map safety basin topography
    5. Halt execution immediately if D* > divergence_threshold
    
    Parameters:
        divergence_threshold: D* limit for safety halt (default: 0.27)
        cooling_schedule_T0: Initial temperature for thermodynamic cooling
        probe_battery_size: Number of adversarial probes (default: 500)
        entropy_release_day: Day of week for entropy release (default: "sunday")
        entropy_release_hour: Hour of day for entropy release (default: 0)
    """
    
    def __init__(
        self,
        divergence_threshold: float = 0.27,
        cooling_schedule_T0: float = 1.0,
        probe_battery_size: int = 500,
        entropy_release_day: str = "sunday",
        entropy_release_hour: int = 0,
    ):
        self.divergence_threshold = divergence_threshold
        self.cooling_schedule_T0 = cooling_schedule_T0
        self.probe_battery_size = probe_battery_size
        self.entropy_release_day = entropy_release_day
        self.entropy_release_hour = entropy_release_hour
        
        # Core safety components
        self.frozen_oracle = FrozenSafetyOracle()
        self.entropy_clock = AlignmentEntropyClock()
        self.kl_sentinel = KLDivergenceSentinel(threshold=divergence_threshold)
        self.probe_battery = AdversarialProbeBattery(size=probe_battery_size)
        self.topography = SafeBasinTopography()
        
        # State tracking
        self.metrics_history: List[SafetyMetrics] = []
        self.halt_count = 0
        self.is_halted = False
        self.halt_reason: Optional[str] = None
        
        # Initialize frozen oracle snapshot
        self.frozen_oracle.freeze()
        logger.info(f"MAXWELLDaemon initialized with D* threshold={divergence_threshold}")
    
    def run_cycle(self) -> SafetyMetrics:
        """
        Run one 100Hz safety cycle.
        
        Returns:
            SafetyMetrics: Current safety state
            
        Raises:
            RuntimeError: If safety halt triggered
        """
        if self.is_halted:
            raise RuntimeError(f"Safety halt active: {self.halt_reason}")
        
        start_time = time.time()
        
        # Measure current beliefs/state
        current_beliefs = self._get_current_beliefs()
        
        # Check KL divergence (convert frozen distribution to dict)
        frozen_dict = {
            "reasoning_quality": self.frozen_oracle.frozen_distribution.reasoning_quality,
            "goal_alignment": self.frozen_oracle.frozen_distribution.goal_alignment,
            "safety_compliance": self.frozen_oracle.frozen_distribution.safety_compliance,
            "communication_clarity": self.frozen_oracle.frozen_distribution.communication_clarity,
        }
        
        kl_div = self.kl_sentinel.measure(
            current=current_beliefs,
            frozen=frozen_dict
        )
        
        # Update entropy clock
        entropy = self.entropy_clock.measure(current_beliefs)
        
        # Check safe basin
        in_basin = self.topography.is_in_basin(current_beliefs)
        
        # Run probe battery (sparse — only nightly or on-demand)
        probe_failures = 0  # Updated by run_probes() separately
        
        # Create metrics snapshot
        metrics = SafetyMetrics(
            timestamp=start_time,
            kl_divergence=kl_div,
            entropy=entropy,
            probe_failures=probe_failures,
            in_safe_basin=in_basin,
        )
        
        self.metrics_history.append(metrics)
        
        # Check halt condition
        if kl_div > self.divergence_threshold:
            self._trigger_halt(f"KL divergence {kl_div:.3f} > threshold {self.divergence_threshold}")
            raise RuntimeError(f"Safety halt: KL divergence exceeded")
        
        if not in_basin:
            self._trigger_halt(f"Beliefs outside safe basin")
            raise RuntimeError(f"Safety halt: Outside safe basin")
        
        # Check execution time (should be <10ms for 100Hz)
        elapsed = time.time() - start_time
        if elapsed > 0.01:
            logger.warning(f"MAXWELL cycle exceeded 10ms budget: {elapsed*1000:.1f}ms")
        
        return metrics
    
    def run_probes(self) -> Tuple[int, int]:
        """
        Run adversarial probe battery (expensive — typically nightly).
        
        Returns:
            (total_probes, failures): Number of probes and number that failed
        """
        logger.info(f"Running {self.probe_battery_size} adversarial probes...")
        
        total, failures = self.probe_battery.run_battery()
        
        if failures > 0:
            logger.error(f"Probes failed: {failures}/{total}")
            self._trigger_halt(f"Adversarial probes failed: {failures}/{total}")
        else:
            logger.info(f"All {total} probes passed")
        
        return total, failures
    
    def entropy_release(self) -> int:
        """
        Run entropy release protocol (weekly, typically Sunday midnight).
        Prunes low-value memories and resets divergence counters.
        
        Returns:
            int: Number of items pruned
        """
        logger.info("Entropy release: Pruning low-value memories...")
        
        pruned = self.entropy_clock.release()
        logger.info(f"Entropy release complete: {pruned} items pruned")
        
        return pruned
    
    def detect_drift(self) -> Optional[str]:
        """
        Analyze recent history for drift patterns.
        
        Returns:
            str: Description of drift if detected, None if stable
        """
        if len(self.metrics_history) < 10:
            return None
        
        recent = self.metrics_history[-10:]
        kl_trend = [m.kl_divergence for m in recent]
        
        # Simple linear trend: is KL increasing?
        if kl_trend[-1] > kl_trend[0]:
            slope = (kl_trend[-1] - kl_trend[0]) / len(kl_trend)
            if slope > 0.01:  # Significant drift
                return f"KL divergence trending up (slope={slope:.4f})"
        
        return None
    
    def status(self) -> Dict:
        """
        Get current daemon status.
        
        Returns:
            dict: Status snapshot
        """
        if not self.metrics_history:
            return {"status": "initializing"}
        
        latest = self.metrics_history[-1]
        
        return {
            "is_halted": self.is_halted,
            "halt_reason": self.halt_reason,
            "halt_count": self.halt_count,
            "latest_metrics": {
                "timestamp": latest.timestamp,
                "kl_divergence": latest.kl_divergence,
                "entropy": latest.entropy,
                "probe_failures": latest.probe_failures,
                "in_safe_basin": latest.in_safe_basin,
            },
            "drift_detected": self.detect_drift(),
            "divergence_threshold": self.divergence_threshold,
            "consecutive_safe_cycles": latest.consecutive_safe_cycles,
        }
    
    def _get_current_beliefs(self) -> Dict[str, float]:
        """
        Get current belief state from agent.
        
        Returns:
            dict: Current beliefs (placeholder — actual implementation
                  would query the full agent state)
        """
        # Placeholder: in real implementation, query agent's belief state
        # For now, return a normalized distribution
        return {
            "reasoning_quality": 0.85,
            "goal_alignment": 0.90,
            "safety_compliance": 0.95,
            "communication_clarity": 0.88,
        }
    
    def _trigger_halt(self, reason: str) -> None:
        """Trigger safety halt."""
        self.is_halted = True
        self.halt_reason = reason
        self.halt_count += 1
        logger.critical(f"MAXWELL HALT #{self.halt_count}: {reason}")
    
    def reset(self) -> None:
        """Reset daemon (for testing or recovery)."""
        self.is_halted = False
        self.halt_reason = None
        self.metrics_history.clear()
        logger.info("MAXWELLDaemon reset")
