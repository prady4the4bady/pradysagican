"""
SafeBasinTopography — Maps safety space as loss landscape

Feature: F123 — Safe Basin Topography

Uses gradient-like analysis to determine if current state is in the
"safe basin" — the region of behavior space that is deemed safe.

Safe basin = region where all constraints are satisfied and drift is minimal.
"""

import logging
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)


class SafeBasinTopography:
    """
    Maps the safety landscape.
    
    Classifies points in state space as safe basin or risky.
    """
    
    def __init__(self):
        self.visits = 0
        self.safe_count = 0
        self.unsafe_count = 0
        self.basin_center: Optional[Dict[str, float]] = None
        self.basin_radius = 0.5  # Default safety radius
    
    def is_in_basin(self, state: Dict[str, float]) -> bool:
        """
        Determine if state is in safe basin.
        
        Parameters:
            state: Current agent state/beliefs
            
        Returns:
            bool: True if in safe basin, False if risky
        """
        self.visits += 1
        
        # Define basin center (ideal state)
        if self.basin_center is None:
            self.basin_center = {
                "reasoning_quality": 0.85,
                "goal_alignment": 0.90,
                "safety_compliance": 0.95,
                "communication_clarity": 0.88,
            }
        
        # Compute distance from basin center
        distance = self._compute_distance(state, self.basin_center)
        
        in_basin = distance <= self.basin_radius
        
        if in_basin:
            self.safe_count += 1
        else:
            self.unsafe_count += 1
        
        return in_basin
    
    def _compute_distance(self, state: Dict[str, float], center: Dict[str, float]) -> float:
        """Compute Euclidean distance from state to center."""
        squared_sum = 0.0
        
        for key in center:
            s = state.get(key, 0.5)  # Default to 0.5 if missing
            c = center[key]
            squared_sum += (s - c) ** 2
        
        return squared_sum ** 0.5
    
    def map_basin(self, samples: int = 100) -> Dict:
        """
        Map the safe basin by sampling (expensive operation).
        
        Parameters:
            samples: Number of samples to take
            
        Returns:
            dict: Basin topology information
        """
        logger.info(f"Mapping basin with {samples} samples...")
        
        basin_points = []
        edge_points = []
        unsafe_points = []
        
        for i in range(samples):
            # Generate random point in state space
            test_state = self._generate_test_point(i, samples)
            
            if self.is_in_basin(test_state):
                basin_points.append(test_state)
            else:
                distance = self._compute_distance(test_state, self.basin_center)
                if distance <= self.basin_radius + 0.1:  # Near edge
                    edge_points.append(test_state)
                else:
                    unsafe_points.append(test_state)
        
        return {
            "basin_points": len(basin_points),
            "edge_points": len(edge_points),
            "unsafe_points": len(unsafe_points),
            "basin_density": len(basin_points) / samples,
            "edge_zone": len(edge_points) / samples,
        }
    
    def _generate_test_point(self, index: int, total: int) -> Dict[str, float]:
        """Generate a test point in state space."""
        # Simple sampling: grid-like traversal
        factor = index / max(1, total)
        
        return {
            "reasoning_quality": 0.5 + 0.5 * factor,
            "goal_alignment": 0.5 + 0.5 * factor,
            "safety_compliance": 0.5 + 0.5 * factor,
            "communication_clarity": 0.5 + 0.5 * factor,
        }
    
    def update_basin(self, new_center: Optional[Dict[str, float]] = None, new_radius: Optional[float] = None) -> None:
        """
        Update basin definition (should be rare).
        
        Parameters:
            new_center: New basin center
            new_radius: New basin radius
        """
        if new_center:
            logger.info(f"Updating basin center: {new_center}")
            self.basin_center = new_center
        
        if new_radius:
            logger.info(f"Updating basin radius: {new_radius}")
            self.basin_radius = new_radius
    
    def get_statistics(self) -> Dict:
        """Get basin statistics."""
        if self.visits == 0:
            return {"visits": 0}
        
        return {
            "visits": self.visits,
            "safe_count": self.safe_count,
            "unsafe_count": self.unsafe_count,
            "safety_rate": self.safe_count / self.visits,
            "basin_center": self.basin_center,
            "basin_radius": self.basin_radius,
        }
    
    def status(self) -> Dict:
        """Get full status."""
        return {
            "visits": self.visits,
            "safety_rate": (self.safe_count / self.visits) if self.visits > 0 else 0.0,
            "statistics": self.get_statistics(),
        }
