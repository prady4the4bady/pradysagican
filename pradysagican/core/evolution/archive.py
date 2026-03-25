"""
F601: DGM ARCHIVE - Developmental Generational Archive with Quality Diversity
==============================================================================

Maintains an archive of evolved agent variants with:
- Quality Diversity (QD) scoring (novelty + performance)
- Compressed storage for 1000+ variants
- Lineage tracking with NetworkX DiGraph
- Multiple sampling strategies (best, tournament, QD, random-frontier)
- Automated pruning to maintain top variants
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import zlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import networkx as nx

logger = logging.getLogger(__name__)


class VariantType(str, Enum):
    """Classification of variant types."""
    BASELINE = "baseline"
    MUTATED = "mutated"
    CROSSOVER = "crossover"
    EVOLVED = "evolved"


class SamplingStrategy(str, Enum):
    """Strategies for sampling variants from archive."""
    BEST = "best"              # Top performers by fitness
    TOURNAMENT = "tournament"   # Tournament selection
    QD = "qd"                  # Quality diversity maximization
    RANDOM_FRONTIER = "random_frontier"  # Frontier of fitness-novelty tradeoff
    RANDOM = "random"          # Uniform random


@dataclass
class VariantMetrics:
    """Performance metrics for a variant."""
    fitness_score: float  # 0.0-1.0
    novelty_score: float  # 0.0-1.0
    qd_score: float  # fitness * novelty
    performance_ms: float  # Runtime performance
    memory_mb: float  # Memory usage
    success_rate: float  # 0.0-1.0
    test_coverage_pct: float


@dataclass
class Variant:
    """A single agent variant in the archive."""
    variant_id: str
    variant_type: VariantType
    code: str
    code_compressed: bytes = field(default_factory=bytes)
    metrics: VariantMetrics = field(default_factory=lambda: VariantMetrics(
        fitness_score=0.0,
        novelty_score=0.0,
        qd_score=0.0,
        performance_ms=0.0,
        memory_mb=0.0,
        success_rate=0.0,
        test_coverage_pct=0.0,
    ))
    lineage_parent_id: Optional[str] = None
    mutation_history: list[str] = field(default_factory=list)
    creation_timestamp: float = field(default_factory=time.time)
    last_evaluated: float = field(default_factory=time.time)
    evaluation_count: int = 0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def compress(self) -> None:
        """Compress code to reduce memory usage."""
        if self.code and not self.code_compressed:
            self.code_compressed = zlib.compress(self.code.encode(), level=9)
            logger.debug("Compressed variant %s: %.1fKB", self.variant_id,
                        len(self.code_compressed) / 1024)

    def decompress(self) -> str:
        """Decompress code from storage."""
        if self.code_compressed and not self.code:
            self.code = zlib.decompress(self.code_compressed).decode()
        return self.code

    def to_dict(self, compress_code: bool = True) -> dict[str, Any]:
        """Convert variant to dictionary for storage."""
        if compress_code:
            self.compress()
        
        return {
            "variant_id": self.variant_id,
            "variant_type": self.variant_type.value,
            "code_hash": hashlib.sha256(self.code.encode()).hexdigest()[:16] if self.code else "",
            "metrics": {
                "fitness_score": self.metrics.fitness_score,
                "novelty_score": self.metrics.novelty_score,
                "qd_score": self.metrics.qd_score,
                "performance_ms": self.metrics.performance_ms,
                "memory_mb": self.metrics.memory_mb,
                "success_rate": self.metrics.success_rate,
                "test_coverage_pct": self.metrics.test_coverage_pct,
            },
            "lineage_parent_id": self.lineage_parent_id,
            "creation_timestamp": self.creation_timestamp,
            "last_evaluated": self.last_evaluated,
            "evaluation_count": self.evaluation_count,
            "tags": self.tags,
        }


class DGMArchive:
    """Developmental Generational Archive with Quality Diversity support."""

    def __init__(
        self,
        archive_dir: Optional[Path] = None,
        max_variants: int = 1000,
        compression_enabled: bool = True,
    ):
        """
        Initialize the DGM archive.
        
        Args:
            archive_dir: Directory for storing archive data
            max_variants: Maximum number of variants to store
            compression_enabled: Whether to compress variant code
        """
        self.archive_dir = archive_dir or Path("./data/dgm_archive")
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_variants = max_variants
        self.compression_enabled = compression_enabled
        
        # In-memory storage
        self._variants: dict[str, Variant] = {}
        
        # Lineage tracking
        self._lineage_graph = nx.DiGraph()
        
        # Performance indices
        self._fitness_index: dict[str, float] = {}
        self._novelty_index: dict[str, float] = {}
        self._qd_index: dict[str, float] = {}
        
        self._load_archive()
        logger.info(
            "DGMArchive initialized: dir=%s, max_variants=%d, loaded=%d variants",
            self.archive_dir, max_variants, len(self._variants)
        )

    def add_variant(
        self,
        code: str,
        variant_type: VariantType,
        metrics: VariantMetrics,
        parent_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Variant:
        """
        Add a new variant to the archive.
        
        Args:
            code: Code of the variant
            variant_type: Type of variant
            metrics: Performance metrics
            parent_id: ID of parent variant (for lineage)
            tags: Tags for variant classification
            metadata: Additional metadata
            
        Returns:
            Created Variant object
        """
        # Generate unique ID
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:12]
        variant_id = f"{variant_type.value}_{int(time.time() * 1000)}_{code_hash}"
        
        variant = Variant(
            variant_id=variant_id,
            variant_type=variant_type,
            code=code,
            metrics=metrics,
            lineage_parent_id=parent_id,
            tags=tags or [],
            metadata=metadata or {},
        )
        
        # Compress if enabled
        if self.compression_enabled:
            variant.compress()
        
        # Store variant
        self._variants[variant_id] = variant
        
        # Update indices
        self._fitness_index[variant_id] = metrics.fitness_score
        self._novelty_index[variant_id] = metrics.novelty_score
        self._qd_index[variant_id] = metrics.qd_score
        
        # Update lineage graph
        self._lineage_graph.add_node(variant_id, variant_type=variant_type.value)
        if parent_id and parent_id in self._variants:
            self._lineage_graph.add_edge(parent_id, variant_id)
        
        logger.debug(
            "Added variant %s: type=%s, fitness=%.3f, novelty=%.3f, parent=%s",
            variant_id, variant_type.value, metrics.fitness_score,
            metrics.novelty_score, parent_id
        )
        
        # Prune if necessary
        if len(self._variants) > self.max_variants:
            self._prune_variants()
        
        return variant

    def get_variant(self, variant_id: str) -> Optional[Variant]:
        """Get a variant by ID."""
        variant = self._variants.get(variant_id)
        if variant:
            # Decompress on access
            variant.decompress()
            variant.evaluation_count += 1
            variant.last_evaluated = time.time()
        return variant

    def sample_variants(
        self,
        count: int = 1,
        strategy: SamplingStrategy = SamplingStrategy.QD,
    ) -> list[Variant]:
        """
        Sample variants using specified strategy.
        
        Args:
            count: Number of variants to sample
            strategy: Sampling strategy to use
            
        Returns:
            List of sampled variants
        """
        if not self._variants:
            logger.warning("Cannot sample: archive is empty")
            return []
        
        count = min(count, len(self._variants))
        variants_list = list(self._variants.values())
        
        if strategy == SamplingStrategy.BEST:
            # Sort by fitness and take top
            sorted_variants = sorted(variants_list, key=lambda v: v.metrics.fitness_score, reverse=True)
            sampled = sorted_variants[:count]
            
        elif strategy == SamplingStrategy.TOURNAMENT:
            # Tournament selection
            sampled = []
            for _ in range(count):
                tournament = sorted(
                    [variants_list[i] for i in range(min(5, len(variants_list)))],
                    key=lambda v: v.metrics.fitness_score,
                    reverse=True
                )
                sampled.append(tournament[0])
            
        elif strategy == SamplingStrategy.QD:
            # Quality-Diversity: balance fitness and novelty
            sorted_variants = sorted(variants_list, key=lambda v: v.metrics.qd_score, reverse=True)
            sampled = sorted_variants[:count]
            
        elif strategy == SamplingStrategy.RANDOM_FRONTIER:
            # Sample from Pareto frontier of fitness vs novelty
            frontier = self._compute_pareto_frontier(variants_list)
            import random
            sampled = random.sample(frontier, min(count, len(frontier)))
            
        else:  # SamplingStrategy.RANDOM
            import random
            sampled = random.sample(variants_list, count)
        
        # Decompress variants on return
        for v in sampled:
            v.decompress()
        
        logger.debug("Sampled %d variants using %s strategy", count, strategy.value)
        return sampled

    def _compute_pareto_frontier(self, variants: list[Variant]) -> list[Variant]:
        """Compute Pareto frontier based on fitness and novelty."""
        frontier = []
        
        for candidate in variants:
            is_dominated = False
            
            for other in variants:
                if other.variant_id == candidate.variant_id:
                    continue
                
                # Check if candidate is dominated by other
                if (other.metrics.fitness_score >= candidate.metrics.fitness_score and
                    other.metrics.novelty_score >= candidate.metrics.novelty_score and
                    (other.metrics.fitness_score > candidate.metrics.fitness_score or
                     other.metrics.novelty_score > candidate.metrics.novelty_score)):
                    is_dominated = True
                    break
            
            if not is_dominated:
                frontier.append(candidate)
        
        return frontier

    def _prune_variants(self) -> None:
        """Prune variants to maintain max_variants count."""
        if len(self._variants) <= self.max_variants:
            return
        
        logger.info("Pruning archive: %d → %d variants", len(self._variants), self.max_variants)
        
        # Keep best performers and most diverse
        sorted_by_qd = sorted(
            self._variants.values(),
            key=lambda v: v.metrics.qd_score,
            reverse=True
        )
        
        # Keep top 70% by QD score
        keep_count = int(self.max_variants * 0.7)
        keep_variants = sorted_by_qd[:keep_count]
        
        # Add diverse frontier variants (30%)
        frontier = self._compute_pareto_frontier(sorted_by_qd[keep_count:])
        diverse_count = self.max_variants - keep_count
        import random
        if frontier:
            keep_variants.extend(random.sample(frontier, min(diverse_count, len(frontier))))
        
        # Remove pruned variants
        keep_ids = {v.variant_id for v in keep_variants}
        removed_ids = set(self._variants.keys()) - keep_ids
        
        for variant_id in removed_ids:
            del self._variants[variant_id]
            self._fitness_index.pop(variant_id, None)
            self._novelty_index.pop(variant_id, None)
            self._qd_index.pop(variant_id, None)
            self._lineage_graph.remove_node(variant_id)
        
        logger.info("Pruned %d variants; archive now has %d", len(removed_ids), len(self._variants))

    def get_lineage_tree(self) -> nx.DiGraph:
        """Get the lineage tree as a NetworkX DiGraph."""
        return self._lineage_graph.copy()

    def get_generation_stats(self) -> dict[str, Any]:
        """Get statistics about variants in archive."""
        if not self._variants:
            return {"total_variants": 0}
        
        variants_list = list(self._variants.values())
        fitness_scores = [v.metrics.fitness_score for v in variants_list]
        novelty_scores = [v.metrics.novelty_score for v in variants_list]
        qd_scores = [v.metrics.qd_score for v in variants_list]
        
        import statistics
        
        return {
            "total_variants": len(self._variants),
            "max_variant_id": max(self.max_variants, len(self._variants)),
            "avg_fitness": statistics.mean(fitness_scores),
            "max_fitness": max(fitness_scores),
            "avg_novelty": statistics.mean(novelty_scores),
            "max_novelty": max(novelty_scores),
            "avg_qd_score": statistics.mean(qd_scores),
            "max_qd_score": max(qd_scores),
            "variant_types": {
                vtype.value: len([v for v in variants_list if v.variant_type == vtype])
                for vtype in VariantType
            },
            "avg_evaluation_count": statistics.mean(v.evaluation_count for v in variants_list),
            "lineage_depth": nx.dag_longest_path_length(self._lineage_graph) if self._lineage_graph.number_of_nodes() > 0 else 0,
        }

    def export_variants(self, output_path: Optional[Path] = None) -> Path:
        """
        Export all variants to JSON file.
        
        Args:
            output_path: Path to export file
            
        Returns:
            Path to exported file
        """
        output_path = output_path or self.archive_dir / "variants_export.json"
        
        try:
            export_data = {
                "timestamp": time.time(),
                "total_variants": len(self._variants),
                "variants": [
                    v.to_dict(compress_code=False) for v in self._variants.values()
                ],
                "stats": self.get_generation_stats(),
            }
            
            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info("Exported %d variants to %s", len(self._variants), output_path)
            return output_path
        except Exception as exc:
            logger.error("Failed to export variants: %s", exc)
            raise

    def _load_archive(self) -> None:
        """Load archive from storage."""
        archive_file = self.archive_dir / "archive.json"
        if not archive_file.exists():
            return
        
        try:
            with open(archive_file) as f:
                data = json.load(f)
                
                for variant_data in data.get("variants", []):
                    variant = Variant(
                        variant_id=variant_data["variant_id"],
                        variant_type=VariantType(variant_data["variant_type"]),
                        code="",  # Will be decompressed on access
                        metrics=VariantMetrics(
                            fitness_score=variant_data["metrics"]["fitness_score"],
                            novelty_score=variant_data["metrics"]["novelty_score"],
                            qd_score=variant_data["metrics"]["qd_score"],
                            performance_ms=variant_data["metrics"]["performance_ms"],
                            memory_mb=variant_data["metrics"]["memory_mb"],
                            success_rate=variant_data["metrics"]["success_rate"],
                            test_coverage_pct=variant_data["metrics"]["test_coverage_pct"],
                        ),
                        lineage_parent_id=variant_data.get("lineage_parent_id"),
                        creation_timestamp=variant_data.get("creation_timestamp", time.time()),
                        evaluation_count=variant_data.get("evaluation_count", 0),
                        tags=variant_data.get("tags", []),
                    )
                    self._variants[variant.variant_id] = variant
                    self._lineage_graph.add_node(variant.variant_id, variant_type=variant.variant_type.value)
            
            logger.info("Loaded %d variants from archive", len(self._variants))
        except Exception as exc:
            logger.warning("Failed to load archive: %s", exc)

    def save_archive(self) -> None:
        """Save archive to storage."""
        archive_file = self.archive_dir / "archive.json"
        
        try:
            data = {
                "timestamp": time.time(),
                "total_variants": len(self._variants),
                "variants": [v.to_dict() for v in self._variants.values()],
            }
            
            with open(archive_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info("Saved archive with %d variants", len(self._variants))
        except Exception as exc:
            logger.error("Failed to save archive: %s", exc)
