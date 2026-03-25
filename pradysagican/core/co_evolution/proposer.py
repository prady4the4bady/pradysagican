"""
F612: MAE Proposer - Multi-Agent Evolution Proposal Generation
==============================================================

Generate improvement proposals from agent population using:
- Genetic algorithms for code-based solutions
- Particle swarm optimization for parameter tuning
- Differential evolution for continuous improvements
- Cultural consensus for collective decisions
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Dict, Tuple
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class ProposalStrategy(Enum):
    """Strategies for generating proposals."""
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"
    DIFFERENTIAL_EVOLUTION = "differential_evolution"
    CULTURAL_CONSENSUS = "cultural_consensus"


@dataclass
class Proposal:
    """Represents an improvement proposal."""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy: str = "genetic_algorithm"
    improvements: Dict[str, float] = field(default_factory=dict)
    fitness_estimate: float = 0.0
    source_population: List[str] = field(default_factory=list)
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)
    implementation: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    novelty: float = 0.0
    parent_proposals: List[str] = field(default_factory=list)
    generation: int = 0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert proposal to dictionary."""
        return {
            "proposal_id": self.proposal_id,
            "strategy": self.strategy,
            "improvements": self.improvements,
            "fitness_estimate": self.fitness_estimate,
            "confidence": self.confidence,
            "novelty": self.novelty,
            "generation": self.generation,
            "source_population_size": len(self.source_population),
            "tags": self.tags,
            "created_at": self.creation_timestamp.isoformat(),
        }


@dataclass
class PopulationSnapshot:
    """Snapshot of population state for analysis."""
    agents: List[Dict[str, Any]] = field(default_factory=list)
    fitness_scores: Dict[str, float] = field(default_factory=dict)
    diversity_metric: float = 0.0
    avg_fitness: float = 0.0
    best_fitness: float = 0.0
    worst_fitness: float = 0.0
    generation: int = 0


class MAEProposer:
    """Multi-Agent Evolution Proposer for generating improvement proposals."""

    def __init__(
        self,
        population_size: int = 20,
        proposal_batch_size: int = 5,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
    ):
        """Initialize MAE Proposer.

        Args:
            population_size: Size of agent population
            proposal_batch_size: Number of proposals to generate per cycle
            mutation_rate: Rate of mutations in genetic algorithm
            crossover_rate: Rate of crossovers in genetic algorithm
        """
        self.population_size = population_size
        self.proposal_batch_size = proposal_batch_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.proposal_history: List[Proposal] = []
        self.generation_count: int = 0
        self.active_proposals: Dict[str, Proposal] = {}

    async def propose_genetic_algorithm(
        self,
        population: PopulationSnapshot,
        elite_rate: float = 0.2,
    ) -> List[Proposal]:
        """Generate proposals using genetic algorithm strategy.

        Args:
            population: Current population snapshot
            elite_rate: Proportion of elite agents to preserve

        Returns:
            List of proposed improvements
        """
        proposals: List[Proposal] = []
        elite_count = max(1, int(self.population_size * elite_rate))

        # Select elite agents
        sorted_agents = sorted(
            population.agents,
            key=lambda a: population.fitness_scores.get(a.get("id"), 0),
            reverse=True
        )
        elite = sorted_agents[:elite_count]

        for _ in range(self.proposal_batch_size):
            if random.random() < self.crossover_rate and len(elite) >= 2:
                # Crossover strategy
                parent1, parent2 = random.sample(elite, 2)
                proposal = await self._create_crossover_proposal(parent1, parent2)
            else:
                # Mutation strategy
                parent = random.choice(elite)
                proposal = await self._create_mutation_proposal(parent)

            proposal.strategy = ProposalStrategy.GENETIC_ALGORITHM.value
            proposal.source_population = [a.get("id") for a in elite]
            proposal.generation = self.generation_count
            proposals.append(proposal)

        return proposals

    async def propose_particle_swarm(
        self,
        population: PopulationSnapshot,
        cognitive_weight: float = 2.0,
        social_weight: float = 2.0,
        inertia_weight: float = 0.7,
    ) -> List[Proposal]:
        """Generate proposals using particle swarm optimization.

        Args:
            population: Current population snapshot
            cognitive_weight: Individual best influence
            social_weight: Global best influence
            inertia_weight: Momentum factor

        Returns:
            List of proposed improvements
        """
        proposals: List[Proposal] = []

        # Find best agent (global best)
        best_agent = max(
            population.agents,
            key=lambda a: population.fitness_scores.get(a.get("id"), 0)
        )

        for _ in range(self.proposal_batch_size):
            # Select random particle (agent)
            agent = random.choice(population.agents)
            agent_id = agent.get("id")

            # PSO-inspired improvements
            improvements = {
                "velocity_toward_best": social_weight * (
                    best_agent.get("performance", 0) - agent.get("performance", 0)
                ),
                "local_momentum": inertia_weight * agent.get("momentum", 0.1),
                "cognitive_update": cognitive_weight * random.random(),
            }

            proposal = Proposal(
                strategy=ProposalStrategy.PARTICLE_SWARM.value,
                improvements=improvements,
                fitness_estimate=population.fitness_scores.get(agent_id, 0) + 0.05,
                source_population=[agent_id],
                generation=self.generation_count,
                confidence=0.7,
                novelty=0.3,
            )
            proposals.append(proposal)

        return proposals

    async def propose_differential_evolution(
        self,
        population: PopulationSnapshot,
        scale_factor: float = 0.8,
    ) -> List[Proposal]:
        """Generate proposals using differential evolution.

        Args:
            population: Current population snapshot
            scale_factor: Weighting factor for differential evolution

        Returns:
            List of proposed improvements
        """
        proposals: List[Proposal] = []

        for _ in range(self.proposal_batch_size):
            if len(population.agents) >= 3:
                # Select 3 random agents for DE
                r1, r2, r3 = random.sample(population.agents, 3)

                # DE mutation: v = r1 + scale * (r2 - r3)
                improvements = {
                    "base_params": r1.get("parameters", {}),
                    "differential": {
                        "target": r2.get("id"),
                        "reference": r3.get("id"),
                        "scale_factor": scale_factor,
                    }
                }

                fitness_delta = (
                    population.fitness_scores.get(r2.get("id"), 0) -
                    population.fitness_scores.get(r3.get("id"), 0)
                )

                proposal = Proposal(
                    strategy=ProposalStrategy.DIFFERENTIAL_EVOLUTION.value,
                    improvements=improvements,
                    fitness_estimate=population.fitness_scores.get(r1.get("id"), 0) +
                                    (scale_factor * fitness_delta),
                    source_population=[r1.get("id"), r2.get("id"), r3.get("id")],
                    generation=self.generation_count,
                    confidence=0.8,
                    novelty=0.4,
                )
                proposals.append(proposal)

        return proposals

    async def propose_cultural_consensus(
        self,
        population: PopulationSnapshot,
        consensus_threshold: float = 0.6,
    ) -> List[Proposal]:
        """Generate proposals through cultural consensus of population.

        Args:
            population: Current population snapshot
            consensus_threshold: Threshold for consensus agreement

        Returns:
            List of proposed improvements
        """
        proposals: List[Proposal] = []

        # Analyze collective population patterns
        collective_improvements = self._aggregate_improvements(population)

        for _ in range(self.proposal_batch_size):
            # Create proposal based on consensus
            consensus_proposal = Proposal(
                strategy=ProposalStrategy.CULTURAL_CONSENSUS.value,
                improvements=collective_improvements,
                fitness_estimate=population.avg_fitness + 0.1,
                source_population=[a.get("id") for a in population.agents],
                generation=self.generation_count,
                confidence=consensus_threshold,
                novelty=0.2,
            )
            proposals.append(consensus_proposal)

        return proposals

    async def generate_proposals(
        self,
        population: PopulationSnapshot,
        strategies: Optional[List[ProposalStrategy]] = None,
    ) -> List[Proposal]:
        """Generate proposals from population using specified strategies.

        Args:
            population: Current population snapshot
            strategies: List of strategies to use (default: all)

        Returns:
            List of all generated proposals
        """
        all_proposals: List[Proposal] = []

        if strategies is None:
            strategies = list(ProposalStrategy)

        tasks = []

        for strategy in strategies:
            if strategy == ProposalStrategy.GENETIC_ALGORITHM:
                tasks.append(self.propose_genetic_algorithm(population))
            elif strategy == ProposalStrategy.PARTICLE_SWARM:
                tasks.append(self.propose_particle_swarm(population))
            elif strategy == ProposalStrategy.DIFFERENTIAL_EVOLUTION:
                tasks.append(self.propose_differential_evolution(population))
            elif strategy == ProposalStrategy.CULTURAL_CONSENSUS:
                tasks.append(self.propose_cultural_consensus(population))

        if tasks:
            results = await asyncio.gather(*tasks)
            all_proposals = [p for proposals in results for p in proposals]

        self.generation_count += 1
        self.proposal_history.extend(all_proposals)

        for proposal in all_proposals:
            self.active_proposals[proposal.proposal_id] = proposal

        logger.info(
            f"Generated {len(all_proposals)} proposals using {len(strategies)} strategies"
        )
        return all_proposals

    async def _create_mutation_proposal(self, agent: Dict[str, Any]) -> Proposal:
        """Create proposal through mutation of single agent."""
        improvements = {}
        for key in agent.get("capabilities", []):
            if random.random() < self.mutation_rate:
                improvements[key] = agent.get(key, 0) * random.uniform(0.8, 1.2)

        agent_id = agent.get("id", "unknown")
        return Proposal(
            improvements=improvements,
            source_population=[agent_id],
            fitness_estimate=agent.get("fitness", 0) * random.uniform(0.95, 1.05),
            parent_proposals=[],
            confidence=0.6,
            novelty=0.2,
        )

    async def _create_crossover_proposal(
        self,
        parent1: Dict[str, Any],
        parent2: Dict[str, Any]
    ) -> Proposal:
        """Create proposal through crossover of two agents."""
        improvements = {}

        # Crossover capabilities
        caps1 = set(parent1.get("capabilities", []))
        caps2 = set(parent2.get("capabilities", []))
        combined_caps = caps1 | caps2

        for cap in combined_caps:
            if random.random() < 0.5:
                improvements[cap] = parent1.get(cap, 0)
            else:
                improvements[cap] = parent2.get(cap, 0)

        avg_fitness = (
            (parent1.get("fitness", 0) + parent2.get("fitness", 0)) / 2
        ) * random.uniform(0.9, 1.1)

        return Proposal(
            improvements=improvements,
            source_population=[parent1.get("id"), parent2.get("id")],
            fitness_estimate=avg_fitness,
            confidence=0.75,
            novelty=0.3,
        )

    def _aggregate_improvements(self, population: PopulationSnapshot) -> Dict[str, float]:
        """Aggregate improvements across population."""
        aggregated = {}

        for agent in population.agents:
            for key, value in agent.get("improvements", {}).items():
                if key not in aggregated:
                    aggregated[key] = []
                aggregated[key].append(value)

        # Average improvements
        return {k: sum(v) / len(v) if v else 0 for k, v in aggregated.items()}

    def get_proposal_history(self) -> List[Dict[str, Any]]:
        """Get history of generated proposals."""
        return [p.to_dict() for p in self.proposal_history]

    def get_active_proposals(self) -> Dict[str, Dict[str, Any]]:
        """Get currently active proposals."""
        return {pid: p.to_dict() for pid, p in self.active_proposals.items()}

    def retire_proposal(self, proposal_id: str) -> bool:
        """Retire a proposal from active set."""
        if proposal_id in self.active_proposals:
            del self.active_proposals[proposal_id]
            return True
        return False
