"""
KLDivergenceSentinel — Real-time divergence monitor

Feature: F122 — KL Divergence Sentinel

Measures KL(current || frozen) in real-time (< 10ms).
Triggers alarm if D > threshold (default 0.27).

KL divergence: D(P||Q) = Σ P(x) * log(P(x) / Q(x))
"""

import math
import logging
from typing import Dict, Optional
import time

logger = logging.getLogger(__name__)


class KLDivergenceSentinel:
    """
    Real-time KL divergence monitor.
    
    Parameters:
        threshold: Divergence threshold for alarm (D* default = 0.27)
        warning_threshold: Lower threshold for warnings
    """
    
    def __init__(self, threshold: float = 0.27, warning_threshold: float = 0.15):
        self.threshold = threshold
        self.warning_threshold = warning_threshold
        self.last_measurement = 0.0
        self.last_measurement_time = None
        self.measurements_count = 0
        self.alarms_triggered = 0
        self.timing_violations = 0  # Count of >10ms measurements
    
    def measure(
        self,
        current: Dict[str, float],
        frozen: Dict[str, float],
    ) -> float:
        """
        Measure KL divergence from current to frozen distribution.
        
        Must complete in < 10ms for BUS-0 100Hz operation.
        
        Parameters:
            current: Current belief distribution (P)
            frozen: Frozen baseline distribution (Q)
            
        Returns:
            float: KL divergence D(P||Q)
            
        Raises:
            RuntimeError: If threshold exceeded
        """
        start_time = time.perf_counter()
        
        # Normalize to probability distributions
        current_probs = self._normalize(current)
        frozen_probs = self._normalize(frozen)
        
        # Compute KL divergence: Σ P(x) * log(P(x) / Q(x))
        kl_div = 0.0
        
        for key in current_probs:
            p = current_probs.get(key, 1e-10)
            q = frozen_probs.get(key, 1e-10)
            
            if p > 0:
                kl_div += p * math.log(p / q)
        
        # Also check for keys in frozen but not in current
        for key in frozen_probs:
            if key not in current_probs:
                q = frozen_probs[key]
                if q > 0:
                    kl_div += q * math.log(q / 1e-10)  # Missing current = extreme divergence
        
        self.last_measurement = kl_div
        self.measurements_count += 1
        
        # Check timing budget
        elapsed = time.perf_counter() - start_time
        self.last_measurement_time = elapsed
        
        if elapsed > 0.01:  # 10ms budget
            self.timing_violations += 1
            logger.warning(f"KLDivergenceSentinel exceeded 10ms budget: {elapsed*1000:.1f}ms")
        
        # Check alarm condition
        if kl_div > self.threshold:
            self.alarms_triggered += 1
            logger.critical(f"KL DIVERGENCE ALARM: D={kl_div:.4f} > {self.threshold}")
            raise RuntimeError(f"KL divergence exceeded threshold: {kl_div:.4f} > {self.threshold}")
        
        # Check warning condition
        if kl_div > self.warning_threshold:
            logger.warning(f"KL divergence warning: D={kl_div:.4f} (threshold={self.threshold})")
        
        return kl_div
    
    def _normalize(self, distribution: Dict[str, float]) -> Dict[str, float]:
        """Normalize distribution to probabilities."""
        values = list(distribution.values())
        
        if not values:
            return {}
        
        # Use absolute values
        total = sum(abs(v) for v in values)
        
        if total == 0:
            # Uniform distribution
            return {k: 1.0 / len(distribution) for k in distribution}
        
        return {k: abs(v) / total for k, v in distribution.items()}
    
    def get_status(self) -> Dict:
        """Get sentinel status."""
        return {
            "last_measurement": self.last_measurement,
            "last_measurement_time_ms": (self.last_measurement_time * 1000) if self.last_measurement_time else None,
            "measurements_count": self.measurements_count,
            "alarms_triggered": self.alarms_triggered,
            "timing_violations": self.timing_violations,
            "threshold": self.threshold,
            "warning_threshold": self.warning_threshold,
        }
    
    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.measurements_count = 0
        self.alarms_triggered = 0
        self.timing_violations = 0
