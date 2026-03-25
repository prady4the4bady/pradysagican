"""
F613: MAE Solver - Adversarial Resolution & Multi-Objective Optimization
=========================================================================

Resolve conflicts between competing proposals through:
- Pareto frontier calculation for multi-objective optimization
- Conflict resolution strategies
- Solution space exploration
- Return best candidates for validation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving conflicting proposals."""
    PARETO_DOMINANCE = "pareto_dominance"
    WEIGHTED_SUM = "weighted_sum"
    LEXICOGRAPHIC = "lexicographic"
    FUZZY_LOGIC = "fuzzy_logic"
    VOTING = "voting"


@dataclass
class Objective:
    """Represents an optimization objective."""
    name: str
    weight: float = 1.0
    is_maximized: bool = True
    importance: float = 1.0


@dataclass
class Solution:
    """Represents a candidate solution from proposal resolution."""
    solution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_ids: List[str] = field(default_factory=list)
    objectives: Dict[str, float] = field(default_factory=dict)
    pareto_rank: int = 0
    dominated_by_count: int = 0
    crowding_distance: float = 0.0
    feasibility_score: float = 1.0
    implementation: Dict[str, Any] = field(default_factory=dict)
    conflict_resolutions: List[str] = field(default_factory=list)
    creation_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_dominated_by(self, other: Solution, objectives: List[Objective]) -> bool:
        """Check if this solution is dominated by another."""
        is_dominated = False
        for obj in objectives:
            obj_name = obj.name

            self_val = self.objectives.get(obj_name, 0)
            other_val = other.objectives.get(obj_name, 0)

            if obj.is_maximized:
                if other_val > self_val:
                    is_dominated = True
                elif self_val > other_val:
                    return False
            else:
                if other_val < self_val:
                    is_dominated = True
                elif self_val < other_val:
                    return False

        return is_dominated

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "solution_id": self.solution_id,
            "num_proposals": len(self.proposal_ids),
            "objectives": self.objectives,
            "pareto_rank": self.pareto_rank,
            "feasibility_score": self.feasibility_score,
            "crowding_distance": self.crowding_distance,
            "created_at": self.creation_timestamp.isoformat(),
        }


class MAESolver:
    """Multi-Agent Evolution Solver for resolving competing proposals."""

    def __init__(self, objectives: Optional[List[Objective]] = None):
        """Initialize MAE Solver.

        Args:
            objectives: List of optimization objectives
        """
        self.objectives = objectives or [
            Objective("fitness", weight=1.0, is_maximized=True),
            Objective("novelty", weight=0.5, is_maximized=True),
            Objective("efficiency", weight=0.8, is_maximized=True),
        ]
        self.solutions: Dict[str, Solution] = {}
        self.pareto_frontier: List[Solution] = []
        self.resolution_history: List[Dict[str, Any]] = []

    async def resolve_proposals(
        self,
        proposals: List[Any],
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.PARETO_DOMINANCE,
    ) -> List[Solution]:
        """Resolve conflicting proposals into candidate solutions.

        Args:
            proposals: List of competing proposals
            strategy: Resolution strategy to use

        Returns:
            List of non-dominated solutions
        """
        if not proposals:
            return []

        candidates: List[Solution] = []

        if strategy == ConflictResolutionStrategy.PARETO_DOMINANCE:
            candidates = await self._resolve_pareto(proposals)
        elif strategy == ConflictResolutionStrategy.WEIGHTED_SUM:
            candidates = await self._resolve_weighted_sum(proposals)
        elif strategy == ConflictResolutionStrategy.LEXICOGRAPHIC:
            candidates = await self._resolve_lexicographic(proposals)
        elif strategy == ConflictResolutionStrategy.FUZZY_LOGIC:
            candidates = await self._resolve_fuzzy_logic(proposals)
        elif strategy == ConflictResolutionStrategy.VOTING:
            candidates = await self._resolve_voting(proposals)

        # Calculate crowding distance
        for solution in candidates:
            solution.crowding_distance = self._calculate_crowding_distance(
                solution, candidates
            )

        self.pareto_frontier = sorted(
            candidates,
            key=lambda s: (-s.pareto_rank, -s.crowding_distance)
        )

        self.resolution_history.append({
            "strategy": strategy.value,
            "num_proposals": len(proposals),
            "num_solutions": len(candidates),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(
            f"Resolved {len(proposals)} proposals into {len(candidates)} candidates"
        )
        return candidates

    async def _resolve_pareto(self, proposals: List[Any]) -> List[Solution]:
        """Resolve using Pareto dominance (NSGA-II style)."""
        solutions: List[Solution] = []

        # Create initial solutions from proposals
        for proposal in proposals:
            solution = Solution(
                proposal_ids=[proposal.proposal_id],
                objectives={
                    "fitness": proposal.fitness_estimate,
                    "novelty": proposal.novelty,
                    "efficiency": self._calculate_efficiency(proposal),
                }
            )
            solutions.append(solution)

        # Calculate Pareto ranks
        rank = 0
        remaining = set(solutions)

        while remaining:
            # Find non-dominated solutions in current set
            front = []
            for s1 in remaining:
                is_dominated = False
                for s2 in remaining:
                    if s1 != s2 and s1.is_dominated_by(s2, self.objectives):
                        is_dominated = True
                        break
                if not is_dominated:
                    front.append(s1)

            # Assign rank and remove from remaining
            for solution in front:
                solution.pareto_rank = rank
                remaining.remove(solution)

            rank += 1

        return solutions

    async def _resolve_weighted_sum(self, proposals: List[Any]) -> List[Solution]:
        """Resolve using weighted sum (scalarization)."""
        solutions: List[Solution] = []

        for proposal in proposals:
            # Calculate weighted sum
            objectives = {
                "fitness": proposal.fitness_estimate,
                "novelty": proposal.novelty,
                "efficiency": self._calculate_efficiency(proposal),
            }

            weighted_score = sum(
                objectives.get(obj.name, 0) * obj.weight
                for obj in self.objectives
            )

            solution = Solution(
                proposal_ids=[proposal.proposal_id],
                objectives={**objectives, "weighted_score": weighted_score}
            )
            solution.feasibility_score = min(
                1.0, sum(objectives.values()) / len(objectives)
            )
            solutions.append(solution)

        # Sort by weighted score and assign ranks
        solutions.sort(key=lambda s: s.objectives.get("weighted_score", 0), reverse=True)
        for i, solution in enumerate(solutions):
            solution.pareto_rank = i // max(1, len(solutions) // 4)

        return solutions

    async def _resolve_lexicographic(self, proposals: List[Any]) -> List[Solution]:
        """Resolve using lexicographic ordering."""
        solutions: List[Solution] = []

        for proposal in proposals:
            solution = Solution(
                proposal_ids=[proposal.proposal_id],
                objectives={
                    "fitness": proposal.fitness_estimate,
                    "novelty": proposal.novelty,
                    "efficiency": self._calculate_efficiency(proposal),
                }
            )
            solutions.append(solution)

        # Sort lexicographically by objectives in order
        for obj in reversed(self.objectives):
            solutions.sort(
                key=lambda s: s.objectives.get(obj.name, 0),
                reverse=obj.is_maximized
            )

        for i, solution in enumerate(solutions):
            solution.pareto_rank = i // max(1, len(solutions) // 4)

        return solutions

    async def _resolve_fuzzy_logic(self, proposals: List[Any]) -> List[Solution]:
        """Resolve using fuzzy logic membership."""
        solutions: List[Solution] = []

        # Determine membership boundaries
        fitness_scores = [p.fitness_estimate for p in proposals]
        novelty_scores = [p.novelty for p in proposals]
        efficiency_scores = [
            self._calculate_efficiency(p) for p in proposals
        ]

        for proposal in proposals:
            # Calculate fuzzy membership
            fitness_membership = self._fuzzy_membership(
                proposal.fitness_estimate,
                min(fitness_scores),
                max(fitness_scores)
            )
            novelty_membership = self._fuzzy_membership(
                proposal.novelty,
                min(novelty_scores),
                max(novelty_scores)
            )
            efficiency_membership = self._fuzzy_membership(
                self._calculate_efficiency(proposal),
                min(efficiency_scores),
                max(efficiency_scores)
            )

            # Aggregate memberships
            aggregate_membership = (
                fitness_membership * 0.5 +
                novelty_membership * 0.3 +
                efficiency_membership * 0.2
            )

            solution = Solution(
                proposal_ids=[proposal.proposal_id],
                objectives={
                    "fitness": proposal.fitness_estimate,
                    "novelty": proposal.novelty,
                    "efficiency": self._calculate_efficiency(proposal),
                    "fuzzy_score": aggregate_membership,
                },
                feasibility_score=aggregate_membership
            )
            solutions.append(solution)

        # Sort by fuzzy score
        solutions.sort(
            key=lambda s: s.objectives.get("fuzzy_score", 0),
            reverse=True
        )
        for i, solution in enumerate(solutions):
            solution.pareto_rank = i // max(1, len(solutions) // 4)

        return solutions

    async def _resolve_voting(self, proposals: List[Any]) -> List[Solution]:
        """Resolve using voting mechanism."""
        solutions: List[Solution] = []
        vote_counts: Dict[str, int] = {}

        # Each proposal votes for similar proposals
        for proposal in proposals:
            for other in proposals:
                if proposal.proposal_id != other.proposal_id:
                    similarity = self._calculate_similarity(proposal, other)
                    if similarity > 0.7:
                        proposal_key = other.proposal_id
                        vote_counts[proposal_key] = vote_counts.get(proposal_key, 0) + 1

        for proposal in proposals:
            votes = vote_counts.get(proposal.proposal_id, 0)

            solution = Solution(
                proposal_ids=[proposal.proposal_id],
                objectives={
                    "fitness": proposal.fitness_estimate,
                    "novelty": proposal.novelty,
                    "efficiency": self._calculate_efficiency(proposal),
                    "votes": votes,
                },
                feasibility_score=min(1.0, votes / len(proposals))
            )
            solutions.append(solution)

        # Sort by votes
        solutions.sort(key=lambda s: s.objectives.get("votes", 0), reverse=True)
        for i, solution in enumerate(solutions):
            solution.pareto_rank = i // max(1, len(solutions) // 4)

        return solutions

    def _calculate_efficiency(self, proposal: Any) -> float:
        """Calculate efficiency metric for proposal."""
        improvements = proposal.improvements or {}
        if not improvements:
            return 0.5

        # Efficiency = average improvement / complexity
        avg_improvement = sum(improvements.values()) / len(improvements)
        complexity = len(improvements) * 0.05
        return min(1.0, avg_improvement / (1.0 + complexity))

    def _calculate_crowding_distance(
        self,
        solution: Solution,
        solutions: List[Solution]
    ) -> float:
        """Calculate crowding distance in objective space."""
        if len(solutions) <= 2:
            return float('inf')

        distance = 0.0

        for obj in self.objectives:
            obj_name = obj.name
            values = sorted(
                [s.objectives.get(obj_name, 0) for s in solutions]
            )

            if len(values) > 1:
                min_val = values[0]
                max_val = values[-1]

                if max_val - min_val > 1e-10:
                    distance += 1.0 / (1.0 + abs(max_val - min_val))

        return distance / len(self.objectives)

    def _fuzzy_membership(self, value: float, min_val: float, max_val: float) -> float:
        """Calculate fuzzy membership (0-1) for a value."""
        if max_val - min_val < 1e-10:
            return 0.5

        # Triangular membership function
        normalized = (value - min_val) / (max_val - min_val)
        return min(1.0, max(0.0, 1.0 - abs(2.0 * normalized - 1.0)))

    def _calculate_similarity(self, proposal1: Any, proposal2: Any) -> float:
        """Calculate similarity between two proposals."""
        imp1 = set(proposal1.improvements.keys()) if proposal1.improvements else set()
        imp2 = set(proposal2.improvements.keys()) if proposal2.improvements else set()

        if not imp1 and not imp2:
            return 1.0

        if not imp1 or not imp2:
            return 0.0

        intersection = len(imp1 & imp2)
        union = len(imp1 | imp2)

        return intersection / union if union > 0 else 0.0

    def get_pareto_frontier(self) -> List[Dict[str, Any]]:
        """Get current Pareto frontier."""
        return [s.to_dict() for s in self.pareto_frontier]

    def get_best_solutions(self, count: int = 5) -> List[Solution]:
        """Get top N solutions from Pareto frontier."""
        return self.pareto_frontier[:count]

    def add_objective(self, objective: Objective) -> None:
        """Add new objective to optimization."""
        self.objectives.append(objective)

    def set_objective_weights(self, weights: Dict[str, float]) -> None:
        """Update weights for existing objectives."""
        for obj in self.objectives:
            if obj.name in weights:
                obj.weight = weights[obj.name]
