"""
Multi-Agent Orchestration Framework
====================================

Agent population management and evolutionary operators for co-evolution.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Tuple
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import uuid


class SelectionStrategy(Enum):
    """Population selection strategies."""
    TOURNAMENT = "tournament"
    ROULETTE = "roulette"
    RANK = "rank"
    ELITE = "elite"


@dataclass
class ReproductionOperator:
    """Handles agent reproduction."""
    crossover_rate: float = 0.7
    mutation_rate: float = 0.1
    elite_preservation_rate: float = 0.1

    async def crossover(
        self,
        parent1: Any,
        parent2: Any
    ) -> Tuple[Any, Any]:
        """
        Perform genetic crossover between two agents.
        Creates two offspring from parent genetic material.
        """
        offspring1 = await self._blend_agents(parent1, parent2)
        offspring2 = await self._blend_agents(parent2, parent1)
        return offspring1, offspring2

    async def _blend_agents(self, primary: Any, secondary: Any) -> Any:
        """Blend two agents to create offspring."""
        # This would be overridden for specific agent types
        offspring = type(primary)(agent_id=str(uuid.uuid4()))
        if hasattr(primary, 'capabilities'):
            offspring.capabilities = primary.capabilities.copy()
        if hasattr(primary, 'generation'):
            offspring.generation = primary.generation + 1
        return offspring

    async def mutate(self, agent: Any, mutation_rate: Optional[float] = None) -> Any:
        """
        Apply mutations to an agent.
        Introduces variations for exploration.
        """
        rate = mutation_rate or self.mutation_rate
        mutant = type(agent)(agent_id=str(uuid.uuid4()))

        if hasattr(agent, 'state'):
            mutant.state = agent.state.copy()

        if hasattr(agent, 'generation'):
            mutant.generation = agent.generation + 1

        if hasattr(agent, 'parent_agents'):
            mutant.parent_agents = [agent.agent_id]

        return mutant


@dataclass
class MutationOperator:
    """Handles agent mutations."""
    mutation_types: List[str] = field(default_factory=lambda: [
        "parameter_adjustment",
        "capability_modification",
        "learning_rate_change",
        "strategy_shift"
    ])

    async def apply_mutation(self, agent: Any, mutation_type: Optional[str] = None) -> Any:
        """Apply specific mutation to agent."""
        if mutation_type is None:
            import random
            mutation_type = random.choice(self.mutation_types)

        if mutation_type == "parameter_adjustment":
            return await self._adjust_parameters(agent)
        elif mutation_type == "capability_modification":
            return await self._modify_capabilities(agent)
        elif mutation_type == "learning_rate_change":
            return await self._change_learning_rate(agent)
        elif mutation_type == "strategy_shift":
            return await self._shift_strategy(agent)

        return agent

    async def _adjust_parameters(self, agent: Any) -> Any:
        """Adjust agent parameters."""
        import random
        if hasattr(agent, 'state'):
            for key in agent.state:
                if isinstance(agent.state[key], float):
                    agent.state[key] *= random.uniform(0.8, 1.2)
        return agent

    async def _modify_capabilities(self, agent: Any) -> Any:
        """Modify agent capabilities."""
        if hasattr(agent, 'capabilities'):
            await agent.register_capability(f"capability_{uuid.uuid4().hex[:8]}")
        return agent

    async def _change_learning_rate(self, agent: Any) -> Any:
        """Change agent learning rate."""
        if hasattr(agent, 'state'):
            agent.state['learning_rate'] = agent.state.get('learning_rate', 0.1) * 1.1
        return agent

    async def _shift_strategy(self, agent: Any) -> Any:
        """Shift agent strategy."""
        strategies = [
            "aggressive",
            "conservative",
            "balanced",
            "exploratory"
        ]
        import random
        if hasattr(agent, 'strategy'):
            agent.strategy = random.choice(strategies)
        return agent


class AgentPopulation:
    """Manages a population of agents."""

    def __init__(
        self,
        population_size: int = 20,
        selection_strategy: SelectionStrategy = SelectionStrategy.TOURNAMENT
    ):
        self.population_size = population_size
        self.selection_strategy = selection_strategy
        self.agents: List[Any] = []
        self.fitness_scores: Dict[str, float] = {}
        self.generation: int = 0
        self.history: List[Dict[str, Any]] = []

    async def initialize(self, agent_factory: Callable) -> None:
        """Initialize population with agents."""
        self.agents = [agent_factory() for _ in range(self.population_size)]

    async def evaluate(self, evaluator: Callable) -> None:
        """Evaluate fitness of all agents."""
        self.fitness_scores = {}
        for agent in self.agents:
            fitness = await evaluator(agent)
            self.fitness_scores[agent.agent_id] = fitness

    async def select(self, count: int) -> List[Any]:
        """Select agents using configured strategy."""
        if self.selection_strategy == SelectionStrategy.ELITE:
            return await self._select_elite(count)
        elif self.selection_strategy == SelectionStrategy.TOURNAMENT:
            return await self._select_tournament(count)
        elif self.selection_strategy == SelectionStrategy.ROULETTE:
            return await self._select_roulette(count)
        elif self.selection_strategy == SelectionStrategy.RANK:
            return await self._select_rank(count)
        return []

    async def _select_elite(self, count: int) -> List[Any]:
        """Select top performers."""
        sorted_agents = sorted(
            self.agents,
            key=lambda a: self.fitness_scores.get(a.agent_id, 0),
            reverse=True
        )
        return sorted_agents[:count]

    async def _select_tournament(self, count: int) -> List[Any]:
        """Tournament selection."""
        import random
        selected = []
        for _ in range(count):
            tournament = random.sample(self.agents, min(3, len(self.agents)))
            winner = max(
                tournament,
                key=lambda a: self.fitness_scores.get(a.agent_id, 0)
            )
            selected.append(winner)
        return selected

    async def _select_roulette(self, count: int) -> List[Any]:
        """Fitness-proportionate roulette selection."""
        import random
        fitness_values = list(self.fitness_scores.values())
        total_fitness = sum(max(0, f) for f in fitness_values)

        if total_fitness <= 0:
            return random.sample(self.agents, count)

        selected = []
        for _ in range(count):
            pick = random.uniform(0, total_fitness)
            current = 0
            for agent in self.agents:
                current += max(0, self.fitness_scores.get(agent.agent_id, 0))
                if current > pick:
                    selected.append(agent)
                    break
        return selected

    async def _select_rank(self, count: int) -> List[Any]:
        """Rank-based selection."""
        sorted_agents = sorted(
            self.agents,
            key=lambda a: self.fitness_scores.get(a.agent_id, 0),
            reverse=True
        )
        # Bias toward higher ranks
        weights = [len(self.agents) - i for i in range(len(self.agents))]
        import random
        return random.choices(sorted_agents, weights=weights, k=count)

    def get_best_agent(self) -> Optional[Any]:
        """Get best agent in population."""
        if not self.agents:
            return None
        return max(
            self.agents,
            key=lambda a: self.fitness_scores.get(a.agent_id, 0)
        )

    def get_population_stats(self) -> Dict[str, Any]:
        """Get population statistics."""
        if not self.fitness_scores:
            return {}

        scores = list(self.fitness_scores.values())
        return {
            "size": len(self.agents),
            "best_fitness": max(scores),
            "worst_fitness": min(scores),
            "average_fitness": sum(scores) / len(scores),
            "generation": self.generation
        }


class MultiAgentOrchestrator:
    """
    Orchestrates multiple agent populations with co-evolution.
    Enables complex multi-population evolutionary dynamics.
    """

    def __init__(self, num_populations: int = 3):
        self.num_populations = num_populations
        self.populations: List[AgentPopulation] = []
        self.reproduction_operator = ReproductionOperator()
        self.mutation_operator = MutationOperator()
        self.interaction_history: List[Dict[str, Any]] = []
        self.global_best_agent: Optional[Any] = None
        self.global_best_fitness: float = -float('inf')

    async def initialize(
        self,
        agent_factories: List[Callable],
        population_sizes: Optional[List[int]] = None
    ) -> None:
        """Initialize multiple agent populations."""
        if len(agent_factories) != self.num_populations:
            raise ValueError(
                f"Expected {self.num_populations} factories, "
                f"got {len(agent_factories)}"
            )

        sizes = population_sizes or [20] * self.num_populations

        for i, factory in enumerate(agent_factories):
            pop = AgentPopulation(population_size=sizes[i])
            await pop.initialize(factory)
            self.populations.append(pop)

    async def evolve_populations(
        self,
        evaluators: List[Callable],
        num_generations: int = 50
    ) -> Dict[str, Any]:
        """
        Evolve multiple populations with co-evolution.
        Populations can interact and influence each other.
        """
        for gen in range(num_generations):
            # Evaluate each population
            for pop, evaluator in zip(self.populations, evaluators):
                await pop.evaluate(evaluator)
                await self._update_global_best(pop)

            # Allow inter-population interactions
            await self._facilitate_interactions()

            # Evolve each population
            for pop in self.populations:
                await self._evolve_population(pop)

            # Allow context switching
            await asyncio.sleep(0)

        return self.get_orchestration_status()

    async def _update_global_best(self, population: AgentPopulation) -> None:
        """Update global best agent across populations."""
        best_in_pop = population.get_best_agent()
        if best_in_pop:
            best_fitness = population.fitness_scores.get(best_in_pop.agent_id, 0)
            if best_fitness > self.global_best_fitness:
                self.global_best_fitness = best_fitness
                self.global_best_agent = best_in_pop

    async def _facilitate_interactions(self) -> None:
        """Facilitate interactions between populations."""
        if len(self.populations) < 2:
            return

        # Each population learns from global best
        for pop in self.populations:
            if self.global_best_agent and hasattr(self.global_best_agent, 'transfer_knowledge'):
                worst_agent = min(
                    pop.agents,
                    key=lambda a: pop.fitness_scores.get(a.agent_id, 0)
                )
                await self.global_best_agent.transfer_knowledge(worst_agent)

        self.interaction_history.append({
            "timestamp": datetime.utcnow(),
            "global_best_fitness": self.global_best_fitness,
            "num_interactions": len(self.populations)
        })

    async def _evolve_population(self, population: AgentPopulation) -> None:
        """Evolve a single population."""
        # Select elite
        elite_size = max(1, int(population.population_size * 0.1))
        elite = await population.select(elite_size)

        # Create offspring
        offspring = []
        while len(offspring) < population.population_size - elite_size:
            if len(elite) >= 2:
                parent1, parent2 = elite[0], elite[1] if len(elite) > 1 else elite[0]
                child1, child2 = await self.reproduction_operator.crossover(parent1, parent2)
                offspring.extend([child1, child2])
            else:
                parent = elite[0] if elite else population.agents[0]
                child = await self.mutation_operator.apply_mutation(parent)
                offspring.append(child)

        # Update population
        population.agents = elite + offspring[:population.population_size - elite_size]
        population.generation += 1

    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status."""
        stats = []
        for i, pop in enumerate(self.populations):
            stats.append({
                "population": i,
                "stats": pop.get_population_stats()
            })

        return {
            "num_populations": len(self.populations),
            "global_best_fitness": self.global_best_fitness,
            "population_stats": stats,
            "interactions": len(self.interaction_history),
            "timestamp": datetime.utcnow()
        }
