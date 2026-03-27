#!/usr/bin/env python3
"""
PHASE 6A: MULTI-AGENT EVOLUTIONARY SYSTEM
Competitive co-evolutionary training with speciation
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional, Callable
from enum import Enum
from datetime import datetime
import statistics


# ════════════════════════════════════════════════════════════════════════════
# EVOLUTIONARY AGENTS & GENOMES
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class Gene:
    """Single gene in an agent's genome"""
    name: str
    value: float
    min_val: float = 0.0
    max_val: float = 1.0
    mutation_rate: float = 0.1
    
    async def mutate(self) -> float:
        """Apply mutation to gene"""
        if random.random() < self.mutation_rate:
            # Gaussian mutation
            delta = random.gauss(0, self.mutation_rate)
            new_value = max(self.min_val, min(self.max_val, self.value + delta))
            return new_value
        return self.value


@dataclass
class Genome:
    """Complete genome for an agent"""
    genes: Dict[str, Gene]
    fitness: float = 0.0
    age: int = 0
    generation: int = 0
    
    async def mutate(self) -> 'Genome':
        """Create mutated copy of genome"""
        new_genes = {}
        for name, gene in self.genes.items():
            new_value = await gene.mutate()
            new_genes[name] = Gene(
                name=name,
                value=new_value,
                min_val=gene.min_val,
                max_val=gene.max_val,
                mutation_rate=gene.mutation_rate
            )
        
        return Genome(
            genes=new_genes,
            fitness=0.0,
            age=0,
            generation=self.generation + 1
        )
    
    async def crossover(self, other: 'Genome') -> 'Genome':
        """Blend two genomes (uniform crossover)"""
        new_genes = {}
        for name, gene in self.genes.items():
            other_gene = other.genes.get(name)
            if other_gene and random.random() < 0.5:
                new_genes[name] = Gene(
                    name=name,
                    value=other_gene.value,
                    min_val=gene.min_val,
                    max_val=gene.max_val,
                    mutation_rate=gene.mutation_rate
                )
            else:
                new_genes[name] = Gene(
                    name=name,
                    value=gene.value,
                    min_val=gene.min_val,
                    max_val=gene.max_val,
                    mutation_rate=gene.mutation_rate
                )
        
        return Genome(
            genes=new_genes,
            fitness=0.0,
            age=0,
            generation=max(self.generation, other.generation) + 1
        )


class AgentRole(Enum):
    """Role in the ecosystem"""
    PREDATOR = "predator"      # Hunters
    PREY = "prey"              # Hunted
    BUILDER = "builder"        # Tool makers
    SCOUT = "scout"            # Explorers
    COOPERATOR = "cooperator"  # Team players


@dataclass
class CoEvolutionaryAgent:
    """Single agent in co-evolutionary population"""
    agent_id: str
    genome: Genome
    role: AgentRole
    interactions: Dict[str, int] = field(default_factory=dict)
    wins: int = 0
    losses: int = 0
    fitness_history: List[float] = field(default_factory=list)
    
    async def compete(self, opponent: 'CoEvolutionaryAgent') -> Tuple[bool, float]:
        """Compete against another agent"""
        # Fitness comparison with noise
        self_fitness = self.genome.fitness + random.gauss(0, 0.05)
        opp_fitness = opponent.genome.fitness + random.gauss(0, 0.05)
        
        # Account for roles
        role_bonus = {
            AgentRole.PREDATOR: 0.15,
            AgentRole.BUILDER: 0.10,
            AgentRole.COOPERATOR: 0.05,
            AgentRole.SCOUT: 0.05,
        }
        
        self_fitness += role_bonus.get(self.role, 0)
        
        self_wins = self_fitness > opp_fitness
        reward = abs(self_fitness - opp_fitness)
        
        if self_wins:
            self.wins += 1
        else:
            self.losses += 1
        
        # Track interaction
        opponent_id = opponent.agent_id
        self.interactions[opponent_id] = self.interactions.get(opponent_id, 0) + 1
        
        return self_wins, reward
    
    async def update_fitness(self, reward: float) -> None:
        """Update fitness based on competition"""
        # Weighted moving average
        alpha = 0.3
        win_rate = self.wins / (self.wins + self.losses) if (self.wins + self.losses) > 0 else 0
        self.genome.fitness = alpha * (reward + win_rate) + (1 - alpha) * self.genome.fitness
        self.fitness_history.append(self.genome.fitness)


# ════════════════════════════════════════════════════════════════════════════
# POPULATION & SPECIATION
# ════════════════════════════════════════════════════════════════════════════

class Species:
    """Group of similar agents"""
    
    def __init__(self, species_id: str, representative: CoEvolutionaryAgent):
        self.species_id = species_id
        self.representative = representative
        self.members: List[CoEvolutionaryAgent] = [representative]
        self.generation_created = 0
        self.age = 0
        self.best_fitness = representative.genome.fitness
    
    async def distance_to(self, agent: CoEvolutionaryAgent) -> float:
        """Calculate genetic distance"""
        distance = 0.0
        for gene_name, gene in self.representative.genome.genes.items():
            other_gene = agent.genome.genes.get(gene_name)
            if other_gene:
                distance += abs(gene.value - other_gene.value) ** 2
        return distance ** 0.5
    
    async def add_member(self, agent: CoEvolutionaryAgent) -> None:
        """Add agent to species"""
        self.members.append(agent)
        if agent.genome.fitness > self.best_fitness:
            self.best_fitness = agent.genome.fitness
    
    async def get_avg_fitness(self) -> float:
        """Get average fitness"""
        if not self.members:
            return 0.0
        return sum(m.genome.fitness for m in self.members) / len(self.members)


class CoEvolutionaryPopulation:
    """Population with speciation"""
    
    def __init__(self, pop_size: int = 100, distance_threshold: float = 0.5):
        self.pop_size = pop_size
        self.distance_threshold = distance_threshold
        self.population: List[CoEvolutionaryAgent] = []
        self.species: List[Species] = []
        self.generation = 0
        self.history: List[Dict[str, Any]] = []
    
    async def initialize_population(self) -> None:
        """Initialize random population"""
        self.population = []
        
        for i in range(self.pop_size):
            genes = {
                'strength': Gene('strength', random.random(), 0, 1, 0.1),
                'speed': Gene('speed', random.random(), 0, 1, 0.1),
                'intelligence': Gene('intelligence', random.random(), 0, 1, 0.1),
                'cooperation': Gene('cooperation', random.random(), 0, 1, 0.1),
                'aggression': Gene('aggression', random.random(), 0, 1, 0.1),
            }
            
            genome = Genome(genes=genes, fitness=random.random() * 0.5, generation=0)
            role = random.choice(list(AgentRole))
            
            agent = CoEvolutionaryAgent(
                agent_id=f"agent_{i:04d}",
                genome=genome,
                role=role
            )
            
            self.population.append(agent)
    
    async def speciate(self) -> None:
        """Assign agents to species"""
        self.species = []
        unspeciated = set(range(len(self.population)))
        
        for idx in list(unspeciated):
            if idx not in unspeciated:
                continue
            
            # Create new species
            agent = self.population[idx]
            species = Species(f"species_{len(self.species):03d}", agent)
            
            unspeciated.remove(idx)
            
            # Find compatible agents
            compatible = []
            for other_idx in list(unspeciated):
                other = self.population[other_idx]
                distance = await species.distance_to(other)
                if distance < self.distance_threshold:
                    compatible.append((other_idx, distance))
            
            # Add compatible agents
            for other_idx, _ in sorted(compatible, key=lambda x: x[1])[:10]:
                other = self.population[other_idx]
                await species.add_member(other)
                unspeciated.remove(other_idx)
            
            self.species.append(species)
    
    async def select_parents(self) -> Tuple[CoEvolutionaryAgent, CoEvolutionaryAgent]:
        """Tournament selection"""
        tournament_size = 3
        
        # Select from best
        sorted_pop = sorted(self.population, key=lambda a: a.genome.fitness, reverse=True)
        parent1 = min(random.sample(sorted_pop[:10], min(tournament_size, 10)), 
                      key=lambda a: a.genome.fitness)
        parent2 = min(random.sample(sorted_pop[:10], min(tournament_size, 10)),
                      key=lambda a: a.genome.fitness)
        
        return parent1, parent2
    
    async def generate_offspring(self, parent1: CoEvolutionaryAgent, 
                                 parent2: CoEvolutionaryAgent) -> CoEvolutionaryAgent:
        """Create offspring from two parents"""
        # Crossover
        child_genome = await parent1.genome.crossover(parent2.genome)
        
        # Mutation
        child_genome = await child_genome.mutate()
        
        # Create new agent
        child_role = parent1.role if random.random() < 0.6 else parent2.role
        child = CoEvolutionaryAgent(
            agent_id=f"offspring_{self.generation:04d}_{len(self.population):04d}",
            genome=child_genome,
            role=child_role
        )
        
        return child
    
    async def evolve_generation(self) -> None:
        """Evolve one generation"""
        # Speciate current population
        await self.speciate()
        
        # Create new population
        new_population = []
        
        # Preserve best from each species
        for species in self.species:
            best_in_species = max(species.members, key=lambda a: a.genome.fitness)
            new_population.append(best_in_species)
        
        # Generate offspring to fill population
        while len(new_population) < self.pop_size:
            parent1, parent2 = await self.select_parents()
            child = await self.generate_offspring(parent1, parent2)
            new_population.append(child)
        
        # Update population
        self.population = new_population[:self.pop_size]
        
        # Record history
        avg_fitness = statistics.mean(a.genome.fitness for a in self.population)
        best_fitness = max(a.genome.fitness for a in self.population)
        
        self.history.append({
            'generation': self.generation,
            'avg_fitness': avg_fitness,
            'best_fitness': best_fitness,
            'species_count': len(self.species),
        })
        
        self.generation += 1
    
    async def get_population_stats(self) -> Dict[str, Any]:
        """Get population statistics"""
        fitnesses = [a.genome.fitness for a in self.population]
        
        return {
            'generation': self.generation,
            'population_size': len(self.population),
            'species_count': len(self.species),
            'best_fitness': max(fitnesses),
            'avg_fitness': statistics.mean(fitnesses),
            'stdev_fitness': statistics.stdev(fitnesses) if len(fitnesses) > 1 else 0,
            'best_agent': max(self.population, key=lambda a: a.genome.fitness).agent_id,
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_coevolution():
    """Demonstrate co-evolutionary training"""
    
    print("\n" + "=" * 70)
    print("MULTI-AGENT CO-EVOLUTIONARY SYSTEM - PHASE 6A")
    print("=" * 70)
    
    population = CoEvolutionaryPopulation(pop_size=50, distance_threshold=0.3)
    
    # Initialize
    print("\n[Init] Initializing population...")
    await population.initialize_population()
    print(f"  Created {len(population.population)} agents")
    
    # Run evolution
    print("\n[Evolution] Running generations...")
    for gen in range(5):
        # Competition phase
        for i in range(10):  # 10 competition rounds per generation
            agent1 = random.choice(population.population)
            agent2 = random.choice(population.population)
            
            if agent1 != agent2:
                won, reward = await agent1.compete(agent2)
                await agent1.update_fitness(reward)
                
                # Update opponent
                if not won:
                    await agent2.update_fitness(reward * 0.5)  # Partial reward for loss
        
        # Evolution phase
        await population.evolve_generation()
        
        # Report
        stats = await population.get_population_stats()
        print(f"  Gen {gen:2d}: Best={stats['best_fitness']:.3f}, "
              f"Avg={stats['avg_fitness']:.3f}, Species={stats['species_count']}")
    
    # Final statistics
    print("\n[Statistics] Final Population Stats:")
    stats = await population.get_population_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # Show speciation
    print("\n[Species] Final Speciation:")
    for i, species in enumerate(population.species):
        avg_fit = await species.get_avg_fitness()
        print(f"  Species {i}: {len(species.members)} members, avg fitness {avg_fit:.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_coevolution())
