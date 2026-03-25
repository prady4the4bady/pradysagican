"""
PHASE 6: Co-Evolution Framework (F612-F620)
============================================

Multi-Agent Evolution (MAE) framework for PRADYSAGICAN.
Enables continuous learning and adaptation across multiple agent instances.

Exports:
- MAEFramework: Core multi-agent evolution orchestrator
- ToolR0Agent: Tool-R0 co-evolution base class
- CoEvolutionContext: Context for agent evolution
- EvolutionStrategy: Base evolution strategy
"""

from pradysagican.core.co_evolution.base import (
    MAEFramework,
    ToolR0Agent,
    CoEvolutionContext,
    EvolutionStrategy,
    EvolutionMetrics,
    AgentGeneration,
)
from pradysagican.core.co_evolution.agents import (
    MultiAgentOrchestrator,
    AgentPopulation,
    SelectionStrategy,
    ReproductionOperator,
    MutationOperator,
)

__version__ = "1.0.0"
__phase__ = 6
__framework__ = "MAE (Multi-Agent Evolution)"

__all__ = [
    # Base classes
    "MAEFramework",
    "ToolR0Agent",
    "CoEvolutionContext",
    "EvolutionStrategy",
    "EvolutionMetrics",
    "AgentGeneration",
    # Multi-agent orchestration
    "MultiAgentOrchestrator",
    "AgentPopulation",
    "SelectionStrategy",
    "ReproductionOperator",
    "MutationOperator",
]
