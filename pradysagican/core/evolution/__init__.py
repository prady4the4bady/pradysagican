"""
Core evolution module: Evolutionary algorithms and variant management.

Exports:
- Validator: Benchmark-gated code validation
- DGMArchive: Developmental generational archive with quality diversity
"""

from .validator import (
    Validator,
    ValidationReport,
    ValidationDecision,
    BenchmarkResult,
    BenchmarkType,
)
from .archive import (
    DGMArchive,
    Variant,
    VariantType,
    VariantMetrics,
    SamplingStrategy,
)

__all__ = [
    "Validator",
    "ValidationReport",
    "ValidationDecision",
    "BenchmarkResult",
    "BenchmarkType",
    "DGMArchive",
    "Variant",
    "VariantType",
    "VariantMetrics",
    "SamplingStrategy",
]
