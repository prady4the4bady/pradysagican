#!/usr/bin/env python3
"""
PHASE 6D: SPECIATION & ADAPTIVE NICHES
Niche formation, adaptive trait tracking, extinction prevention
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional
from datetime import datetime, timedelta
from enum import Enum


class SpeciesStatus(Enum):
    """Status of a species"""
    ACTIVE = "active"
    DECLINING = "declining"
    RECOVERING = "recovering"
    EXTINCT = "extinct"


@dataclass
class Trait:
    """Individual trait"""
    trait_id: str
    trait_type: str
    value: float
    adaptation_pressure: float = 0.0
    usage_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AdaptiveOrganism:
    """Organism with adaptive traits"""
    organism_id: str
    species_id: str
    traits: Dict[str, Trait] = field(default_factory=dict)
    fitness: float = 0.0
    niche_position: Tuple[float, float] = (0.0, 0.0)
    generation_born: int = 0


class NicheFormation:
    """Manages niche detection and formation"""
    
    def __init__(self, num_niches_target: int = 5, niche_radius: float = 0.3):
        self.num_niches_target = num_niches_target
        self.niche_radius = niche_radius
        self.niches: List[Tuple[float, float]] = []
        self.niche_occupancy: Dict[int, int] = {}
    
    async def detect_niches(self, organisms: List[AdaptiveOrganism]) -> List[Tuple[float, float]]:
        """Detect distinct niches in population"""
        
        if not organisms:
            return []
        
        # Extract positions
        positions = [org.niche_position for org in organisms]
        
        # K-means style clustering
        niches = []
        clusters: Dict[int, List[Tuple[float, float]]] = {}
        
        # Initialize random centers
        random.shuffle(positions)
        for i in range(min(self.num_niches_target, len(positions))):
            niches.append(positions[i])
        
        # Iterate 3 times for convergence
        for iteration in range(3):
            clusters = {i: [] for i in range(len(niches))}
            
            # Assign organisms to nearest niche
            for pos in positions:
                min_dist = float('inf')
                nearest_niche = 0
                
                for i, niche_center in enumerate(niches):
                    dist = ((pos[0] - niche_center[0]) ** 2 + 
                           (pos[1] - niche_center[1]) ** 2) ** 0.5
                    if dist < min_dist:
                        min_dist = dist
                        nearest_niche = i
                
                clusters[nearest_niche].append(pos)
            
            # Update niche centers
            new_niches = []
            for i, positions_in_cluster in clusters.items():
                if positions_in_cluster:
                    avg_x = sum(p[0] for p in positions_in_cluster) / len(positions_in_cluster)
                    avg_y = sum(p[1] for p in positions_in_cluster) / len(positions_in_cluster)
                    new_niches.append((avg_x, avg_y))
            
            niches = new_niches
        
        self.niches = niches
        
        # Track occupancy
        self.niche_occupancy = {}
        for i, positions_in_cluster in clusters.items():
            self.niche_occupancy[i] = len(positions_in_cluster)
        
        return niches
    
    async def get_niche_diversity(self) -> float:
        """Get diversity across niches (0-1)"""
        
        if not self.niche_occupancy:
            return 0.0
        
        total = sum(self.niche_occupancy.values())
        max_occupancy = max(self.niche_occupancy.values()) if self.niche_occupancy else 1
        
        # Diversity = how evenly distributed organisms are
        # Perfect = all niches equally occupied
        expected_per_niche = total / len(self.niche_occupancy) if self.niche_occupancy else 1
        
        diversity = 1.0 - (max_occupancy / (expected_per_niche + 1e-6)) / len(self.niche_occupancy)
        
        return max(0.0, min(1.0, diversity))


class SpeciesTracker:
    """Tracks species, extinctions, and adaptive pressures"""
    
    def __init__(self):
        self.species_map: Dict[str, Dict] = {}
        self.extinction_history: List[Tuple[str, int, str]] = []  # (species_id, gen, reason)
        self.trait_pressures: Dict[str, float] = {}
        self.generation = 0
    
    async def register_species(self, species_id: str, organisms: List[AdaptiveOrganism]) -> None:
        """Register a new species"""
        
        if species_id not in self.species_map:
            traits = set()
            for org in organisms:
                traits.update(org.traits.keys())
            
            self.species_map[species_id] = {
                'organisms': len(organisms),
                'traits': traits,
                'birth_generation': self.generation,
                'status': SpeciesStatus.ACTIVE,
                'fitness_history': [],
                'population_history': [len(organisms)]
            }
    
    async def update_species(self, species_id: str, organisms: List[AdaptiveOrganism]) -> None:
        """Update species statistics"""
        
        if species_id in self.species_map:
            avg_fitness = sum(org.fitness for org in organisms) / len(organisms) if organisms else 0.0
            
            self.species_map[species_id]['organisms'] = len(organisms)
            self.species_map[species_id]['fitness_history'].append(avg_fitness)
            self.species_map[species_id]['population_history'].append(len(organisms))
            
            # Check for extinction
            if len(organisms) < 2:
                self.species_map[species_id]['status'] = SpeciesStatus.EXTINCT
                self.extinction_history.append((species_id, self.generation, 'low_population'))
            elif avg_fitness < 0.1:
                self.species_map[species_id]['status'] = SpeciesStatus.DECLINING
            elif avg_fitness > 0.5:
                self.species_map[species_id]['status'] = SpeciesStatus.RECOVERING
    
    async def prevent_extinction(self, species_id: str, refugium: List[AdaptiveOrganism]) -> List[AdaptiveOrganism]:
        """Try to save species through refugium strategy"""
        
        if species_id in self.species_map and self.species_map[species_id]['status'] == SpeciesStatus.EXTINCT:
            # Clone refugium individuals
            clones = []
            for org in refugium:
                clone = AdaptiveOrganism(
                    organism_id=f"{org.organism_id}_clone",
                    species_id=species_id,
                    traits={k: v for k, v in org.traits.items()},
                    fitness=org.fitness * 0.9,  # Slightly reduced fitness
                    niche_position=org.niche_position,
                    generation_born=self.generation
                )
                clones.append(clone)
            
            self.species_map[species_id]['status'] = SpeciesStatus.RECOVERING
            self.extinction_history.append((species_id, self.generation, 'recovered'))
            
            return clones
        
        return []
    
    async def get_species_status(self) -> Dict:
        """Get overall species statistics"""
        
        active = sum(1 for s in self.species_map.values() if s['status'] == SpeciesStatus.ACTIVE)
        declining = sum(1 for s in self.species_map.values() if s['status'] == SpeciesStatus.DECLINING)
        recovering = sum(1 for s in self.species_map.values() if s['status'] == SpeciesStatus.RECOVERING)
        extinct = sum(1 for s in self.species_map.values() if s['status'] == SpeciesStatus.EXTINCT)
        
        return {
            'total_species': len(self.species_map),
            'active': active,
            'declining': declining,
            'recovering': recovering,
            'extinct': extinct,
            'total_extinctions': len(self.extinction_history)
        }


class AdaptivePopulation:
    """Population with adaptive trait tracking and speciation"""
    
    def __init__(self, pop_size: int = 100):
        self.pop_size = pop_size
        self.population: List[AdaptiveOrganism] = []
        self.niche_former = NicheFormation()
        self.species_tracker = SpeciesTracker()
        self.generation = 0
        self.trait_evolution_history: List[Dict] = []
    
    async def initialize_population(self) -> None:
        """Initialize population with random organisms"""
        
        self.population = []
        
        for i in range(self.pop_size):
            traits = {}
            for j in range(3):
                traits[f"trait_{j}"] = Trait(
                    trait_id=f"trait_{j}",
                    trait_type=random.choice(['morphological', 'behavioral', 'physiological']),
                    value=random.random()
                )
            
            org = AdaptiveOrganism(
                organism_id=f"org_{i}",
                species_id="species_0",
                traits=traits,
                fitness=random.random(),
                niche_position=(random.random(), random.random()),
                generation_born=0
            )
            
            self.population.append(org)
        
        # Register initial species
        await self.species_tracker.register_species("species_0", self.population)
    
    async def apply_adaptation_pressure(self, pressure_traits: List[str]) -> None:
        """Apply pressure to specific trait types"""
        
        for org in self.population:
            for trait_name in pressure_traits:
                if trait_name in org.traits:
                    trait = org.traits[trait_name]
                    
                    # Increase adaptation pressure
                    trait.adaptation_pressure += 0.1
                    trait.usage_count += 1
                    
                    # Organisms with higher values survive better
                    org.fitness *= (1.0 + trait.value * 0.1)
    
    async def evolve_traits(self) -> None:
        """Evolve traits based on adaptation pressure"""
        
        # Top 50% survive
        sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        survivors = sorted_pop[:len(sorted_pop) // 2]
        
        # Breed next generation
        new_pop = survivors.copy()
        while len(new_pop) < self.pop_size:
            parent1 = random.choice(survivors)
            parent2 = random.choice(survivors)
            
            # Create offspring
            offspring = AdaptiveOrganism(
                organism_id=f"org_{len(new_pop)}",
                species_id=parent1.species_id,
                traits={},
                fitness=0.0,
                niche_position=(
                    (parent1.niche_position[0] + parent2.niche_position[0]) / 2 + random.gauss(0, 0.05),
                    (parent1.niche_position[1] + parent2.niche_position[1]) / 2 + random.gauss(0, 0.05)
                ),
                generation_born=self.generation
            )
            
            # Inherit and mutate traits
            for trait_name, trait in parent1.traits.items():
                new_trait = Trait(
                    trait_id=trait.trait_id,
                    trait_type=trait.trait_type,
                    value=trait.value + random.gauss(0, 0.05),
                    adaptation_pressure=trait.adaptation_pressure
                )
                offspring.traits[trait_name] = new_trait
            
            offspring.fitness = (parent1.fitness + parent2.fitness) / 2
            new_pop.append(offspring)
        
        self.population = new_pop[:self.pop_size]
    
    async def form_species(self) -> None:
        """Form species based on niche positions"""
        
        niches = await self.niche_former.detect_niches(self.population)
        
        # Assign organisms to niches
        for org in self.population:
            min_dist = float('inf')
            nearest_niche_idx = 0
            
            for i, niche in enumerate(niches):
                dist = ((org.niche_position[0] - niche[0]) ** 2 + 
                       (org.niche_position[1] - niche[1]) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    nearest_niche_idx = i
            
            org.species_id = f"species_{nearest_niche_idx}"
        
        # Register new species
        for niche_idx in range(len(niches)):
            species_orgs = [org for org in self.population if org.species_id == f"species_{niche_idx}"]
            if species_orgs:
                await self.species_tracker.register_species(f"species_{niche_idx}", species_orgs)
                await self.species_tracker.update_species(f"species_{niche_idx}", species_orgs)
    
    async def step(self, generations: int = 5) -> List[Dict]:
        """Simulate population for N generations"""
        
        results = []
        
        for gen in range(generations):
            self.generation = gen
            self.species_tracker.generation = gen
            
            # Apply random adaptation pressures
            if random.random() < 0.3:
                await self.apply_adaptation_pressure(['trait_0'])
            if random.random() < 0.3:
                await self.apply_adaptation_pressure(['trait_1'])
            
            # Evolve traits
            await self.evolve_traits()
            
            # Form species
            await self.form_species()
            
            # Collect stats
            stats = await self.species_tracker.get_species_status()
            niche_div = await self.niche_former.get_niche_diversity()
            avg_fitness = sum(org.fitness for org in self.population) / len(self.population)
            
            record = {
                'generation': gen,
                'avg_fitness': avg_fitness,
                'niche_diversity': niche_div,
                'species_count': stats['total_species'],
                'extinctions': stats['total_extinctions'],
                'status': stats
            }
            
            results.append(record)
        
        return results


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_speciation():
    """Demonstrate speciation and adaptive niches"""
    
    print("\n" + "=" * 70)
    print("SPECIATION & ADAPTIVE NICHES - PHASE 6D")
    print("=" * 70)
    
    # Initialize population
    print("\n[Setup] Initializing population...")
    pop = AdaptivePopulation(pop_size=100)
    await pop.initialize_population()
    print(f"  Population size: {len(pop.population)}")
    
    # Simulate evolution
    print("\n[Evolution] Simulating 10 generations...")
    results = await pop.step(generations=10)
    
    print("\n[Generation Statistics]:")
    print(f"  Gen | Avg Fitness | Niche Div | Species | Extinctions")
    print(f"  ----+-------------+-----------+---------+------------")
    
    for record in results:
        gen = record['generation']
        fit = record['avg_fitness']
        div = record['niche_diversity']
        sp = record['species_count']
        ext = record['extinctions']
        
        print(f"  {gen:2d}  |    {fit:.4f}    |   {div:.3f}   |   {sp:2d}    |    {ext:2d}")
    
    # Final statistics
    print("\n[Final Statistics]:")
    final_stats = results[-1]['status']
    print(f"  Total species formed: {final_stats['total_species']}")
    print(f"  Active species: {final_stats['active']}")
    print(f"  Declining species: {final_stats['declining']}")
    print(f"  Recovering species: {final_stats['recovering']}")
    print(f"  Extinct species: {final_stats['extinct']}")
    print(f"  Total extinctions recorded: {final_stats['total_extinctions']}")
    
    # Niche statistics
    print("\n[Niche Distribution]:")
    if pop.niche_former.niche_occupancy:
        for i, occupancy in pop.niche_former.niche_occupancy.items():
            print(f"  Niche {i}: {occupancy} organisms")
    
    # Trait evolution
    print("\n[Trait Pressures Applied]:")
    total_trait_pressure = 0
    for org in pop.population:
        for trait in org.traits.values():
            total_trait_pressure += trait.adaptation_pressure
    
    avg_pressure = total_trait_pressure / (len(pop.population) * 3) if pop.population else 0
    print(f"  Average adaptation pressure: {avg_pressure:.4f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_speciation())
