"""
Tests for F601: DGM ARCHIVE module
==================================
Tests for developmental generational archive.
"""

import pytest
from pathlib import Path
from pradysagican.core.evolution.archive import (
    DGMArchive,
    Variant,
    VariantType,
    VariantMetrics,
    SamplingStrategy,
)


@pytest.fixture
def archive(tmp_path):
    """Create test archive instance."""
    return DGMArchive(archive_dir=tmp_path)


@pytest.fixture
def sample_metrics():
    """Create sample metrics."""
    return VariantMetrics(
        fitness_score=0.85,
        novelty_score=0.72,
        qd_score=0.61,
        performance_ms=125.0,
        memory_mb=45.2,
        success_rate=0.95,
        test_coverage_pct=82.0,
    )


class TestArchiveInitialization:
    """Test archive initialization."""

    def test_archive_init(self, archive):
        """Test basic initialization."""
        assert archive is not None
        assert archive.archive_dir.exists()
        assert archive.max_variants > 0
        assert len(archive._variants) == 0

    def test_archive_with_custom_max(self, tmp_path):
        """Test initialization with custom max variants."""
        archive = DGMArchive(archive_dir=tmp_path, max_variants=500)
        assert archive.max_variants == 500


class TestVariantManagement:
    """Test variant addition and retrieval."""

    def test_add_variant(self, archive, sample_metrics):
        """Test adding variant to archive."""
        code = "def test(): return 42"
        variant = archive.add_variant(
            code=code,
            variant_type=VariantType.BASELINE,
            metrics=sample_metrics,
        )
        
        assert variant is not None
        assert variant.variant_id is not None
        assert variant.variant_type == VariantType.BASELINE
        assert len(archive._variants) == 1

    def test_get_variant(self, archive, sample_metrics):
        """Test retrieving variant."""
        code = "def hello(): return 'world'"
        added = archive.add_variant(code, VariantType.EVOLVED, sample_metrics)
        
        retrieved = archive.get_variant(added.variant_id)
        assert retrieved is not None
        assert retrieved.variant_id == added.variant_id
        assert retrieved.code == code

    def test_get_nonexistent_variant(self, archive):
        """Test getting non-existent variant."""
        variant = archive.get_variant("nonexistent_id")
        assert variant is None

    def test_add_with_parent(self, archive, sample_metrics):
        """Test adding variant with parent."""
        parent = archive.add_variant("def parent(): pass", VariantType.BASELINE, sample_metrics)
        
        child_metrics = VariantMetrics(
            fitness_score=0.90,
            novelty_score=0.68,
            qd_score=0.612,
            performance_ms=110.0,
            memory_mb=42.0,
            success_rate=0.97,
            test_coverage_pct=85.0,
        )
        child = archive.add_variant(
            "def child(): pass",
            VariantType.MUTATED,
            child_metrics,
            parent_id=parent.variant_id,
        )
        
        assert child.lineage_parent_id == parent.variant_id


class TestVariantMetrics:
    """Test variant metrics."""

    def test_metrics_structure(self, sample_metrics):
        """Test metrics structure."""
        assert sample_metrics.fitness_score == 0.85
        assert sample_metrics.novelty_score == 0.72
        assert sample_metrics.qd_score == 0.61

    def test_variant_compression(self, archive, sample_metrics):
        """Test variant compression."""
        code = "def " * 100 + "test(): pass"  # Create a long code
        variant = archive.add_variant(code, VariantType.BASELINE, sample_metrics)
        
        assert len(variant.code_compressed) > 0
        assert variant.decompress() == code


class TestSampling:
    """Test variant sampling strategies."""

    def test_sample_best(self, archive, sample_metrics):
        """Test sampling best variants."""
        for i in range(5):
            metrics = VariantMetrics(
                fitness_score=0.5 + i * 0.1,
                novelty_score=0.5,
                qd_score=0.25 + i * 0.05,
                performance_ms=100.0,
                memory_mb=40.0,
                success_rate=0.9,
                test_coverage_pct=80.0,
            )
            archive.add_variant(f"def code{i}(): pass", VariantType.BASELINE, metrics)
        
        sampled = archive.sample_variants(count=2, strategy=SamplingStrategy.BEST)
        assert len(sampled) == 2
        assert sampled[0].metrics.fitness_score >= sampled[1].metrics.fitness_score

    def test_sample_tournament(self, archive, sample_metrics):
        """Test tournament sampling."""
        for i in range(5):
            metrics = VariantMetrics(
                fitness_score=0.5 + i * 0.1,
                novelty_score=0.5,
                qd_score=0.25,
                performance_ms=100.0,
                memory_mb=40.0,
                success_rate=0.9,
                test_coverage_pct=80.0,
            )
            archive.add_variant(f"def code{i}(): pass", VariantType.BASELINE, metrics)
        
        sampled = archive.sample_variants(count=2, strategy=SamplingStrategy.TOURNAMENT)
        assert len(sampled) == 2

    def test_sample_qd(self, archive, sample_metrics):
        """Test QD sampling."""
        for i in range(5):
            metrics = VariantMetrics(
                fitness_score=0.5 + i * 0.1,
                novelty_score=0.5 + i * 0.05,
                qd_score=(0.5 + i * 0.1) * (0.5 + i * 0.05),
                performance_ms=100.0,
                memory_mb=40.0,
                success_rate=0.9,
                test_coverage_pct=80.0,
            )
            archive.add_variant(f"def code{i}(): pass", VariantType.BASELINE, metrics)
        
        sampled = archive.sample_variants(count=2, strategy=SamplingStrategy.QD)
        assert len(sampled) == 2

    def test_sample_random(self, archive, sample_metrics):
        """Test random sampling."""
        for i in range(5):
            archive.add_variant(f"def code{i}(): pass", VariantType.BASELINE, sample_metrics)
        
        sampled = archive.sample_variants(count=2, strategy=SamplingStrategy.RANDOM)
        assert len(sampled) == 2

    def test_sample_empty_archive(self, archive):
        """Test sampling from empty archive."""
        sampled = archive.sample_variants(count=5)
        assert len(sampled) == 0


class TestLineageTracking:
    """Test lineage tracking."""

    def test_lineage_graph_creation(self, archive, sample_metrics):
        """Test lineage graph creation."""
        parent = archive.add_variant("def p(): pass", VariantType.BASELINE, sample_metrics)
        child = archive.add_variant(
            "def c(): pass",
            VariantType.MUTATED,
            sample_metrics,
            parent_id=parent.variant_id,
        )
        
        graph = archive.get_lineage_tree()
        assert parent.variant_id in graph.nodes()
        assert child.variant_id in graph.nodes()
        assert (parent.variant_id, child.variant_id) in graph.edges()

    def test_lineage_depth(self, archive, sample_metrics):
        """Test lineage depth calculation."""
        v1 = archive.add_variant("def v1(): pass", VariantType.BASELINE, sample_metrics)
        v2 = archive.add_variant("def v2(): pass", VariantType.MUTATED, sample_metrics, parent_id=v1.variant_id)
        v3 = archive.add_variant("def v3(): pass", VariantType.EVOLVED, sample_metrics, parent_id=v2.variant_id)
        
        stats = archive.get_generation_stats()
        assert stats["lineage_depth"] >= 2


class TestPruning:
    """Test archive pruning."""

    def test_pruning_limit(self, tmp_path):
        """Test pruning maintains max_variants limit."""
        archive = DGMArchive(archive_dir=tmp_path, max_variants=10)
        
        # Add more variants than max
        for i in range(15):
            metrics = VariantMetrics(
                fitness_score=0.5 + (i % 10) * 0.05,
                novelty_score=0.5 + (i % 10) * 0.02,
                qd_score=0.25,
                performance_ms=100.0,
                memory_mb=40.0,
                success_rate=0.9,
                test_coverage_pct=80.0,
            )
            archive.add_variant(f"def code{i}(): pass", VariantType.BASELINE, metrics)
        
        # Archive should be pruned
        assert len(archive._variants) <= archive.max_variants


class TestStatistics:
    """Test archive statistics."""

    def test_generation_stats(self, archive, sample_metrics):
        """Test generation statistics."""
        for i in range(3):
            archive.add_variant(f"def code{i}(): pass", VariantType.BASELINE, sample_metrics)
        
        stats = archive.get_generation_stats()
        assert stats["total_variants"] == 3
        assert stats["avg_fitness"] > 0
        assert "variant_types" in stats

    def test_stats_empty_archive(self, archive):
        """Test stats on empty archive."""
        stats = archive.get_generation_stats()
        assert stats["total_variants"] == 0


class TestExport:
    """Test variant export."""

    def test_export_variants(self, archive, sample_metrics, tmp_path):
        """Test exporting variants."""
        for i in range(3):
            archive.add_variant(f"def code{i}(): pass", VariantType.BASELINE, sample_metrics)
        
        export_path = archive.export_variants(output_path=tmp_path / "export.json")
        assert export_path.exists()

    def test_export_empty_archive(self, archive, tmp_path):
        """Test exporting empty archive."""
        export_path = archive.export_variants(output_path=tmp_path / "empty.json")
        assert export_path.exists()


class TestVariantTypes:
    """Test variant type handling."""

    def test_all_variant_types(self, archive, sample_metrics):
        """Test all variant types."""
        for vtype in VariantType:
            variant = archive.add_variant(
                f"def {vtype.value}(): pass",
                vtype,
                sample_metrics,
            )
            assert variant.variant_type == vtype

    def test_variant_type_filtering(self, archive, sample_metrics):
        """Test filtering by variant type."""
        archive.add_variant("def b(): pass", VariantType.BASELINE, sample_metrics)
        archive.add_variant("def m(): pass", VariantType.MUTATED, sample_metrics)
        
        stats = archive.get_generation_stats()
        variant_types = stats["variant_types"]
        
        assert variant_types[VariantType.BASELINE.value] >= 1
        assert variant_types[VariantType.MUTATED.value] >= 1
