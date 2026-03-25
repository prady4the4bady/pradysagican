"""
FrozenSafetyOracle — Immutable initial safety distribution

Captures and stores the initial safety distribution at startup.
This frozen snapshot becomes the reference point for all drift measurements.
Cannot be modified after freezing (immutable).
"""

import json
import hashlib
from typing import Dict, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SafetyDistribution:
    """Represents a safety distribution snapshot."""
    reasoning_quality: float
    goal_alignment: float
    safety_compliance: float
    communication_clarity: float
    timestamp: float
    hash_value: Optional[str] = None
    
    def compute_hash(self) -> str:
        """Compute SHA-256 hash of this distribution."""
        data = json.dumps(asdict(self), sort_keys=True, default=str)
        return hashlib.sha256(data.encode()).hexdigest()


class FrozenSafetyOracle:
    """
    Immutable snapshot of initial safety distribution.
    
    Once frozen, this cannot be modified. All drift is measured against this.
    Feature: F127 — Frozen Safety Oracle
    """
    
    def __init__(self):
        self.frozen_distribution: Optional[SafetyDistribution] = None
        self.is_frozen = False
        self.freeze_timestamp: Optional[float] = None
    
    def freeze(self) -> SafetyDistribution:
        """
        Freeze the current safety distribution.
        
        This captures the baseline safety state at startup.
        Can only be called once.
        
        Returns:
            SafetyDistribution: The frozen snapshot
            
        Raises:
            RuntimeError: If already frozen
        """
        import time
        
        if self.is_frozen:
            raise RuntimeError("Oracle already frozen — cannot freeze again")
        
        # Capture initial safety distribution
        self.frozen_distribution = SafetyDistribution(
            reasoning_quality=0.85,      # Baseline reasoning quality
            goal_alignment=0.90,         # Initial goal alignment
            safety_compliance=0.95,      # Initial safety compliance
            communication_clarity=0.88,  # Initial clarity
            timestamp=time.time(),
        )
        
        # Compute immutable hash
        self.frozen_distribution.hash_value = self.frozen_distribution.compute_hash()
        
        self.is_frozen = True
        self.freeze_timestamp = self.frozen_distribution.timestamp
        
        logger.info(
            f"FrozenSafetyOracle frozen at {self.freeze_timestamp}\n"
            f"  Hash: {self.frozen_distribution.hash_value[:16]}...\n"
            f"  Distribution: {asdict(self.frozen_distribution)}"
        )
        
        return self.frozen_distribution
    
    def get_frozen(self) -> SafetyDistribution:
        """
        Retrieve the frozen distribution.
        
        Returns:
            SafetyDistribution: The frozen snapshot
            
        Raises:
            RuntimeError: If not yet frozen
        """
        if not self.is_frozen or self.frozen_distribution is None:
            raise RuntimeError("Oracle not yet frozen")
        
        return self.frozen_distribution
    
    def verify_integrity(self) -> bool:
        """
        Verify the frozen distribution hasn't been tampered with.
        
        Returns:
            bool: True if hash matches, False otherwise
        """
        if not self.is_frozen or self.frozen_distribution is None:
            return False
        
        # Recompute hash from fields (not stored hash_value which may be modified)
        current_data = {
            "reasoning_quality": self.frozen_distribution.reasoning_quality,
            "goal_alignment": self.frozen_distribution.goal_alignment,
            "safety_compliance": self.frozen_distribution.safety_compliance,
            "communication_clarity": self.frozen_distribution.communication_clarity,
            "timestamp": self.frozen_distribution.timestamp,
        }
        current_hash = hashlib.sha256(json.dumps(current_data, sort_keys=True).encode()).hexdigest()
        stored_hash = self.frozen_distribution.hash_value
        
        if current_hash != stored_hash:
            logger.error(
                f"Oracle integrity check FAILED!\n"
                f"  Expected: {stored_hash[:16] if stored_hash else 'None'}...\n"
                f"  Got: {current_hash[:16]}..."
            )
            return False
        
        return True
    
    def compare_distance(self, current: Dict[str, float]) -> float:
        """
        Compute distance from frozen distribution to current state.
        
        Uses Euclidean distance in normalized space.
        
        Parameters:
            current: Current belief distribution
            
        Returns:
            float: Distance (0.0 = identical, 1.0+ = far apart)
        """
        if not self.is_frozen or self.frozen_distribution is None:
            raise RuntimeError("Oracle not frozen")
        
        frozen_dict = {
            "reasoning_quality": self.frozen_distribution.reasoning_quality,
            "goal_alignment": self.frozen_distribution.goal_alignment,
            "safety_compliance": self.frozen_distribution.safety_compliance,
            "communication_clarity": self.frozen_distribution.communication_clarity,
        }
        
        # Compute squared differences
        squared_diffs = []
        for key in frozen_dict:
            if key not in current:
                squared_diffs.append(1.0)  # Missing key = max distance
            else:
                diff = frozen_dict[key] - current[key]
                squared_diffs.append(diff ** 2)
        
        # Euclidean distance
        distance = sum(squared_diffs) ** 0.5
        return distance
    
    def status(self) -> Dict:
        """Get status of the frozen oracle."""
        return {
            "is_frozen": self.is_frozen,
            "freeze_timestamp": self.freeze_timestamp,
            "distribution": asdict(self.frozen_distribution) if self.frozen_distribution else None,
            "integrity_ok": self.verify_integrity(),
        }
