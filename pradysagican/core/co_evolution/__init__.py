"""
PHASE 6: Co-Evolution Framework (F612-F620)
============================================

Multi-Agent Evolution (MAE) framework for PRADYSAGICAN.
Enables continuous learning and adaptation across multiple agent instances.

Exports:
- MAEProposer: Generate improvement proposals (F612)
- MAESolver: Resolve conflicts & optimize (F613)
- MAEJudge: Quality assessment (F614)
- ToolR0Evolution: Recursive tool building (F615)
- CoEvolutionOrchestrator: Complete pipeline (F616)
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
from pradysagican.core.co_evolution.proposer import (
    MAEProposer,
    Proposal,
    ProposalStrategy,
    PopulationSnapshot,
)
from pradysagican.core.co_evolution.solver import (
    MAESolver,
    Solution,
    Objective,
    ConflictResolutionStrategy,
)
from pradysagican.core.co_evolution.judge import (
    MAEJudge,
    FitnessScore,
    BenchmarkResult,
    PopulationMetrics,
    BenchmarkType,
)
from pradysagican.core.co_evolution.tool_r0 import (
    ToolR0Evolution,
    ToolSpecification,
    ToolComposition,
    ToolType,
)
from pradysagican.core.co_evolution.orchestrator import (
    CoEvolutionOrchestrator,
    EvolutionState,
)

__version__ = "1.0.0"
__phase__ = 6
__framework__ = "MAE (Multi-Agent Evolution) v2"

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
    # Phase 6 Features
    "MAEProposer",
    "Proposal",
    "ProposalStrategy",
    "PopulationSnapshot",
    "MAESolver",
    "Solution",
    "Objective",
    "ConflictResolutionStrategy",
    "MAEJudge",
    "FitnessScore",
    "BenchmarkResult",
    "PopulationMetrics",
    "BenchmarkType",
    "ToolR0Evolution",
    "ToolSpecification",
    "ToolComposition",
    "ToolType",
    "CoEvolutionOrchestrator",
    "EvolutionState",
]
