#!/usr/bin/env python3
"""
PHASE 6B: QUALITY-DIVERSITY OPTIMIZATION
MAP-Elites algorithm for exploring solution space
"""

import asyncio
import random
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime


# ════════════════════════════════════════════════════════════════════════════
# BEHAVIOR DESCRIPTORS & ARCHIVE
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class BehaviorDescriptor:
    """Characterizes solution behavior in low-dimensional space"""
    dimensions: int = 2
    values: List[float] = field(default_factory=list)
    
    async def to_key(self) -> str:
        """Convert to dictionary key"""
        return "|".join(f"{v:.2f}" for v in self.values)
    
    async def distance_to(self, other: 'BehaviorDescriptor') -> float:
        """Euclidean distance to other descriptor"""
        if len(self.values) != len(other.values):
            return float('inf')
        return sum((a - b) ** 2 for a, b in zip(self.values, other.values)) ** 0.5


@dataclass
class Solution:
    """Solution with quality and behavior"""
    solution_id: str
    genes: Dict[str, float]
    quality: float
    behavior: BehaviorDescriptor
    novelty_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class QualityDiversityArchive:
    """MAP-Elites archive for QD optimization"""
    
    def __init__(self, grid_size: int = 10):
        self.grid_size = grid_size
        self.archive: Dict[str, Solution] = {}
        self.history: List[Dict[str, Any]] = []
        self.evaluations = 0
    
    async def get_cell_key(self, behavior: BehaviorDescriptor) -> str:
        """Get grid cell for behavior"""
        return await behavior.to_key()
    
    async def add_solution(self, solution: Solution) -> Tuple[bool, str]:
        """Add solution to archive if it improves the cell"""
        cell_key = await self.get_cell_key(solution.behavior)
        
        if cell_key not in self.archive:
            # New cell - always add
            self.archive[cell_key] = solution
            self.evaluations += 1
            return True, "new_cell"
        
        # Cell exists - check if improvement
        existing = self.archive[cell_key]
        if solution.quality > existing.quality:
            self.archive[cell_key] = solution
            self.evaluations += 1
            return True, "improved"
        
        return False, "no_improvement"
    
    async def get_coverage(self) -> float:
        """Get coverage percentage"""
        return len(self.archive) / (self.grid_size ** 2)
    
    async def get_quality_stats(self) -> Dict[str, float]:
        """Get quality statistics"""
        if not self.archive:
            return {}
        
        qualities = [s.quality for s in self.archive.values()]
        
        return {
            'best_quality': max(qualities),
            'worst_quality': min(qualities),
            'avg_quality': sum(qualities) / len(qualities),
            'median_quality': sorted(qualities)[len(qualities) // 2],
        }
    
    async def get_best_solutions(self, k: int = 5) -> List[Solution]:
        """Get top k solutions by quality"""
        sorted_solutions = sorted(self.archive.values(), 
                                 key=lambda s: s.quality, reverse=True)
        return sorted_solutions[:k]


# ════════════════════════════════════════════════════════════════════════════
# NOVELTY SEARCH
# ════════════════════════════════════════════════════════════════════════════

class NoveltySearch:
    """Novelty-based behavioral search"""
    
    def __init__(self, k_neighbors: int = 15):
        self.k_neighbors = k_neighbors
        self.behavioral_history: List[BehaviorDescriptor] = []
    
    async def evaluate_novelty(self, behavior: BehaviorDescriptor,
                              archive: QualityDiversityArchive) -> float:
        """Calculate novelty score for a behavior"""
        
        # Get all behaviors from archive
        all_behaviors = [s.behavior for s in archive.archive.values()]
        
        if not all_behaviors:
            return 1.0  # High novelty if archive empty
        
        # Calculate distances to k nearest neighbors
        distances = []
        for existing_behavior in all_behaviors:
            dist = await behavior.distance_to(existing_behavior)
            distances.append(dist)
        
        # Average distance to k neighbors
        distances.sort()
        k = min(self.k_neighbors, len(distances))
        novelty = sum(distances[:k]) / k if k > 0 else 0.0
        
        return min(novelty, 1.0)  # Normalize to [0, 1]


# ════════════════════════════════════════════════════════════════════════════
# MAP-ELITES OPTIMIZATION
# ════════════════════════════════════════════════════════════════════════════

class MapElitesOptimizer:
    """MAP-Elites algorithm for quality-diversity optimization"""
    
    def __init__(self, pop_size: int = 100, grid_size: int = 10):
        self.pop_size = pop_size
        self.grid_size = grid_size
        self.archive = QualityDiversityArchive(grid_size)
        self.novelty_search = NoveltySearch(k_neighbors=10)
        self.generation = 0
        self.solutions_evaluated = 0
    
    async def create_random_solution(self) -> Solution:
        """Generate random solution"""
        genes = {
            'param_a': random.random(),
            'param_b': random.random(),
            'param_c': random.random(),
            'param_d': random.random(),
        }
        
        # Behavior from first two parameters
        behavior = BehaviorDescriptor(
            dimensions=2,
            values=[genes['param_a'], genes['param_b']]
        )
        
        # Quality from all parameters
        quality = (genes['param_a'] * genes['param_b'] + 
                  genes['param_c'] * genes['param_d'])
        
        # Add novelty bonus
        novelty = await self.novelty_search.evaluate_novelty(behavior, self.archive)
        quality_with_novelty = 0.7 * quality + 0.3 * novelty
        
        solution = Solution(
            solution_id=f"sol_{self.solutions_evaluated:06d}",
            genes=genes,
            quality=quality_with_novelty,
            behavior=behavior,
            novelty_score=novelty
        )
        
        self.solutions_evaluated += 1
        return solution
    
    async def mutate_solution(self, solution: Solution) -> Solution:
        """Create mutated copy of solution"""
        new_genes = solution.genes.copy()
        
        # Mutate random genes
        for _ in range(random.randint(1, 2)):
            gene_name = random.choice(list(new_genes.keys()))
            new_genes[gene_name] = max(0, min(1, new_genes[gene_name] + random.gauss(0, 0.1)))
        
        # Recalculate behavior and quality
        behavior = BehaviorDescriptor(
            dimensions=2,
            values=[new_genes['param_a'], new_genes['param_b']]
        )
        
        quality = (new_genes['param_a'] * new_genes['param_b'] + 
                  new_genes['param_c'] * new_genes['param_d'])
        
        novelty = await self.novelty_search.evaluate_novelty(behavior, self.archive)
        quality_with_novelty = 0.7 * quality + 0.3 * novelty
        
        solution = Solution(
            solution_id=f"sol_{self.solutions_evaluated:06d}",
            genes=new_genes,
            quality=quality_with_novelty,
            behavior=behavior,
            novelty_score=novelty
        )
        
        self.solutions_evaluated += 1
        return solution
    
    async def optimize_generation(self) -> Dict[str, Any]:
        """Run one generation of MAP-Elites"""
        
        # Sample from archive or generate random
        for _ in range(self.pop_size):
            if self.archive.archive and random.random() < 0.8:
                # Mutate from archive
                parent = random.choice(list(self.archive.archive.values()))
                solution = await self.mutate_solution(parent)
            else:
                # Random solution
                solution = await self.create_random_solution()
            
            # Try to add to archive
            added, reason = await self.archive.add_solution(solution)
        
        # Record statistics
        coverage = await self.archive.get_coverage()
        quality_stats = await self.archive.get_quality_stats()
        
        stats = {
            'generation': self.generation,
            'solutions_evaluated': self.solutions_evaluated,
            'archive_size': len(self.archive.archive),
            'coverage': coverage,
        }
        stats.update(quality_stats)
        
        self.archive.history.append(stats)
        self.generation += 1
        
        return stats
    
    async def get_elite_map(self) -> Dict[str, Dict[str, Any]]:
        """Get current elite solutions"""
        elite_map = {}
        
        for cell_key, solution in self.archive.archive.items():
            elite_map[cell_key] = {
                'quality': solution.quality,
                'novelty': solution.novelty_score,
                'genes': solution.genes,
            }
        
        return elite_map


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_quality_diversity():
    """Demonstrate quality-diversity optimization"""
    
    print("\n" + "=" * 70)
    print("QUALITY-DIVERSITY OPTIMIZATION (MAP-Elites) - PHASE 6B")
    print("=" * 70)
    
    optimizer = MapElitesOptimizer(pop_size=50, grid_size=10)
    
    # Run generations
    print("\n[Optimization] Running MAP-Elites generations...")
    for gen in range(10):
        stats = await optimizer.optimize_generation()
        
        print(f"  Gen {gen:2d}: Archive={stats['archive_size']:3d}, "
              f"Coverage={stats['coverage']*100:5.1f}%, "
              f"Quality={stats['best_quality']:6.3f}")
    
    # Final statistics
    print("\n[Statistics] Final Results:")
    final_stats = await optimizer.archive.get_quality_stats()
    for key, value in final_stats.items():
        print(f"  {key}: {value:.4f}")
    
    print(f"  Archive size: {len(optimizer.archive.archive)}")
    print(f"  Solutions evaluated: {optimizer.solutions_evaluated}")
    
    # Show best solutions
    print("\n[Elite Solutions] Top 5 by Quality:")
    best = await optimizer.archive.get_best_solutions(k=5)
    for i, sol in enumerate(best, 1):
        print(f"  {i}. Quality: {sol.quality:.4f}, Novelty: {sol.novelty_score:.4f}")
        print(f"     Behavior: ({sol.behavior.values[0]:.3f}, {sol.behavior.values[1]:.3f})")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_quality_diversity())
