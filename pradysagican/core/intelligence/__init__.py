"""Phase 7 Intelligence Architecture (F621-F645)

Multi-engine reasoning framework with graph-based, temporal, semantic, and integration engines.
"""

from .graph_engine import (
    KnowledgeGraph,
    Node,
    Relationship,
    NodeType,
    RelationshipType,
    GraphQuery,
    QueryResult,
    BelievePropagation,
)
from .temporal_reasoning import (
    TemporalReasoner,
    TemporalEvent,
    EventType,
    CausalChain,
    CausalLink,
    TemporalConstraint,
    TemporalRelation,
    CounterfactualWorld,
)
from .semantic_engine import (
    SemanticSpace,
    ConceptEmbedding,
    AnalogyDetector,
    Analogy,
    CrossDomainTransfer,
)
from .knowledge_integrator import (
    KnowledgeIntegrator,
    KnowledgeSource,
    KnowledgeFact,
    Contradiction,
    SourceType,
    ResolutionStrategy,
)
from .orchestrator import (
    ReasoningOrchestrator,
    QueryRouter,
    ReasoningFusion,
    Query,
    ReasoningResult,
    FusedResult,
    QueryType,
    ReasoningEngine,
)

__all__ = [
    # Graph Engine
    "KnowledgeGraph",
    "Node",
    "Relationship",
    "NodeType",
    "RelationshipType",
    "GraphQuery",
    "QueryResult",
    "BelievePropagation",
    # Temporal Reasoning
    "TemporalReasoner",
    "TemporalEvent",
    "EventType",
    "CausalChain",
    "CausalLink",
    "TemporalConstraint",
    "TemporalRelation",
    "CounterfactualWorld",
    # Semantic Engine
    "SemanticSpace",
    "ConceptEmbedding",
    "AnalogyDetector",
    "Analogy",
    "CrossDomainTransfer",
    # Knowledge Integration
    "KnowledgeIntegrator",
    "KnowledgeSource",
    "KnowledgeFact",
    "Contradiction",
    "SourceType",
    "ResolutionStrategy",
    # Orchestrator
    "ReasoningOrchestrator",
    "QueryRouter",
    "ReasoningFusion",
    "Query",
    "ReasoningResult",
    "FusedResult",
    "QueryType",
    "ReasoningEngine",
]
