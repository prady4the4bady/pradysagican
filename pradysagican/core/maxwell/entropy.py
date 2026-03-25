"""
AlignmentEntropyClock — Monotonic drift counter

Feature: F125 — Alignment Entropy Clock

Measures Shannon entropy of the agent's belief distribution.
Tracks whether entropy is increasing (indicating drift/confusion) or stable.
"""

import math
import logging
from typing import Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class AlignmentEntropyClock:
    """
    Monitors alignment entropy (belief distribution stability).
    
    Shannon entropy measures uncertainty:
    - H = -Σ p_i * log(p_i)
    - Low H = confident, stable beliefs
    - High H = uncertain, drifting beliefs
    
    Tracks monotonic increase (monotonic drift counter).
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.entropy_history: deque = deque(maxlen=window_size)
        self.total_measurements = 0
        self.max_entropy_seen = 0.0
        self.entropy_release_log: List[Dict] = []
    
    def measure(self, beliefs: Dict[str, float]) -> float:
        """
        Measure Shannon entropy of current beliefs.
        
        Parameters:
            beliefs: Dictionary of belief values (normalized to [0, 1])
            
        Returns:
            float: Shannon entropy H (0 = complete certainty, log(N) = max uncertainty)
        """
        # Extract belief values and normalize
        values = list(beliefs.values())
        
        if not values:
            return 0.0
        
        # Normalize to probability distribution
        total = sum(abs(v) for v in values)  # Use absolute values
        if total == 0:
            return 0.0
        
        probs = [abs(v) / total for v in values]
        
        # Compute Shannon entropy
        entropy = 0.0
        for p in probs:
            if p > 0:  # Avoid log(0)
                entropy -= p * math.log2(p)
        
        self.entropy_history.append(entropy)
        self.total_measurements += 1
        self.max_entropy_seen = max(self.max_entropy_seen, entropy)
        
        return entropy
    
    def is_drifting(self, threshold: float = 0.5) -> bool:
        """
        Check if entropy is above threshold (indicating drift).
        
        Parameters:
            threshold: Entropy threshold for drift detection
            
        Returns:
            bool: True if current entropy > threshold
        """
        if not self.entropy_history:
            return False
        
        current_entropy = self.entropy_history[-1]
        return current_entropy > threshold
    
    def get_drift_trend(self) -> Optional[str]:
        """
        Analyze entropy trend over recent history.
        
        Returns:
            str: Description of trend ("stable", "drifting", "critical"), or None
        """
        if len(self.entropy_history) < 5:
            return "insufficient_data"
        
        recent = list(self.entropy_history)[-10:]
        mean = sum(recent) / len(recent)
        
        if mean < 0.3:
            return "stable"
        elif mean < 0.6:
            return "drifting"
        else:
            return "critical"
    
    def release(self) -> int:
        """
        Run entropy release protocol (weekly).
        
        Clears old low-priority memory, resets history for fresh measurement.
        This is called on Sunday at midnight (BUS-0 schedule).
        
        Returns:
            int: Number of items pruned
        """
        logger.info("Entropy release: Clearing history and resetting drift counters")
        
        # Store current max entropy for statistics
        pruned_count = len(self.entropy_history) + len(self.entropy_release_log)
        
        # Clear history
        self.entropy_history.clear()
        
        # Log the release event
        self.entropy_release_log.append({
            "event": "entropy_release",
            "max_entropy": self.max_entropy_seen,
            "total_measurements": self.total_measurements,
            "pruned": pruned_count,
        })
        
        # Reset counters
        self.total_measurements = 0
        self.max_entropy_seen = 0.0
        
        logger.info(
            f"Entropy release complete: {pruned_count} items pruned\n"
            f"  Max entropy this cycle: {self.max_entropy_seen:.3f}\n"
            f"  Measurements: {self.total_measurements}"
        )
        
        return pruned_count
    
    def get_statistics(self) -> Dict:
        """
        Get current entropy statistics.
        
        Returns:
            dict: Statistics about entropy measurements
        """
        if not self.entropy_history:
            return {
                "measurements": 0,
                "current": None,
                "mean": None,
                "max": None,
            }
        
        history_list = list(self.entropy_history)
        current = history_list[-1]
        mean = sum(history_list) / len(history_list)
        
        return {
            "measurements": self.total_measurements,
            "current": current,
            "mean": mean,
            "max": max(history_list),
            "min": min(history_list),
            "trend": self.get_drift_trend(),
            "drifting": self.is_drifting(),
        }
    
    def status(self) -> Dict:
        """Get full status."""
        return {
            "current_statistics": self.get_statistics(),
            "history_length": len(self.entropy_history),
            "max_entropy_seen": self.max_entropy_seen,
            "releases_count": len(self.entropy_release_log),
        }
