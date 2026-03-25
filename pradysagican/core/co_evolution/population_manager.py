"""
F619: Population Manager - Multi-Population Coordination
=========================================================

Coordinate evolution across multiple populations:
- Multi-population synchronization
- Migration between populations
- Speciation to prevent harmful mixing
- Diversity maintenance across populations
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class SpeciesType(Enum):
    """Types of species classifications."""
    EXPLORERS = "explorers"  # High novelty, medium fitness
    EXPLOITERS = "exploiters"  # High fitness, low novelty
    BALANCED = "balanced"  # Medium fitness and novelty
    NICHE_SPECIALISTS = "niche_specialists"  # Domain-specific excellence


class MigrationPolicy(Enum):
    """Policies for inter-population migration."""
    ELITE_MIGRATION = "elite_migration"  # Best individuals only
    RANDOM_MIGRATION = "random_migration"  # Random sample
    DIVERSITY_MIGRATION = "diversity_migration"  # Most novel individuals
    BALANCED_MIGRATION = "balanced_migration"  # Mix of elite and diverse


@dataclass
class PopulationIndividual:
    """Individual in a population."""
    individual_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    species: str = SpeciesType.BALANCED.value
    fitness: float = 0.0
    novelty: float = 0.0
    genome: Dict[str, Any] = field(default_factory=dict)
    generation_created: int = 0
    age: int = 0
    migration_history: List[str] = field(default_factory=list)
    performance_data: Dict[str, float] = field(default_factory=dict)

    def compute_species_affinity(self) -> str:
        """Determine species classification."""
        if self.fitness > 0.7 and self.novelty < 0.3:
            return SpeciesType.EXPLOITERS.value
        elif self.novelty > 0.7 and self.fitness < 0.5:
            return SpeciesType.EXPLORERS.value
        elif self.fitness > 0.6 and self.novelty > 0.6:
            return SpeciesType.NICHE_SPECIALISTS.value
        else:
            return SpeciesType.BALANCED.value

    def update_age(self) -> None:
        """Increment individual age."""
        self.age += 1

    def record_migration(self, target_population_id: str) -> None:
        """Record migration to target population."""
        self.migration_history.append(target_population_id)


@dataclass
class SpeciesPopulation:
    """Population of a specific species."""
    species_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    species_type: str = SpeciesType.BALANCED.value
    individuals: Dict[str, PopulationIndividual] = field(default_factory=dict)
    target_size: int = 50
    generation: int = 0
    average_fitness: float = 0.0
    average_novelty: float = 0.0
    diversity_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    def update_metrics(self) -> None:
        """Update species population metrics."""
        if not self.individuals:
            self.average_fitness = 0.0
            self.average_novelty = 0.0
            self.diversity_score = 0.0
            return

        individuals_list = list(self.individuals.values())
        self.average_fitness = sum(i.fitness for i in individuals_list) / len(individuals_list)
        self.average_novelty = sum(i.novelty for i in individuals_list) / len(individuals_list)
        
        # Diversity: variance in fitness and novelty
        fitness_var = sum((i.fitness - self.average_fitness) ** 2 for i in individuals_list) / len(individuals_list)
        novelty_var = sum((i.novelty - self.average_novelty) ** 2 for i in individuals_list) / len(individuals_list)
        self.diversity_score = (fitness_var + novelty_var) / 2


class PopulationCluster:
    """Manages a cluster of specialized populations."""

    def __init__(
        self,
        num_species: int = 4,
        individuals_per_species: int = 50,
    ):
        """Initialize population cluster.

        Args:
            num_species: Number of species populations
            individuals_per_species: Target individuals per species
        """
        self.cluster_id = str(uuid.uuid4())
        self.num_species = num_species
        self.individuals_per_species = individuals_per_species
        
        # Species populations
        self.species_populations: Dict[str, SpeciesPopulation] = {}
        for species_type in SpeciesType:
            pop = SpeciesPopulation(
                species_type=species_type.value,
                target_size=individuals_per_species,
            )
            self.species_populations[species_type.value] = pop

        # Metrics
        self.generation = 0
        self.total_individuals = 0
        self.creation_timestamp = datetime.utcnow()

    def add_individual(
        self,
        individual: PopulationIndividual,
        species_type: str,
    ) -> bool:
        """Add individual to species population.

        Args:
            individual: Individual to add
            species_type: Target species type

        Returns:
            True if added successfully
        """
        if species_type not in self.species_populations:
            logger.warning(f"Unknown species type: {species_type}")
            return False

        species_pop = self.species_populations[species_type]
        
        # Check capacity
        if len(species_pop.individuals) >= species_pop.target_size:
            logger.debug(f"Species {species_type} at capacity")
            return False

        species_pop.individuals[individual.individual_id] = individual
        self.total_individuals += 1
        return True

    def evolve_species(self) -> None:
        """Evolve each species population."""
        for species_pop in self.species_populations.values():
            species_pop.generation += 1
            species_pop.update_metrics()
            logger.debug(
                f"Evolved species {species_pop.species_type}: "
                f"fitness={species_pop.average_fitness:.3f}, "
                f"novelty={species_pop.average_novelty:.3f}"
            )

    def get_cluster_diversity(self) -> float:
        """Calculate cluster-level diversity.

        Returns:
            Diversity score (0.0-1.0)
        """
        if not self.species_populations:
            return 0.0

        species_diversities = [
            pop.diversity_score
            for pop in self.species_populations.values()
            if pop.individuals
        ]

        if not species_diversities:
            return 0.0

        return sum(species_diversities) / len(species_diversities)

    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get cluster statistics."""
        stats = {
            "cluster_id": self.cluster_id,
            "total_individuals": self.total_individuals,
            "generation": self.generation,
            "cluster_diversity": self.get_cluster_diversity(),
            "species": {}
        }

        for species_type, pop in self.species_populations.items():
            stats["species"][species_type] = {
                "size": len(pop.individuals),
                "target_size": pop.target_size,
                "average_fitness": pop.average_fitness,
                "average_novelty": pop.average_novelty,
                "diversity_score": pop.diversity_score,
            }

        return stats


class SpeciationManager:
    """Manages speciation to prevent harmful mixing."""

    def __init__(self, similarity_threshold: float = 0.8):
        """Initialize speciation manager.

        Args:
            similarity_threshold: Threshold for same-species classification
        """
        self.similarity_threshold = similarity_threshold
        self.species_map: Dict[str, str] = {}  # individual_id -> species_id
        self.species_representatives: Dict[str, PopulationIndividual] = {}
        self.species_sizes: Dict[str, int] = {}

    def speciate_individual(
        self,
        individual: PopulationIndividual,
        population: List[PopulationIndividual],
    ) -> str:
        """Assign individual to species.

        Args:
            individual: Individual to speciate
            population: Existing population for comparison

        Returns:
            Species ID
        """
        # Compute affinity with existing species
        best_species_id = None
        best_similarity = self.similarity_threshold

        for species_id, representative in self.species_representatives.items():
            similarity = self._compute_similarity(individual, representative)
            if similarity > best_similarity:
                best_similarity = similarity
                best_species_id = species_id

        # Create new species if no good match
        if best_species_id is None:
            best_species_id = str(uuid.uuid4())
            self.species_representatives[best_species_id] = individual
            self.species_sizes[best_species_id] = 0

        # Assign individual to species
        self.species_map[individual.individual_id] = best_species_id
        self.species_sizes[best_species_id] = self.species_sizes.get(best_species_id, 0) + 1

        logger.debug(f"Speciated individual {individual.individual_id} to species {best_species_id}")
        return best_species_id

    def _compute_similarity(
        self,
        ind1: PopulationIndividual,
        ind2: PopulationIndividual,
    ) -> float:
        """Compute similarity between two individuals.

        Args:
            ind1: First individual
            ind2: Second individual

        Returns:
            Similarity score (0.0-1.0)
        """
        # Simple: based on fitness and novelty
        fitness_diff = abs(ind1.fitness - ind2.fitness)
        novelty_diff = abs(ind1.novelty - ind2.novelty)
        
        similarity = 1.0 - (fitness_diff + novelty_diff) / 2.0
        return max(0.0, similarity)

    def get_species_info(self, species_id: str) -> Dict[str, Any]:
        """Get information about a species.

        Args:
            species_id: Species identifier

        Returns:
            Species information
        """
        return {
            "species_id": species_id,
            "size": self.species_sizes.get(species_id, 0),
            "representative": self.species_representatives.get(species_id),
        }

    def get_all_species(self) -> List[Dict[str, Any]]:
        """Get all species information.

        Returns:
            List of species information dicts
        """
        return [
            self.get_species_info(species_id)
            for species_id in self.species_representatives.keys()
        ]


class MultiPopulationManager:
    """Manages multiple co-evolving populations."""

    def __init__(
        self,
        num_populations: int = 5,
        migration_interval: int = 10,
        migration_policy: MigrationPolicy = MigrationPolicy.BALANCED_MIGRATION,
    ):
        """Initialize multi-population manager.

        Args:
            num_populations: Number of populations to manage
            migration_interval: Generations between migrations
            migration_policy: Policy for inter-population migration
        """
        self.num_populations = num_populations
        self.migration_interval = migration_interval
        self.migration_policy = migration_policy

        # Populations
        self.clusters: Dict[str, PopulationCluster] = {}
        for i in range(num_populations):
            cluster = PopulationCluster(num_species=4)
            self.clusters[f"pop_{i}"] = cluster

        # Speciation
        self.speciation_manager = SpeciationManager()

        # Metrics
        self.generation = 0
        self.migrations_executed = 0

    def migrate_individuals(
        self,
        num_migrants: int = 5,
    ) -> Dict[str, Any]:
        """Execute inter-population migration.

        Args:
            num_migrants: Number of individuals to migrate

        Returns:
            Migration statistics
        """
        migration_stats = {
            "migrants_moved": 0,
            "migrations_by_policy": {},
            "population_changes": {}
        }

        # Select source and target populations
        pop_ids = list(self.clusters.keys())
        if len(pop_ids) < 2:
            return migration_stats

        migration_pairs = [
            (pop_ids[i], pop_ids[(i + 1) % len(pop_ids)])
            for i in range(len(pop_ids))
        ]

        for source_id, target_id in migration_pairs:
            source_cluster = self.clusters[source_id]
            target_cluster = self.clusters[target_id]

            # Select migrants based on policy
            migrants = self._select_migrants(
                source_cluster,
                num_migrants,
                self.migration_policy
            )

            # Perform migration
            for migrant in migrants:
                species_type = migrant.compute_species_affinity()
                if target_cluster.add_individual(migrant, species_type):
                    migrant.record_migration(target_id)
                    migration_stats["migrants_moved"] += 1

        self.migrations_executed += 1
        logger.debug(f"Migration completed: {migration_stats['migrants_moved']} individuals moved")
        return migration_stats

    def _select_migrants(
        self,
        cluster: PopulationCluster,
        count: int,
        policy: MigrationPolicy,
    ) -> List[PopulationIndividual]:
        """Select individuals for migration based on policy.

        Args:
            cluster: Source population cluster
            count: Number of individuals to select
            policy: Migration selection policy

        Returns:
            List of selected individuals
        """
        all_individuals = []
        for species_pop in cluster.species_populations.values():
            all_individuals.extend(species_pop.individuals.values())

        if not all_individuals:
            return []

        count = min(count, len(all_individuals))

        if policy == MigrationPolicy.ELITE_MIGRATION:
            # Select highest fitness
            selected = sorted(
                all_individuals,
                key=lambda x: x.fitness,
                reverse=True
            )[:count]
        elif policy == MigrationPolicy.DIVERSITY_MIGRATION:
            # Select highest novelty
            selected = sorted(
                all_individuals,
                key=lambda x: x.novelty,
                reverse=True
            )[:count]
        elif policy == MigrationPolicy.BALANCED_MIGRATION:
            # Mix of elite and diverse
            elite = sorted(
                all_individuals,
                key=lambda x: x.fitness,
                reverse=True
            )[:count // 2]
            diverse = sorted(
                all_individuals,
                key=lambda x: x.novelty,
                reverse=True
            )[:count - len(elite)]
            selected = elite + diverse
        else:  # RANDOM_MIGRATION
            import random
            selected = random.sample(all_individuals, count)

        return selected

    def get_global_stats(self) -> Dict[str, Any]:
        """Get statistics across all populations.

        Returns:
            Global statistics
        """
        all_stats = {
            "total_populations": len(self.clusters),
            "current_generation": self.generation,
            "total_migrations": self.migrations_executed,
            "populations": {}
        }

        total_individuals = 0
        avg_fitness_list = []
        avg_novelty_list = []

        for pop_id, cluster in self.clusters.items():
            cluster_stats = cluster.get_cluster_stats()
            all_stats["populations"][pop_id] = cluster_stats
            
            for species_stats in cluster_stats["species"].values():
                total_individuals += species_stats["size"]
                if species_stats["average_fitness"] > 0:
                    avg_fitness_list.append(species_stats["average_fitness"])
                if species_stats["average_novelty"] > 0:
                    avg_novelty_list.append(species_stats["average_novelty"])

        all_stats["total_individuals"] = total_individuals
        all_stats["average_fitness"] = sum(avg_fitness_list) / len(avg_fitness_list) if avg_fitness_list else 0.0
        all_stats["average_novelty"] = sum(avg_novelty_list) / len(avg_novelty_list) if avg_novelty_list else 0.0

        return all_stats
