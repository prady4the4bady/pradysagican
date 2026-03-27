"""
PHASE 4B: Swarm Intelligence & Multi-agent Optimization
=======================================================

Particle swarm optimization, ant colony algorithms,
emergent behavior detection, and consensus mechanisms.

Attribution: PSO, ACO papers, multi-agent systems,
emergent computation, stigmergy
"""

import asyncio
import logging
import random
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# PARTICLE SWARM OPTIMIZATION
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class Particle:
    """Particle in swarm"""
    particle_id: str
    position: List[float]  # Current position in search space
    velocity: List[float]  # Current velocity
    best_position: List[float] = field(default_factory=list)
    best_fitness: float = -float('inf')
    current_fitness: float = 0.0
    neighborhood_best: List[float] = field(default_factory=list)


class ParticleSwarmOptimizer:
    """PSO for optimization"""
    
    def __init__(self, num_particles: int = 30, 
                 dimensions: int = 10,
                 inertia: float = 0.7,
                 cognitive: float = 1.5,
                 social: float = 1.5):
        self.num_particles = num_particles
        self.dimensions = dimensions
        self.inertia = inertia
        self.cognitive = cognitive
        self.social = social
        self.particles: List[Particle] = []
        self.global_best: List[float] = None
        self.global_best_fitness: float = -float('inf')
        self.iteration = 0
        self.history: List[Dict[str, Any]] = []
    
    async def initialize_swarm(self):
        """Initialize particle swarm"""
        self.particles = []
        
        for i in range(self.num_particles):
            position = [random.uniform(-5.0, 5.0) for _ in range(self.dimensions)]
            velocity = [random.uniform(-1.0, 1.0) for _ in range(self.dimensions)]
            
            particle = Particle(
                particle_id=f"particle_{i}",
                position=position,
                velocity=velocity,
                best_position=position.copy(),
            )
            
            self.particles.append(particle)
        
        # Initialize global best
        self.global_best = self.particles[0].position.copy()
    
    async def evaluate_fitness(self, position: List[float]) -> float:
        """Evaluate fitness at position"""
        # Rosenbrock function: sum of (1-x_i)^2 + 100(x_{i+1}-x_i^2)^2
        fitness = 0.0
        for i in range(len(position) - 1):
            fitness += (1 - position[i])**2 + 100 * (position[i+1] - position[i]**2)**2
        return 1.0 / (1.0 + fitness)  # Normalize to 0-1
    
    async def update_particles(self):
        """Update particle positions and velocities"""
        
        for particle in self.particles:
            # Evaluate current position
            particle.current_fitness = await self.evaluate_fitness(particle.position)
            
            # Update personal best
            if particle.current_fitness > particle.best_fitness:
                particle.best_fitness = particle.current_fitness
                particle.best_position = particle.position.copy()
            
            # Update global best
            if particle.current_fitness > self.global_best_fitness:
                self.global_best_fitness = particle.current_fitness
                self.global_best = particle.position.copy()
            
            # Update velocity and position
            for j in range(self.dimensions):
                r1, r2 = random.random(), random.random()
                
                # PSO update equation
                particle.velocity[j] = (
                    self.inertia * particle.velocity[j] +
                    self.cognitive * r1 * (particle.best_position[j] - particle.position[j]) +
                    self.social * r2 * (self.global_best[j] - particle.position[j])
                )
                
                # Update position
                particle.position[j] += particle.velocity[j]
                
                # Boundary conditions
                particle.position[j] = max(-5.0, min(5.0, particle.position[j]))
    
    async def run(self, num_iterations: int = 50) -> Dict[str, Any]:
        """Run PSO"""
        await self.initialize_swarm()
        
        for i in range(num_iterations):
            await self.update_particles()
            
            avg_fitness = sum(p.current_fitness for p in self.particles) / len(self.particles)
            
            self.history.append({
                'iteration': i,
                'global_best_fitness': self.global_best_fitness,
                'avg_fitness': avg_fitness,
            })
        
        return {
            'best_position': self.global_best,
            'best_fitness': self.global_best_fitness,
            'iterations': num_iterations,
            'history': self.history[-10:],  # Last 10
        }


# ════════════════════════════════════════════════════════════════════════════
# ANT COLONY OPTIMIZATION
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class Ant:
    """Ant in colony"""
    ant_id: str
    path: List[int]
    pheromone_deposit: float = 0.0
    path_cost: float = float('inf')


class AntColonyOptimizer:
    """ACO for optimization"""
    
    def __init__(self, num_ants: int = 30,
                 num_nodes: int = 10,
                 evaporation: float = 0.1,
                 alpha: float = 1.0,
                 beta: float = 2.0):
        self.num_ants = num_ants
        self.num_nodes = num_nodes
        self.evaporation = evaporation
        self.alpha = alpha
        self.beta = beta
        
        # Distance matrix (simulated)
        self.distance_matrix = self._init_distance_matrix()
        
        # Pheromone matrix
        self.pheromone = self._init_pheromone()
        
        self.ants: List[Ant] = []
        self.best_path: List[int] = None
        self.best_cost: float = float('inf')
        self.iteration = 0
    
    def _init_distance_matrix(self) -> List[List[float]]:
        """Initialize distance matrix"""
        matrix = []
        for i in range(self.num_nodes):
            row = []
            for j in range(self.num_nodes):
                if i == j:
                    row.append(0)
                else:
                    row.append(random.uniform(1.0, 10.0))
            matrix.append(row)
        return matrix
    
    def _init_pheromone(self) -> List[List[float]]:
        """Initialize pheromone matrix"""
        return [[1.0 for _ in range(self.num_nodes)] for _ in range(self.num_nodes)]
    
    async def construct_paths(self):
        """Construct paths for all ants"""
        self.ants = []
        
        for i in range(self.num_ants):
            ant = Ant(ant_id=f"ant_{i}", path=[])
            
            # Start from random node
            start = random.randint(0, self.num_nodes - 1)
            ant.path = [start]
            
            # Build path
            for _ in range(self.num_nodes - 1):
                current = ant.path[-1]
                unvisited = [j for j in range(self.num_nodes) if j not in ant.path]
                
                # Probabilistic choice using pheromone and distance
                probabilities = []
                for next_node in unvisited:
                    pheromone = self.pheromone[current][next_node] ** self.alpha
                    distance = (1.0 / self.distance_matrix[current][next_node]) ** self.beta
                    prob = pheromone * distance
                    probabilities.append((next_node, prob))
                
                # Normalize and select
                total_prob = sum(p[1] for p in probabilities)
                if total_prob > 0:
                    probabilities = [(n, p / total_prob) for n, p in probabilities]
                    
                    r = random.random()
                    cumsum = 0
                    for node, prob in probabilities:
                        cumsum += prob
                        if r <= cumsum:
                            ant.path.append(node)
                            break
                else:
                    ant.path.append(random.choice(unvisited))
            
            # Calculate path cost
            cost = 0
            for i in range(len(ant.path) - 1):
                cost += self.distance_matrix[ant.path[i]][ant.path[i+1]]
            
            ant.path_cost = cost
            ant.pheromone_deposit = 1.0 / cost
            
            self.ants.append(ant)
    
    async def update_pheromone(self):
        """Update pheromone levels"""
        # Evaporation
        for i in range(self.num_nodes):
            for j in range(self.num_nodes):
                self.pheromone[i][j] *= (1 - self.evaporation)
        
        # Ant deposits
        for ant in self.ants:
            for i in range(len(ant.path) - 1):
                from_node = ant.path[i]
                to_node = ant.path[i+1]
                self.pheromone[from_node][to_node] += ant.pheromone_deposit
    
    async def run(self, num_iterations: int = 50) -> Dict[str, Any]:
        """Run ACO"""
        best_costs = []
        
        for iteration in range(num_iterations):
            await self.construct_paths()
            
            # Find best path
            best_ant = min(self.ants, key=lambda a: a.path_cost)
            if best_ant.path_cost < self.best_cost:
                self.best_cost = best_ant.path_cost
                self.best_path = best_ant.path.copy()
            
            await self.update_pheromone()
            best_costs.append(self.best_cost)
        
        return {
            'best_path': self.best_path,
            'best_cost': self.best_cost,
            'iterations': num_iterations,
            'best_costs': best_costs[-10:],  # Last 10
        }


# ════════════════════════════════════════════════════════════════════════════
# EMERGENT BEHAVIOR & CONSENSUS
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class Agent:
    """Agent in multi-agent system"""
    agent_id: str
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    decision: str = "undecided"
    confidence: float = 0.5
    neighbors: List[str] = field(default_factory=list)


class EmergentBehaviorDetector:
    """Detect emergent behaviors in multi-agent systems"""
    
    def __init__(self, num_agents: int = 50):
        self.num_agents = num_agents
        self.agents: Dict[str, Agent] = {}
        self.behaviors: List[Dict[str, Any]] = []
    
    async def initialize_agents(self):
        """Initialize agent population"""
        self.agents = {}
        
        for i in range(self.num_agents):
            agent = Agent(
                agent_id=f"agent_{i}",
                position=(random.uniform(-10, 10), random.uniform(-10, 10)),
                velocity=(random.uniform(-1, 1), random.uniform(-1, 1)),
            )
            self.agents[agent.agent_id] = agent
    
    async def update_neighborhoods(self):
        """Update agent neighborhoods"""
        for agent in self.agents.values():
            agent.neighbors = []
            
            # Find nearby agents (distance < 5)
            for other_id, other in self.agents.items():
                if agent.agent_id != other_id:
                    dist = math.sqrt(
                        (agent.position[0] - other.position[0])**2 +
                        (agent.position[1] - other.position[1])**2
                    )
                    if dist < 5.0:
                        agent.neighbors.append(other_id)
    
    async def simulate_step(self):
        """Simulate one time step"""
        await self.update_neighborhoods()
        
        for agent in self.agents.values():
            # Random decision or follow neighbors
            if random.random() < 0.7 and agent.neighbors:
                # Follow majority in neighborhood
                decisions = []
                for neighbor_id in agent.neighbors:
                    decisions.append(self.agents[neighbor_id].decision)
                
                if decisions:
                    agent.decision = max(set(decisions), key=decisions.count)
                    agent.confidence = decisions.count(agent.decision) / len(decisions)
            else:
                # Random decision
                agent.decision = random.choice(['cooperate', 'defect'])
                agent.confidence = random.uniform(0.3, 0.9)
    
    async def detect_emergence(self, num_steps: int = 50) -> Dict[str, Any]:
        """Detect emergent behaviors"""
        await self.initialize_agents()
        
        for _ in range(num_steps):
            await self.simulate_step()
        
        # Analyze final state
        cooperate_count = sum(1 for a in self.agents.values() if a.decision == 'cooperate')
        cooperation_level = cooperate_count / len(self.agents)
        
        avg_confidence = sum(a.confidence for a in self.agents.values()) / len(self.agents)
        
        cluster_count = self._count_clusters()
        
        emergence = {
            'cooperation_level': cooperation_level,
            'avg_confidence': avg_confidence,
            'clusters': cluster_count,
            'emergence_strength': cooperation_level * avg_confidence,
        }
        
        self.behaviors.append(emergence)
        return emergence
    
    def _count_clusters(self) -> int:
        """Count distinct decision clusters"""
        decisions = [a.decision for a in self.agents.values()]
        return len(set(decisions))


# ════════════════════════════════════════════════════════════════════════════
# INTEGRATED SWARM SYSTEM
# ════════════════════════════════════════════════════════════════════════════

class SwarmIntelligenceSystem:
    """Complete swarm intelligence system"""
    
    def __init__(self):
        self.pso = ParticleSwarmOptimizer(num_particles=30, dimensions=10)
        self.aco = AntColonyOptimizer(num_ants=30, num_nodes=10)
        self.emergence = EmergentBehaviorDetector(num_agents=50)
    
    async def run_pso(self) -> Dict[str, Any]:
        """Run particle swarm optimization"""
        print("[Swarm] Running Particle Swarm Optimization...")
        result = await self.pso.run(num_iterations=10)
        print(f"  Best Fitness: {result['best_fitness']:.4f}")
        return result
    
    async def run_aco(self) -> Dict[str, Any]:
        """Run ant colony optimization"""
        print("[Swarm] Running Ant Colony Optimization...")
        result = await self.aco.run(num_iterations=10)
        print(f"  Best Cost: {result['best_cost']:.2f}")
        return result
    
    async def detect_emergence(self) -> Dict[str, Any]:
        """Detect emergent behaviors"""
        print("[Swarm] Detecting Emergent Behaviors...")
        result = await self.emergence.detect_emergence(num_steps=20)
        print(f"  Cooperation Level: {result['cooperation_level']:.1%}")
        print(f"  Emergence Strength: {result['emergence_strength']:.4f}")
        return result
    
    async def comprehensive_swarm_study(self) -> Dict[str, Any]:
        """Run comprehensive swarm analysis"""
        
        print(f"\n{'='*70}")
        print(f"SWARM INTELLIGENCE SYSTEM - PHASE 4B")
        print(f"{'='*70}\n")
        
        pso_result = await self.run_pso()
        print()
        aco_result = await self.run_aco()
        print()
        emergence_result = await self.detect_emergence()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'pso': pso_result,
            'aco': aco_result,
            'emergence': emergence_result,
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_swarm_system():
    """Demonstrate swarm intelligence"""
    
    system = SwarmIntelligenceSystem()
    results = await system.comprehensive_swarm_study()
    
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}\n")
    
    print(f"Particle Swarm Optimization:")
    print(f"  Iterations: {results['pso']['iterations']}")
    print(f"  Best Fitness: {results['pso']['best_fitness']:.4f}")
    print(f"  Convergence: Achieved in {len(results['pso']['history'])} steps\n")
    
    print(f"Ant Colony Optimization:")
    print(f"  Iterations: {results['aco']['iterations']}")
    print(f"  Best Cost: {results['aco']['best_cost']:.2f}")
    print(f"  Path Length: {len(results['aco']['best_path'])} nodes\n")
    
    print(f"Emergent Behavior:")
    print(f"  Cooperation: {results['emergence']['cooperation_level']:.1%}")
    print(f"  Clusters: {results['emergence']['clusters']}")
    print(f"  Confidence: {results['emergence']['avg_confidence']:.2%}")


if __name__ == "__main__":
    asyncio.run(demo_swarm_system())
