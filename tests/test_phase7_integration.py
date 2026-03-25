"""Test suite for Phase 7 Integration (F636-F645) - Multi-engine coordination."""

import pytest
import numpy as np
import time
from unittest.mock import Mock, patch, MagicMock

from pradysagican.core.intelligence.orchestrator import (
    ReasoningOrchestrator,
    QueryRouter,
    ReasoningFusion,
    Query,
    ReasoningResult,
    FusedResult,
    QueryType,
    ReasoningEngine,
)
from pradysagican.core.intelligence.graph_engine import KnowledgeGraph, NodeType
from pradysagican.core.intelligence.temporal_reasoning import TemporalReasoner, EventType
from pradysagican.core.intelligence.semantic_engine import SemanticSpace
from pradysagican.core.intelligence.knowledge_integrator import (
    KnowledgeIntegrator,
    SourceType,
    ResolutionStrategy,
)


class TestQueryRouter:
    """Test QueryRouter functionality."""

    def test_router_initialization(self):
        """Test router initialization."""
        router = QueryRouter()
        assert len(router._routing_rules) > 0

    def test_route_factual_query(self):
        """Test routing factual query."""
        router = QueryRouter()
        query = Query(
            query_id="q1",
            content="What is 2+2?",
            query_type=QueryType.FACTUAL,
        )
        engines = router.route_query(query)
        assert len(engines) > 0
        assert any(e in engines for e in [ReasoningEngine.KNOWLEDGE, ReasoningEngine.GRAPH])

    def test_route_causal_query(self):
        """Test routing causal query."""
        router = QueryRouter()
        query = Query(
            query_id="q2",
            content="Why did X cause Y?",
            query_type=QueryType.CAUSAL,
        )
        engines = router.route_query(query)
        assert any(
            e in engines for e in [ReasoningEngine.GRAPH, ReasoningEngine.TEMPORAL]
        )

    def test_route_counterfactual_query(self):
        """Test routing counterfactual query."""
        router = QueryRouter()
        query = Query(
            query_id="q3",
            content="What if X happened?",
            query_type=QueryType.COUNTERFACTUAL,
        )
        engines = router.route_query(query)
        assert len(engines) > 0

    def test_custom_routing_rule(self):
        """Test adding custom routing rules."""
        router = QueryRouter()
        custom_engines = [ReasoningEngine.SEMANTIC, ReasoningEngine.GRAPH]

        router.add_routing_rule(QueryType.ANALOGICAL, custom_engines)

        query = Query(
            query_id="q4",
            content="What's analogous?",
            query_type=QueryType.ANALOGICAL,
        )
        engines = router.route_query(query)
        assert engines == custom_engines

    def test_hybrid_query_routing(self):
        """Test hybrid query routing."""
        router = QueryRouter()
        query = Query(
            query_id="q5",
            content="Complex reasoning",
            query_type=QueryType.HYBRID,
        )
        engines = router.route_query(query)
        assert len(engines) >= 2


class TestReasoningFusion:
    """Test ReasoningFusion functionality."""

    def test_fusion_initialization(self):
        """Test fusion initialization."""
        fusion = ReasoningFusion(fusion_method="weighted_confidence")
        assert fusion._fusion_method == "weighted_confidence"

    def test_fuse_single_result(self):
        """Test fusing single result."""
        fusion = ReasoningFusion()

        result = ReasoningResult(
            engine=ReasoningEngine.GRAPH,
            answer="Answer 1",
            confidence=0.8,
            metadata={"query_id": "q1"},
        )

        fused = fusion.fuse_results([result])
        assert fused.final_answer == "Answer 1"
        assert fused.confidence == 0.8

    def test_fuse_multiple_results_consensus(self):
        """Test fusing multiple results with consensus."""
        fusion = ReasoningFusion(fusion_method="consensus")

        results = [
            ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Answer A",
                confidence=0.9,
                metadata={"query_id": "q1"},
            ),
            ReasoningResult(
                engine=ReasoningEngine.TEMPORAL,
                answer="Answer A",
                confidence=0.85,
                metadata={"query_id": "q1"},
            ),
        ]

        fused = fusion.fuse_results(results)
        assert fused.consensus_score > 0.5

    def test_fuse_conflicting_results(self):
        """Test fusing conflicting results."""
        fusion = ReasoningFusion(fusion_method="majority_vote")

        results = [
            ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Answer A",
                confidence=0.7,
                metadata={"query_id": "q1"},
            ),
            ReasoningResult(
                engine=ReasoningEngine.TEMPORAL,
                answer="Answer B",
                confidence=0.6,
                metadata={"query_id": "q1"},
            ),
            ReasoningResult(
                engine=ReasoningEngine.SEMANTIC,
                answer="Answer A",
                confidence=0.75,
                metadata={"query_id": "q1"},
            ),
        ]

        fused = fusion.fuse_results(results)
        assert fused.final_answer != ""

    def test_fusion_methods(self):
        """Test different fusion methods."""
        results = [
            ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Result",
                confidence=0.8,
                metadata={"query_id": "q1"},
            ),
            ReasoningResult(
                engine=ReasoningEngine.SEMANTIC,
                answer="Result",
                confidence=0.85,
                metadata={"query_id": "q1"},
            ),
        ]

        for method in [
            "weighted_confidence",
            "consensus",
            "majority_vote",
            "ensemble",
        ]:
            fusion = ReasoningFusion(fusion_method=method)
            fused = fusion.fuse_results(results)
            assert 0.0 <= fused.confidence <= 1.0

    def test_fusion_history(self):
        """Test fusion history tracking."""
        fusion = ReasoningFusion()

        results = [
            ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Test",
                confidence=0.7,
                metadata={"query_id": "q1"},
            )
        ]

        fusion.fuse_results(results)
        fusion.fuse_results(results)

        history = fusion.get_fusion_history()
        assert len(history) == 2


class TestReasoningOrchestrator:
    """Test ReasoningOrchestrator functionality."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        orchestrator = ReasoningOrchestrator()
        assert len(orchestrator._engines) == 0

    def test_register_engine(self):
        """Test registering engines."""
        orchestrator = ReasoningOrchestrator()

        def mock_engine(query: Query) -> ReasoningResult:
            return ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Test",
                confidence=0.5,
            )

        orchestrator.register_engine(ReasoningEngine.GRAPH, mock_engine)
        assert ReasoningEngine.GRAPH in orchestrator._engines

    def test_process_simple_query(self):
        """Test processing a simple query."""
        orchestrator = ReasoningOrchestrator()

        def mock_engine(query: Query) -> ReasoningResult:
            return ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Test Answer",
                confidence=0.8,
                metadata={"query_id": query.query_id},
            )

        orchestrator.register_engine(ReasoningEngine.GRAPH, mock_engine)

        query = Query(
            query_id="q1",
            content="Test query",
            query_type=QueryType.FACTUAL,
        )

        result = orchestrator.process_query(query)
        assert result.final_answer != ""

    def test_process_query_with_multiple_engines(self):
        """Test processing with multiple engines."""
        orchestrator = ReasoningOrchestrator()

        def engine1(query: Query) -> ReasoningResult:
            return ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Answer from Graph",
                confidence=0.8,
                metadata={"query_id": query.query_id},
            )

        def engine2(query: Query) -> ReasoningResult:
            return ReasoningResult(
                engine=ReasoningEngine.TEMPORAL,
                answer="Answer from Temporal",
                confidence=0.75,
                metadata={"query_id": query.query_id},
            )

        orchestrator.register_engine(ReasoningEngine.GRAPH, engine1)
        orchestrator.register_engine(ReasoningEngine.TEMPORAL, engine2)

        query = Query(
            query_id="q2",
            content="Complex query",
            query_type=QueryType.CAUSAL,
        )

        result = orchestrator.process_query(query)
        assert result.confidence >= 0.0

    def test_process_batch_queries(self):
        """Test processing batch of queries."""
        orchestrator = ReasoningOrchestrator()

        def mock_engine(query: Query) -> ReasoningResult:
            return ReasoningResult(
                engine=ReasoningEngine.SYMBOLIC,
                answer=f"Answer for {query.query_id}",
                confidence=0.7,
                metadata={"query_id": query.query_id},
            )

        orchestrator.register_engine(ReasoningEngine.SYMBOLIC, mock_engine)

        queries = [
            Query(query_id=f"q{i}", content=f"Query {i}", query_type=QueryType.FACTUAL)
            for i in range(3)
        ]

        results = orchestrator.process_batch(queries)
        assert len(results) == 3

    def test_query_caching(self):
        """Test query result caching."""
        orchestrator = ReasoningOrchestrator()
        call_count = {"count": 0}

        def mock_engine(query: Query) -> ReasoningResult:
            call_count["count"] += 1
            return ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Cached Answer",
                confidence=0.9,
                metadata={"query_id": query.query_id},
            )

        orchestrator.register_engine(ReasoningEngine.GRAPH, mock_engine)

        query = Query(
            query_id="q1",
            content="Same query",
            query_type=QueryType.FACTUAL,
        )

        result1 = orchestrator.process_query(query, use_cache=True)
        result2 = orchestrator.process_query(query, use_cache=True)

        assert call_count["count"] == 1

    def test_cache_bypass(self):
        """Test bypassing cache."""
        orchestrator = ReasoningOrchestrator()

        def mock_engine(query: Query) -> ReasoningResult:
            return ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Answer",
                confidence=0.5,
                metadata={"query_id": query.query_id},
            )

        orchestrator.register_engine(ReasoningEngine.GRAPH, mock_engine)

        query = Query(
            query_id="q1",
            content="Query",
            query_type=QueryType.FACTUAL,
        )

        orchestrator.process_query(query, use_cache=True)
        orchestrator.clear_cache()

        assert len(orchestrator._results_cache) == 0

    def test_get_routing_suggestions(self):
        """Test getting routing suggestions."""
        orchestrator = ReasoningOrchestrator()

        query = Query(
            query_id="q1",
            content="Causal query",
            query_type=QueryType.CAUSAL,
        )

        suggestions = orchestrator.get_routing_suggestions(query)
        assert "suggested_engines" in suggestions
        assert "query_type" in suggestions

    def test_orchestrator_stats(self):
        """Test getting orchestrator stats."""
        orchestrator = ReasoningOrchestrator()

        def mock_engine(query: Query) -> ReasoningResult:
            return ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer="Test",
                confidence=0.5,
                metadata={"query_id": query.query_id},
            )

        orchestrator.register_engine(ReasoningEngine.GRAPH, mock_engine)
        stats = orchestrator.get_stats()

        assert "registered_engines" in stats
        assert "cached_results" in stats


class TestQuery:
    """Test Query data structure."""

    def test_query_creation(self):
        """Test query creation."""
        query = Query(
            query_id="q1",
            content="Test question",
            query_type=QueryType.FACTUAL,
            priority=3,
        )
        assert query.query_id == "q1"
        assert query.priority == 3

    def test_query_serialization(self):
        """Test query serialization."""
        query = Query(
            query_id="q1",
            content="Question",
            query_type=QueryType.CAUSAL,
            parameters={"depth": 5},
        )
        query_dict = query.to_dict()
        assert query_dict["query_id"] == "q1"
        assert query_dict["parameters"]["depth"] == 5


class TestReasoningResult:
    """Test ReasoningResult data structure."""

    def test_result_creation(self):
        """Test result creation."""
        result = ReasoningResult(
            engine=ReasoningEngine.GRAPH,
            answer="Test Answer",
            confidence=0.85,
            reasoning_steps=["Step 1", "Step 2"],
        )
        assert result.answer == "Test Answer"
        assert len(result.reasoning_steps) == 2

    def test_result_serialization(self):
        """Test result serialization."""
        result = ReasoningResult(
            engine=ReasoningEngine.TEMPORAL,
            answer="Result",
            confidence=0.7,
        )
        result_dict = result.to_dict()
        assert result_dict["engine"] == "temporal"
        assert result_dict["confidence"] == 0.7


# Integration Scenarios

class TestMultiEngineReasoning:
    """Integration tests for multi-engine reasoning."""

    def test_graph_based_reasoning(self):
        """Test graph-based reasoning engine."""
        from pradysagican.core.intelligence.graph_engine import RelationshipType

        graph = KnowledgeGraph()

        n1 = graph.add_node("A", NodeType.ENTITY)
        n2 = graph.add_node("B", NodeType.ENTITY)
        graph.add_relationship(n1, n2, RelationshipType.CAUSALITY)

        def graph_engine(query: Query) -> ReasoningResult:
            paths = graph.multi_hop_reasoning(query.content)
            return ReasoningResult(
                engine=ReasoningEngine.GRAPH,
                answer=f"Graph found {len(paths.get('conclusions', []))} conclusions",
                confidence=paths.get("confidence", 0.5),
                metadata={"query_id": query.query_id},
            )

        orchestrator = ReasoningOrchestrator()
        orchestrator.register_engine(ReasoningEngine.GRAPH, graph_engine)

        query = Query(
            query_id="q1",
            content="A causes B",
            query_type=QueryType.GRAPH,
        )

        result = orchestrator.process_query(query)
        assert result.final_answer != ""

    def test_temporal_reasoning_integration(self):
        """Test temporal reasoning integration."""
        reasoner = TemporalReasoner()
        current_time = time.time()

        e1 = reasoner.add_event("Event1", EventType.ACTION, current_time)
        e2 = reasoner.add_event("Event2", EventType.OUTCOME, current_time + 1)
        reasoner.add_causal_link(e1, e2)

        def temporal_engine(query: Query) -> ReasoningResult:
            paths = reasoner.find_causal_paths(e1)
            return ReasoningResult(
                engine=ReasoningEngine.TEMPORAL,
                answer=f"Found {len(paths)} causal paths",
                confidence=0.8 if paths else 0.3,
                metadata={"query_id": query.query_id},
            )

        orchestrator = ReasoningOrchestrator()
        orchestrator.register_engine(ReasoningEngine.TEMPORAL, temporal_engine)

        query = Query(
            query_id="q1",
            content="Temporal reasoning",
            query_type=QueryType.TEMPORAL,
        )

        result = orchestrator.process_query(query)
        assert result.confidence >= 0.0

    def test_semantic_reasoning_integration(self):
        """Test semantic reasoning integration."""
        space = SemanticSpace(dimensionality=10)
        space.embed_concept("Dog")
        space.embed_concept("Cat")

        def semantic_engine(query: Query) -> ReasoningResult:
            query_emb = np.random.randn(10)
            neighbors = space.nearest_neighbors(query_emb, limit=2)
            return ReasoningResult(
                engine=ReasoningEngine.SEMANTIC,
                answer=f"Found {len(neighbors)} semantic neighbors",
                confidence=0.7,
                metadata={"query_id": query.query_id},
            )

        orchestrator = ReasoningOrchestrator()
        orchestrator.register_engine(ReasoningEngine.SEMANTIC, semantic_engine)

        query = Query(
            query_id="q1",
            content="Semantic query",
            query_type=QueryType.SEMANTIC,
        )

        result = orchestrator.process_query(query)
        assert result.final_answer != ""

    def test_knowledge_integration_engine(self):
        """Test knowledge integration engine."""
        integrator = KnowledgeIntegrator()
        integrator.register_source(
            "Source1", SourceType.OBSERVATION, credibility=0.9
        )
        integrator.register_source("Source2", SourceType.INFERENCE, credibility=0.7)

        def knowledge_engine(query: Query) -> ReasoningResult:
            integration = integrator.integrate_sources()
            return ReasoningResult(
                engine=ReasoningEngine.KNOWLEDGE,
                answer=f"Integrated {len(integration['merged_facts'])} facts",
                confidence=integration.get("integration_confidence", 0.5),
                metadata={"query_id": query.query_id},
            )

        orchestrator = ReasoningOrchestrator()
        orchestrator.register_engine(ReasoningEngine.KNOWLEDGE, knowledge_engine)

        query = Query(
            query_id="q1",
            content="Integration query",
            query_type=QueryType.INTEGRATION,
        )

        result = orchestrator.process_query(query)
        assert result.confidence >= 0.0

    def test_full_reasoning_pipeline(self):
        """Test complete multi-engine reasoning pipeline."""
        orchestrator = ReasoningOrchestrator()

        def engine1(q: Query) -> ReasoningResult:
            return ReasoningResult(
                ReasoningEngine.GRAPH,
                "Graph answer",
                0.8,
                metadata={"query_id": q.query_id},
            )

        def engine2(q: Query) -> ReasoningResult:
            return ReasoningResult(
                ReasoningEngine.TEMPORAL,
                "Temporal answer",
                0.75,
                metadata={"query_id": q.query_id},
            )

        def engine3(q: Query) -> ReasoningResult:
            return ReasoningResult(
                ReasoningEngine.SEMANTIC,
                "Semantic answer",
                0.7,
                metadata={"query_id": q.query_id},
            )

        orchestrator.register_engine(ReasoningEngine.GRAPH, engine1)
        orchestrator.register_engine(ReasoningEngine.TEMPORAL, engine2)
        orchestrator.register_engine(ReasoningEngine.SEMANTIC, engine3)

        query = Query(
            query_id="complex_q",
            content="Complex reasoning task",
            query_type=QueryType.HYBRID,
        )

        result = orchestrator.process_query(query)
        assert result.final_answer != ""
        assert result.confidence >= 0.0
        assert len(result.contributing_engines) > 0
