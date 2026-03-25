"""
F616: Co-Evolution Loop Orchestrator
====================================

Coordinates the complete co-evolution cycle:
- Proposer → Solver → Judge → Validator pipeline
- Multi-population management (10-50 agents per population)
- Evolution metrics tracking
- Adaptive mutation rates based on stagnation
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from datetime import datetime, timezone
import uuid

from .proposer import MAEProposer, ProposalStrategy, PopulationSnapshot
from .solver import MAESolver, ConflictResolutionStrategy
from .judge import MAEJudge, BenchmarkType

logger = logging.getLogger(__name__)


@dataclass
class EvolutionState:
    """State of co-evolution process."""
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_generation: int = 0
    populations: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    best_solutions: List[str] = field(default_factory=list)
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    diversity_score: float = 0.5
    convergence_rate: float = 0.0
    stagnation_counter: int = 0
    creation_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_improvement_generation: int = 0


class CoEvolutionOrchestrator:
    """Orchestrates complete co-evolution cycle."""

    def __init__(
        self,
        num_populations: int = 3,
        population_size: int = 20,
        max_generations: int = 100,
        elite_rate: float = 0.1,
    ):
        """Initialize Co-Evolution Orchestrator.

        Args:
            num_populations: Number of evolving populations
            population_size: Size of each population
            max_generations: Maximum generations to evolve
            elite_rate: Proportion of elite agents to preserve
        """
        self.num_populations = num_populations
        self.population_size = population_size
        self.max_generations = max_generations
        self.elite_rate = elite_rate

        # Core components
        self.proposer = MAEProposer(
            population_size=population_size,
            proposal_batch_size=population_size // 4
        )
        self.solver = MAESolver()
        self.judge = MAEJudge()

        # State management
        self.evolution_state: Optional[EvolutionState] = None
        self.state_history: List[EvolutionState] = []
        self.cycle_history: List[Dict[str, Any]] = []
        self.is_running = False
        self.best_fitness_ever = 0.0

    async def initialize_evolution(
        self,
        population_factory: Callable[[], Dict[str, Any]],
    ) -> EvolutionState:
        """Initialize co-evolution with initial populations.

        Args:
            population_factory: Callable that creates individual agents

        Returns:
            Initial evolution state
        """
        populations = {}
        for i in range(self.num_populations):
            pop_id = f"population_{i}"
            populations[pop_id] = [
                population_factory() for _ in range(self.population_size)
            ]

        self.evolution_state = EvolutionState(
            populations=populations,
            mutation_rate=0.1,
            crossover_rate=0.7,
        )

        logger.info(
            f"Initialized co-evolution with {self.num_populations} populations"
        )
        return self.evolution_state

    async def run_evolution_cycle(self) -> Tuple[EvolutionState, Dict[str, Any]]:
        """Run one complete co-evolution cycle.

        Returns:
            Updated evolution state and cycle metrics
        """
        if not self.evolution_state:
            raise RuntimeError("Evolution not initialized")

        state = self.evolution_state
        cycle_start = datetime.now(timezone.utc)

        cycle_metrics = {
            "generation": state.current_generation,
            "cycle_timestamp": cycle_start.isoformat(),
            "stages": {},
        }

        # Stage 1: Generate Proposals
        proposals_stage = await self._stage_propose(state)
        cycle_metrics["stages"]["proposal"] = proposals_stage

        # Stage 2: Resolve Conflicts
        solver_stage = await self._stage_solve(proposals_stage["proposals"])
        cycle_metrics["stages"]["solver"] = solver_stage

        # Stage 3: Evaluate Quality
        judge_stage = await self._stage_judge(
            solver_stage["solutions"],
            state.populations
        )
        cycle_metrics["stages"]["judge"] = judge_stage

        # Stage 4: Update Populations
        updated_state = await self._stage_update(
            state,
            solver_stage["solutions"],
            judge_stage["metrics"]
        )

        # Stage 5: Adaptive Parameter Tuning
        await self._adapt_parameters(updated_state)

        cycle_duration_ms = (
            (datetime.now(timezone.utc) - cycle_start).total_seconds() * 1000
        )
        cycle_metrics["duration_ms"] = cycle_duration_ms

        self.evolution_state = updated_state
        self.state_history.append(updated_state)
        self.cycle_history.append(cycle_metrics)

        logger.info(f"Completed evolution cycle {state.current_generation}")
        return updated_state, cycle_metrics

    async def _stage_propose(self, state: EvolutionState) -> Dict[str, Any]:
        """Generate proposals from all populations."""
        all_proposals = []

        for pop_id, population in state.populations.items():
            # Create population snapshot
            snapshot = PopulationSnapshot(
                agents=population,
                generation=state.current_generation,
                diversity_metric=state.diversity_score,
                avg_fitness=state.convergence_rate,
            )

            # Generate proposals using multiple strategies
            proposals = await self.proposer.generate_proposals(
                snapshot,
                strategies=[
                    ProposalStrategy.GENETIC_ALGORITHM,
                    ProposalStrategy.PARTICLE_SWARM,
                    ProposalStrategy.DIFFERENTIAL_EVOLUTION,
                ]
            )
            all_proposals.extend(proposals)

        return {
            "stage": "propose",
            "num_proposals": len(all_proposals),
            "proposals": all_proposals,
        }

    async def _stage_solve(self, proposals: List[Any]) -> Dict[str, Any]:
        """Resolve conflicting proposals."""
        if not proposals:
            return {
                "stage": "solve",
                "num_solutions": 0,
                "solutions": [],
            }

        solutions = await self.solver.resolve_proposals(
            proposals,
            strategy=ConflictResolutionStrategy.PARETO_DOMINANCE
        )

        return {
            "stage": "solve",
            "num_solutions": len(solutions),
            "solutions": solutions,
            "pareto_frontier": self.solver.get_pareto_frontier(),
        }

    async def _stage_judge(
        self,
        solutions: List[Any],
        populations: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Evaluate solutions quality."""
        population_by_id = {}
        for pop_id, pop_list in populations.items():
            for agent in pop_list:
                agent_id = agent.get("id", str(uuid.uuid4()))
                population_by_id[agent_id] = agent

        # Evaluate best solutions
        ranked_solutions = []
        for solution in solutions[:min(10, len(solutions))]:
            fitness_score = await self.judge.evaluate_solution(
                solution.solution_id,
                {**solution.objectives, **solution.implementation}
            )
            ranked_solutions.append((solution, fitness_score))

        # Get population metrics
        population_metrics = await self.judge.evaluate_population(
            population_by_id,
            generation=self.evolution_state.current_generation
        )

        return {
            "stage": "judge",
            "num_evaluated": len(ranked_solutions),
            "top_solutions": [
                (s.solution_id, f.overall_fitness)
                for s, f in ranked_solutions[:5]
            ],
            "metrics": population_metrics,
        }

    async def _stage_update(
        self,
        state: EvolutionState,
        solutions: List[Any],
        metrics: Any,
    ) -> EvolutionState:
        """Update populations with best solutions."""
        new_state = EvolutionState(
            current_generation=state.current_generation + 1,
            populations=state.populations.copy(),
            mutation_rate=state.mutation_rate,
            crossover_rate=state.crossover_rate,
            stagnation_counter=state.stagnation_counter,
        )

        # Select best solutions and add to populations
        if solutions:
            best_solutions = sorted(
                solutions,
                key=lambda s: self._get_solution_fitness(s),
                reverse=True
            )[:self.population_size // 4]

            new_state.best_solutions = [s.solution_id for s in best_solutions]

            # Add best solutions to first population
            if new_state.populations:
                first_pop_id = list(new_state.populations.keys())[0]
                for solution in best_solutions:
                    new_agent = {
                        "id": solution.solution_id,
                        **solution.objectives,
                        **solution.implementation,
                    }
                    new_state.populations[first_pop_id].append(new_agent)

                # Trim population to size
                new_state.populations[first_pop_id] = (
                    new_state.populations[first_pop_id][-self.population_size:]
                )

        # Update metrics
        if metrics:
            new_state.diversity_score = metrics.diversity_index
            new_state.convergence_rate = metrics.convergence_rate
            new_state.stagnation_counter = metrics.stagnation_counter

            if metrics.best_fitness > self.best_fitness_ever:
                self.best_fitness_ever = metrics.best_fitness
                new_state.last_improvement_generation = new_state.current_generation

        return new_state

    async def _adapt_parameters(self, state: EvolutionState) -> None:
        """Adaptively adjust mutation and crossover rates.

        Based on convergence state and stagnation.
        """
        # Increase mutation if stagnating
        if state.stagnation_counter > 5:
            state.mutation_rate = min(0.3, state.mutation_rate * 1.2)
            logger.info(f"Increased mutation rate to {state.mutation_rate:.3f}")

        # Decrease mutation if converged
        if state.convergence_rate > 0.9:
            state.mutation_rate = max(0.05, state.mutation_rate * 0.8)
            logger.info(f"Decreased mutation rate to {state.mutation_rate:.3f}")

        # Adjust crossover based on diversity
        if state.diversity_score < 0.2:
            state.crossover_rate = min(0.9, state.crossover_rate * 1.1)
        elif state.diversity_score > 0.7:
            state.crossover_rate = max(0.5, state.crossover_rate * 0.9)

    async def run_full_evolution(self, duration_seconds: float = 300) -> Dict[str, Any]:
        """Run evolution for specified duration or until convergence.

        Args:
            duration_seconds: Maximum evolution duration

        Returns:
            Final evolution summary
        """
        self.is_running = True
        start_time = datetime.now(timezone.utc)

        try:
            generation = 0
            while generation < self.max_generations:
                # Check time limit
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                if elapsed > duration_seconds:
                    logger.info(f"Evolution time limit reached ({elapsed:.1f}s)")
                    break

                # Run evolution cycle
                state, cycle_metrics = await self.run_evolution_cycle()
                generation += 1

                # Check convergence
                if state.convergence_rate > 0.95:
                    logger.info(
                        f"Evolution converged at generation {generation}"
                    )
                    break

                await asyncio.sleep(0)

            return self._summarize_evolution(state)

        finally:
            self.is_running = False

    def _summarize_evolution(self, final_state: EvolutionState) -> Dict[str, Any]:
        """Create summary of evolution results."""
        return {
            "final_generation": final_state.current_generation,
            "num_cycles": len(self.cycle_history),
            "best_solutions": final_state.best_solutions,
            "best_fitness": self.best_fitness_ever,
            "final_diversity": final_state.diversity_score,
            "final_convergence": final_state.convergence_rate,
            "proposal_count": len(self.proposer.proposal_history),
            "judge_evaluations": len(self.judge.fitness_scores),
            "pareto_frontier_size": len(self.solver.pareto_frontier),
        }

    def _get_solution_fitness(self, solution: Any) -> float:
        """Extract fitness value from solution."""
        if hasattr(solution, "objectives"):
            return solution.objectives.get("fitness", 0.0)
        return 0.0

    def get_evolution_status(self) -> Dict[str, Any]:
        """Get current evolution status."""
        if not self.evolution_state:
            return {"status": "not_initialized"}

        return {
            "is_running": self.is_running,
            "generation": self.evolution_state.current_generation,
            "num_populations": len(self.evolution_state.populations),
            "mutation_rate": self.evolution_state.mutation_rate,
            "convergence_rate": self.evolution_state.convergence_rate,
            "diversity_score": self.evolution_state.diversity_score,
            "best_fitness": self.best_fitness_ever,
            "cycles_completed": len(self.cycle_history),
        }
