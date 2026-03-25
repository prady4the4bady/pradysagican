"""
Core self-referential module: Self-improvement and code editing.

Exports:
- SelfRefEditor: Direct file editing with improvement analysis
"""

from .editor import (
    SelfRefEditor,
    EditResult,
    Improvement,
    ImprovementType,
    CodeMetrics,
)

__all__ = [
    "SelfRefEditor",
    "EditResult",
    "Improvement",
    "ImprovementType",
    "CodeMetrics",
]
