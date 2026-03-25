"""
Core learning module: Automated reinforcement learning from failures.

Exports:
- AutoRL: Failure-driven principle extraction and retrieval
"""

from .auto_rl import (
    AutoRL,
    FailureTrajectory,
    FailureEvent,
    FailureCategory,
    Principle,
    RetrievalResult,
)

__all__ = [
    "AutoRL",
    "FailureTrajectory",
    "FailureEvent",
    "FailureCategory",
    "Principle",
    "RetrievalResult",
]
