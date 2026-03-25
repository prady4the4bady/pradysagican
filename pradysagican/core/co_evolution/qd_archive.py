"""
F617: Quality-Diversity Archive - Behavioral Descriptor & Novelty Metrics
===========================================================================

Extends archive with quality-diversity measures:
- Behavioral descriptors for solution characterization
- Novelty search integration with quality optimization
- Archive management preventing premature convergence
- QD-score (quality × diversity) calculation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum
from datetime import datetime
import uuid
import math

logger = logging.getLogger(__name__)


class BehaviorType(Enum):
    """Types of behavioral descriptors."""
    PERFORMANCE = "performance"
    EXPLORATION = "exploration"
    CONVERGENCE = "convergence"
    DIVERSITY = "diversity"
    ROBUSTNESS = "robustness"


@dataclass
class BehavioralDescriptor:
    """Characterizes solution behavior in the search space."""
    descriptor_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    behavior_type: str = BehaviorType.PERFORMANCE.value
    features: Dict[str, float] = field(default_factory=dict)
    centroid: Optional[List[float]] = None
    magnitude: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def compute_distance(self, other: BehavioralDescriptor) -> float:
        """Compute distance to another behavioral descriptor."""
        if not self.centroid or not other.centroid:
            return 0.0
        
        if len(self.centroid) != len(other.centroid):
            return float('inf')
        
        sum_sq = sum((a - b) ** 2 for a, b in zip(self.centroid, other.centroid))
        return math.sqrt(sum_sq)

    def normalize(self) -> None:
        """Normalize descriptor features."""
        if not self.features:
            return
        
        max_val = max(abs(v) for v in self.features.values()) if self.features else 1.0
        if max_val > 0:
            self.features = {k: v / max_val for k, v in self.features.items()}
        
        if self.centroid:
            mag = math.sqrt(sum(x ** 2 for x in self.centroid))
            if mag > 0:
                self.centroid = [x / mag for x in self.centroid]
                self.magnitude = 1.0


@dataclass
class ArchivedSolution:
    """Solution stored in QD archive."""
    solution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    behavioral_descriptor: Optional[BehavioralDescriptor] = None
    fitness: float = 0.0
    novelty: float = 0.0
    qd_score: float = 0.0
    implementation: Dict[str, Any] = field(default_factory=dict)
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    parent_solution_id: Optional[str] = None

    def update_qd_score(self, quality: float, diversity: float) -> None:
        """Update QD-score based on quality and diversity."""
        self.fitness = quality
        self.novelty = diversity
        self.qd_score = quality * diversity


class QDArchive:
    """Quality-Diversity Archive for maintaining diverse, high-quality solutions."""

    def __init__(
        self,
        max_size: int = 1000,
        novelty_threshold: float = 0.1,
        quality_threshold: float = 0.5,
    ):
        """Initialize QD Archive.

        Args:
            max_size: Maximum solutions to store
            novelty_threshold: Minimum novelty for archive inclusion
            quality_threshold: Minimum fitness for archive inclusion
        """
        self.max_size = max_size
        self.novelty_threshold = novelty_threshold
        self.quality_threshold = quality_threshold

        # Archive storage
        self.solutions: Dict[str, ArchivedSolution] = {}
        self.cells: Dict[str, Set[str]] = {}  # Behavioral cell mapping
        self.frontier: List[str] = []  # Novelty frontier
        
        # Metrics
        self.archive_size = 0
        self.total_stored = 0
        self.rejections = 0
        self.updates = 0

    def _compute_behavioral_cell(self, descriptor: BehavioralDescriptor) -> str:
        """Map behavioral descriptor to discrete cell."""
        if not descriptor.centroid:
            return "unknown"
        
        # Quantize centroid into discrete bins
        cell_coords = tuple(
            int((x + 1.0) * 5) for x in descriptor.centroid[:3]
        )
        return f"cell_{cell_coords}"

    def store_solution(
        self,
        solution_id: str,
        behavioral_descriptor: BehavioralDescriptor,
        fitness: float,
        implementation: Dict[str, Any],
        parent_id: Optional[str] = None,
    ) -> bool:
        """Store solution in archive with quality-diversity metrics.

        Args:
            solution_id: Unique solution identifier
            behavioral_descriptor: Behavioral characterization
            fitness: Quality metric (0.0-1.0)
            implementation: Solution implementation details
            parent_id: Parent solution ID if applicable

        Returns:
            True if solution was stored, False if rejected
        """
        # Compute novelty
        novelty = self._compute_novelty(behavioral_descriptor)
        
        # Check inclusion criteria
        if fitness < self.quality_threshold and novelty < self.novelty_threshold:
            self.rejections += 1
            logger.debug(
                f"Solution {solution_id} rejected: fitness={fitness:.3f}, novelty={novelty:.3f}"
            )
            return False

        # Check if solution already exists
        if solution_id in self.solutions:
            existing = self.solutions[solution_id]
            if fitness > existing.fitness:
                existing.fitness = fitness
                existing.novelty = novelty
                existing.update_qd_score(fitness, novelty)
                self.updates += 1
                logger.debug(f"Updated solution {solution_id}")
            return True

        # Create archived solution
        archived = ArchivedSolution(
            solution_id=solution_id,
            behavioral_descriptor=behavioral_descriptor,
            fitness=fitness,
            novelty=novelty,
            parent_solution_id=parent_id,
            implementation=implementation,
        )
        archived.update_qd_score(fitness, novelty)

        # Check archive capacity
        if len(self.solutions) >= self.max_size:
            self._evict_worst_solution()

        # Store solution
        self.solutions[solution_id] = archived
        cell_id = self._compute_behavioral_cell(behavioral_descriptor)
        
        if cell_id not in self.cells:
            self.cells[cell_id] = set()
        self.cells[cell_id].add(solution_id)
        
        self.archive_size = len(self.solutions)
        self.total_stored += 1
        self._update_frontier()
        
        logger.debug(
            f"Stored solution {solution_id}: fitness={fitness:.3f}, novelty={novelty:.3f}"
        )
        return True

    def sample_with_qd(
        self,
        num_samples: int = 5,
        quality_weight: float = 0.5,
        diversity_weight: float = 0.5,
    ) -> List[ArchivedSolution]:
        """Sample solutions with quality-diversity balancing.

        Args:
            num_samples: Number of solutions to sample
            quality_weight: Weight for fitness in selection
            diversity_weight: Weight for novelty in selection

        Returns:
            List of sampled solutions
        """
        if not self.solutions:
            return []

        if len(self.solutions) <= num_samples:
            return list(self.solutions.values())

        # Compute selection scores
        scores = {}
        for sol_id, solution in self.solutions.items():
            score = (
                quality_weight * solution.fitness +
                diversity_weight * solution.novelty
            )
            scores[sol_id] = score

        # Select top solutions
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected_ids = [sol_id for sol_id, _ in ranked[:num_samples]]
        
        return [self.solutions[sid] for sid in selected_ids]

    def get_novelty_frontier(self) -> List[ArchivedSolution]:
        """Get solutions on the novelty frontier.

        Returns:
            List of frontier solutions
        """
        frontier_solutions = [
            self.solutions[sid] for sid in self.frontier 
            if sid in self.solutions
        ]
        return sorted(
            frontier_solutions,
            key=lambda x: x.novelty,
            reverse=True
        )

    def _compute_novelty(self, descriptor: BehavioralDescriptor) -> float:
        """Compute novelty of a new descriptor.

        Args:
            descriptor: Behavioral descriptor

        Returns:
            Novelty score (0.0-1.0)
        """
        if not self.solutions:
            return 1.0

        # Find k-nearest neighbors
        k = min(15, len(self.solutions))
        distances = []
        
        for solution in self.solutions.values():
            if solution.behavioral_descriptor:
                dist = descriptor.compute_distance(solution.behavioral_descriptor)
                distances.append(dist)

        if not distances:
            return 1.0

        distances.sort()
        avg_nearest = sum(distances[:k]) / k if distances else float('inf')
        
        # Normalize to 0-1 range
        novelty = min(1.0, avg_nearest / 10.0)
        return novelty

    def _evict_worst_solution(self) -> None:
        """Remove lowest QD-score solution to maintain archive size."""
        if not self.solutions:
            return

        worst_id = min(
            self.solutions.keys(),
            key=lambda sid: self.solutions[sid].qd_score
        )
        
        solution = self.solutions.pop(worst_id)
        cell_id = self._compute_behavioral_cell(solution.behavioral_descriptor)
        if cell_id in self.cells:
            self.cells[cell_id].discard(worst_id)

        logger.debug(f"Evicted solution {worst_id} from archive")

    def _update_frontier(self) -> None:
        """Update novelty frontier solutions."""
        if not self.solutions:
            self.frontier = []
            return

        # Solutions with high novelty and decent fitness
        candidates = [
            (sid, sol) for sid, sol in self.solutions.items()
            if sol.novelty >= 0.7 and sol.fitness >= 0.6
        ]

        # Sort by novelty
        self.frontier = [
            sid for sid, _ in sorted(
                candidates,
                key=lambda x: x[1].novelty,
                reverse=True
            )[:min(50, len(candidates))]
        ]

    def get_archive_stats(self) -> Dict[str, Any]:
        """Get archive statistics.

        Returns:
            Dictionary with archive metrics
        """
        if not self.solutions:
            return {
                "size": 0,
                "total_stored": self.total_stored,
                "rejections": self.rejections,
                "updates": self.updates,
                "avg_fitness": 0.0,
                "avg_novelty": 0.0,
                "avg_qd_score": 0.0,
                "frontier_size": 0,
            }

        solutions_list = list(self.solutions.values())
        avg_fitness = sum(s.fitness for s in solutions_list) / len(solutions_list)
        avg_novelty = sum(s.novelty for s in solutions_list) / len(solutions_list)
        avg_qd_score = sum(s.qd_score for s in solutions_list) / len(solutions_list)

        return {
            "size": len(self.solutions),
            "total_stored": self.total_stored,
            "rejections": self.rejections,
            "updates": self.updates,
            "avg_fitness": avg_fitness,
            "avg_novelty": avg_novelty,
            "avg_qd_score": avg_qd_score,
            "frontier_size": len(self.frontier),
            "capacity_used": len(self.solutions) / self.max_size,
        }

    def clear(self) -> None:
        """Clear archive contents."""
        self.solutions.clear()
        self.cells.clear()
        self.frontier.clear()
        self.archive_size = 0
        logger.debug("Archive cleared")
