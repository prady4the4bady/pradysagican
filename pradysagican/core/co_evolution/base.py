"""
Multi-Agent Evolution (MAE) Framework and Tool-R0 Base Classes
===============================================================

Core classes for agent co-evolution in PRADYSAGICAN Phase 6.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, Set, Tuple
from enum import Enum
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime, timezone
import uuid


class EvolutionStrategy(Enum):
    """Evolution strategy types."""
    GENETIC_ALGORITHM = "genetic_algorithm"
    PARTICLE_SWARM = "particle_swarm"
    DIFFERENTIAL_EVOLUTION = "differential_evolution"
    COOPERATIVE_COEVOLUTION = "cooperative_coevolution"


@dataclass
class EvolutionMetrics:
    """Metrics tracking agent evolution."""
    generation: int
    population_size: int
    best_fitness: float
    average_fitness: float
    worst_fitness: float
    diversity_score: float
    convergence_rate: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_converged(self, threshold: float = 0.95) -> bool:
        """Check if population has converged."""
        return self.convergence_rate >= threshold

    def is_diverse(self, threshold: float = 0.3) -> bool:
        """Check if population maintains diversity."""
        return self.diversity_score >= threshold


@dataclass
class AgentGeneration:
    """Represents a generation of agents."""
    generation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agents: List[Any] = field(default_factory=list)
    fitness_scores: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    parent_generation_id: Optional[str] = None
    evolution_strategy: str = "genetic_algorithm"

    def get_best_agent_id(self) -> Optional[str]:
        """Get ID of best-performing agent."""
        if not self.fitness_scores:
            return None
        return max(self.fitness_scores, key=self.fitness_scores.get)

    def get_average_fitness(self) -> float:
        """Calculate average fitness."""
        if not self.fitness_scores:
            return 0.0
        return sum(self.fitness_scores.values()) / len(self.fitness_scores)


@dataclass
class CoEvolutionContext:
    """Context for agent co-evolution."""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    shared_knowledge: Dict[str, Any] = field(default_factory=dict)
    global_constraints: Dict[str, Any] = field(default_factory=dict)
    performance_history: List[EvolutionMetrics] = field(default_factory=list)
    agent_interactions: Dict[str, List[str]] = field(default_factory=dict)
    environment_state: Dict[str, Any] = field(default_factory=dict)

    async def update_shared_knowledge(self, key: str, value: Any) -> None:
        """Update shared knowledge pool."""
        self.shared_knowledge[key] = {
            "value": value,
            "timestamp": datetime.now(timezone.utc),
            "version": self.shared_knowledge.get(key, {}).get("version", 0) + 1
        }

    def record_performance(self, metrics: EvolutionMetrics) -> None:
        """Record generation performance."""
        self.performance_history.append(metrics)


class ToolR0Agent(ABC):
    """
    Tool-R0: Recursive tool-building agent base class.
    Implements co-evolution primitives for self-improvement.
    """

    def __init__(self, agent_id: Optional[str] = None):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.generation: int = 0
        self.fitness: float = 0.0
        self.capabilities: Set[str] = set()
        self.learned_patterns: List[Dict[str, Any]] = []
        self.parent_agents: List[str] = []
        self.tool_registry: Dict[str, Callable] = {}
        self.state: Dict[str, Any] = {}
        self.evolution_log: List[Dict[str, Any]] = []

    @abstractmethod
    async def evaluate_fitness(self) -> float:
        """Evaluate agent fitness. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def mutate(self, mutation_rate: float = 0.1) -> 'ToolR0Agent':
        """Apply mutations for evolution. Must be implemented by subclasses."""
        pass

    @abstractmethod
    async def cross_over(self, other: 'ToolR0Agent') -> Tuple['ToolR0Agent', 'ToolR0Agent']:
        """Perform crossover with another agent. Must be implemented by subclasses."""
        pass

    async def build_tool(self, tool_spec: Dict[str, Any]) -> Callable:
        """
        Recursively build a new tool based on specification.
        This is the core Tool-R0 capability.
        """
        tool_id = tool_spec.get("id", str(uuid.uuid4()))
        tool_type = tool_spec.get("type", "generic")

        async def tool_function(*args, **kwargs) -> Any:
            """Generated tool function."""
            return {
                "tool_id": tool_id,
                "tool_type": tool_type,
                "args": args,
                "kwargs": kwargs,
                "timestamp": datetime.now(timezone.utc),
                "agent_id": self.agent_id
            }

        self.tool_registry[tool_id] = tool_function
        self.learned_patterns.append(tool_spec)
        return tool_function

    async def register_capability(self, capability_name: str) -> None:
        """Register a new capability."""
        self.capabilities.add(capability_name)
        self.evolution_log.append({
            "action": "capability_added",
            "capability": capability_name,
            "timestamp": datetime.now(timezone.utc)
        })

    async def transfer_knowledge(self, target_agent: 'ToolR0Agent') -> None:
        """Transfer learned patterns to another agent."""
        target_agent.learned_patterns.extend(self.learned_patterns)
        target_agent.parent_agents.append(self.agent_id)

    def get_evolution_summary(self) -> Dict[str, Any]:
        """Get summary of agent evolution."""
        return {
            "agent_id": self.agent_id,
            "generation": self.generation,
            "fitness": self.fitness,
            "capabilities": list(self.capabilities),
            "tools_built": len(self.tool_registry),
            "patterns_learned": len(self.learned_patterns),
            "parents": self.parent_agents,
            "evolution_events": len(self.evolution_log)
        }


class MAEFramework(ABC):
    """
    Multi-Agent Evolution Framework.
    Orchestrates evolution of multiple agents with co-evolution support.
    """

    def __init__(
        self,
        strategy: EvolutionStrategy = EvolutionStrategy.GENETIC_ALGORITHM,
        population_size: int = 20,
        max_generations: int = 100,
        elite_rate: float = 0.1
    ):
        self.strategy = strategy
        self.population_size = population_size
        self.max_generations = max_generations
        self.elite_rate = elite_rate
        self.current_generation: Optional[AgentGeneration] = None
        self.generation_history: List[AgentGeneration] = []
        self.evolution_context: Optional[CoEvolutionContext] = None
        self.metrics_history: List[EvolutionMetrics] = []
        self.is_running = False

    async def initialize_population(self, agent_factory: Callable) -> None:
        """Initialize agent population."""
        agents = [agent_factory() for _ in range(self.population_size)]
        self.current_generation = AgentGeneration(
            agents=agents,
            evolution_strategy=self.strategy.value
        )
        self.evolution_context = CoEvolutionContext()

    async def evaluate_fitness(self) -> None:
        """Evaluate fitness of all agents in current generation."""
        if not self.current_generation:
            return

        fitness_scores = {}
        for agent in self.current_generation.agents:
            fitness = await agent.evaluate_fitness()
            fitness_scores[agent.agent_id] = fitness

        self.current_generation.fitness_scores = fitness_scores

    async def select_elite(self) -> List[Any]:
        """Select elite agents for next generation."""
        if not self.current_generation:
            return []

        elite_count = max(1, int(self.population_size * self.elite_rate))
        sorted_agents = sorted(
            self.current_generation.agents,
            key=lambda a: self.current_generation.fitness_scores.get(a.agent_id, 0),
            reverse=True
        )
        return sorted_agents[:elite_count]

    async def create_next_generation(self) -> None:
        """Create next generation through selection and reproduction."""
        elite = await self.select_elite()
        offspring = []

        while len(offspring) < self.population_size - len(elite):
            if len(elite) >= 2 and self._should_crossover():
                parent1, parent2 = self._select_parents(elite, 2)
                child1, child2 = await parent1.cross_over(parent2)
                offspring.extend([child1, child2])
            else:
                parent = self._select_parents(elite, 1)[0]
                child = await parent.mutate()
                offspring.append(child)

        self.current_generation.agents = elite + offspring[:self.population_size - len(elite)]

    async def run_evolution(self, num_generations: Optional[int] = None) -> EvolutionMetrics:
        """Run evolution for specified generations."""
        self.is_running = True
        generations_to_run = num_generations or self.max_generations

        try:
            for gen in range(generations_to_run):
                await self.evaluate_fitness()
                metrics = await self._compute_metrics()
                self.metrics_history.append(metrics)

                if self.evolution_context:
                    self.evolution_context.record_performance(metrics)

                if metrics.is_converged():
                    break

                await self.create_next_generation()
                self.generation_history.append(self.current_generation)

                # Allow for context switching
                await asyncio.sleep(0)

            return self.metrics_history[-1] if self.metrics_history else None
        finally:
            self.is_running = False

    async def _compute_metrics(self) -> EvolutionMetrics:
        """Compute evolution metrics for current generation."""
        if not self.current_generation:
            return EvolutionMetrics(0, 0, 0, 0, 0, 0, 0)

        fitness_scores = self.current_generation.fitness_scores.values()
        if not fitness_scores:
            return EvolutionMetrics(0, 0, 0, 0, 0, 0, 0)

        scores_list = list(fitness_scores)
        diversity = self._calculate_diversity(scores_list)

        return EvolutionMetrics(
            generation=len(self.generation_history),
            population_size=len(self.current_generation.agents),
            best_fitness=max(scores_list),
            average_fitness=sum(scores_list) / len(scores_list),
            worst_fitness=min(scores_list),
            diversity_score=diversity,
            convergence_rate=1.0 - diversity
        )

    def _should_crossover(self, crossover_rate: float = 0.7) -> bool:
        """Determine if crossover should occur."""
        import random
        return random.random() < crossover_rate

    def _select_parents(self, population: List[Any], count: int) -> List[Any]:
        """Select parents from population (tournament selection)."""
        import random
        return [random.choice(population) for _ in range(count)]

    def _calculate_diversity(self, fitness_scores: List[float]) -> float:
        """Calculate population diversity."""
        if len(fitness_scores) < 2:
            return 0.0
        mean = sum(fitness_scores) / len(fitness_scores)
        variance = sum((x - mean) ** 2 for x in fitness_scores) / len(fitness_scores)
        # Normalize to [0, 1]
        return min(1.0, variance / (mean + 1e-6))

    def get_evolution_status(self) -> Dict[str, Any]:
        """Get current evolution status."""
        return {
            "is_running": self.is_running,
            "strategy": self.strategy.value,
            "generations_completed": len(self.generation_history),
            "current_metrics": self.metrics_history[-1] if self.metrics_history else None,
            "population_size": self.population_size,
            "history_size": len(self.generation_history)
        }
