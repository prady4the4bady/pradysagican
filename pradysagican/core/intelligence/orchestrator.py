"""
Phase 7 - Reasoning Orchestrator (F641-F645)
==============================================
Routes queries to appropriate reasoning engines and combines their results.

Features:
- Query routing based on type and characteristics
- Multi-engine reasoning coordination
- Result fusion and consensus building
- Confidence scoring and aggregation
- Adaptive reasoning strategy selection
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ── Enums ─────────────────────────────────────────────────────────────────────

class QueryType(Enum):
    """Types of queries for routing."""
    FACTUAL = "factual"
    CAUSAL = "causal"
    ANALOGICAL = "analogical"
    TEMPORAL = "temporal"
    SEMANTIC = "semantic"
    GRAPH = "graph"
    COUNTERFACTUAL = "counterfactual"
    INTEGRATION = "integration"
    HYBRID = "hybrid"


class ReasoningEngine(Enum):
    """Available reasoning engines."""
    GRAPH = "graph"
    TEMPORAL = "temporal"
    SEMANTIC = "semantic"
    KNOWLEDGE = "knowledge"
    SYMBOLIC = "symbolic"


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class Query:
    """Structured query for the reasoning system."""
    query_id: str
    content: str
    query_type: QueryType
    priority: int = 5  # 1 (highest) to 10 (lowest)
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "content": self.content,
            "type": self.query_type.value,
            "priority": self.priority,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


@dataclass
class ReasoningResult:
    """Result from a reasoning engine."""
    engine: ReasoningEngine
    answer: str
    confidence: float = 0.5
    explanation: str = ""
    reasoning_steps: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine.value,
            "answer": self.answer,
            "confidence": self.confidence,
            "explanation": self.explanation,
            "reasoning_steps": self.reasoning_steps,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


@dataclass
class FusedResult:
    """Result after fusing multiple reasoning outputs."""
    query_id: str
    final_answer: str
    confidence: float = 0.5
    contributing_engines: list[ReasoningEngine] = field(default_factory=list)
    all_results: list[ReasoningResult] = field(default_factory=list)
    fusion_method: str = ""
    consensus_score: float = 0.0
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_id": self.query_id,
            "final_answer": self.final_answer,
            "confidence": self.confidence,
            "engines": [e.value for e in self.contributing_engines],
            "fusion_method": self.fusion_method,
            "consensus_score": self.consensus_score,
            "execution_time_ms": self.execution_time_ms,
        }


# ── Query Router ───────────────────────────────────────────────────────────────

class QueryRouter:
    """Routes queries to appropriate reasoning engines."""

    def __init__(self) -> None:
        self._routing_rules: dict[QueryType, list[ReasoningEngine]] = {
            QueryType.FACTUAL: [ReasoningEngine.KNOWLEDGE, ReasoningEngine.GRAPH],
            QueryType.CAUSAL: [ReasoningEngine.GRAPH, ReasoningEngine.TEMPORAL],
            QueryType.ANALOGICAL: [ReasoningEngine.SEMANTIC],
            QueryType.TEMPORAL: [ReasoningEngine.TEMPORAL, ReasoningEngine.GRAPH],
            QueryType.SEMANTIC: [ReasoningEngine.SEMANTIC, ReasoningEngine.KNOWLEDGE],
            QueryType.GRAPH: [ReasoningEngine.GRAPH],
            QueryType.COUNTERFACTUAL: [
                ReasoningEngine.TEMPORAL,
                ReasoningEngine.GRAPH,
                ReasoningEngine.SYMBOLIC,
            ],
            QueryType.INTEGRATION: [
                ReasoningEngine.KNOWLEDGE,
                ReasoningEngine.SYMBOLIC,
            ],
            QueryType.HYBRID: [
                ReasoningEngine.GRAPH,
                ReasoningEngine.TEMPORAL,
                ReasoningEngine.SEMANTIC,
            ],
        }
        logger.info("Initialized QueryRouter")

    def route_query(self, query: Query) -> list[ReasoningEngine]:
        """Determine which engines should process this query."""
        engines = self._routing_rules.get(query.query_type, [ReasoningEngine.SYMBOLIC])
        logger.debug(f"Routed {query.query_id} to {len(engines)} engines: {[e.value for e in engines]}")
        return engines

    def add_routing_rule(
        self, query_type: QueryType, engines: list[ReasoningEngine]
    ) -> None:
        """Add or update a routing rule."""
        self._routing_rules[query_type] = engines
        logger.debug(f"Updated routing rule for {query_type.value}")

    def get_routing_rules(self) -> dict[QueryType, list[ReasoningEngine]]:
        """Get all routing rules."""
        return self._routing_rules


# ── Reasoning Fusion ──────────────────────────────────────────────────────────

class ReasoningFusion:
    """Combines results from multiple reasoning engines."""

    def __init__(self, fusion_method: str = "weighted_confidence") -> None:
        self._fusion_method = fusion_method
        self._fusion_history: list[dict[str, Any]] = []
        logger.info(f"Initialized ReasoningFusion (method={fusion_method})")

    def fuse_results(self, results: list[ReasoningResult]) -> FusedResult:
        """Combine multiple reasoning results into a single answer."""
        if not results:
            logger.warning("No results to fuse")
            return FusedResult(
                query_id="",
                final_answer="",
                confidence=0.0,
            )

        if self._fusion_method == "weighted_confidence":
            fused = self._fuse_by_weighted_confidence(results)
        elif self._fusion_method == "consensus":
            fused = self._fuse_by_consensus(results)
        elif self._fusion_method == "majority_vote":
            fused = self._fuse_by_majority_vote(results)
        elif self._fusion_method == "ensemble":
            fused = self._fuse_by_ensemble(results)
        else:
            fused = self._fuse_by_weighted_confidence(results)

        self._fusion_history.append(fused.to_dict())
        logger.info(
            f"Fused {len(results)} results: confidence={fused.confidence:.2f}, consensus={fused.consensus_score:.2f}"
        )

        return fused

    def _fuse_by_weighted_confidence(self, results: list[ReasoningResult]) -> FusedResult:
        """Fuse by weighting results by confidence."""
        total_confidence = sum(r.confidence for r in results)
        if total_confidence == 0:
            average_answer = " ".join(r.answer for r in results[:3])
            confidence = 0.3
        else:
            weighted_answers = [
                (r.answer, r.confidence / total_confidence) for r in results
            ]
            average_answer = weighted_answers[0][0]
            confidence = sum(r.confidence for r in results) / len(results)

        consensus = self._calculate_consensus(results)

        return FusedResult(
            query_id=results[0].metadata.get("query_id", ""),
            final_answer=average_answer,
            confidence=min(1.0, confidence),
            contributing_engines=[r.engine for r in results],
            all_results=results,
            fusion_method=self._fusion_method,
            consensus_score=consensus,
        )

    def _fuse_by_consensus(self, results: list[ReasoningResult]) -> FusedResult:
        """Fuse by finding consensus among results."""
        consensus = self._calculate_consensus(results)

        if consensus > 0.7:
            final_answer = results[0].answer
            confidence = consensus
        else:
            final_answer = " || ".join(r.answer for r in results[:2])
            confidence = 0.5

        return FusedResult(
            query_id=results[0].metadata.get("query_id", ""),
            final_answer=final_answer,
            confidence=confidence,
            contributing_engines=[r.engine for r in results],
            all_results=results,
            fusion_method=self._fusion_method,
            consensus_score=consensus,
        )

    def _fuse_by_majority_vote(self, results: list[ReasoningResult]) -> FusedResult:
        """Fuse by majority vote on answers."""
        answer_counts: dict[str, int] = {}
        for result in results:
            answer = result.answer[:50]
            answer_counts[answer] = answer_counts.get(answer, 0) + 1

        majority_answer = max(answer_counts, key=answer_counts.get) if answer_counts else ""
        majority_count = answer_counts.get(majority_answer, 0)
        confidence = majority_count / len(results) if results else 0.0

        return FusedResult(
            query_id=results[0].metadata.get("query_id", ""),
            final_answer=majority_answer,
            confidence=confidence,
            contributing_engines=[r.engine for r in results],
            all_results=results,
            fusion_method=self._fusion_method,
            consensus_score=confidence,
        )

    def _fuse_by_ensemble(self, results: list[ReasoningResult]) -> FusedResult:
        """Fuse using ensemble aggregation."""
        avg_confidence = sum(r.confidence for r in results) / len(results) if results else 0.0
        consensus = self._calculate_consensus(results)

        combined_reasoning = "\n".join(r.reasoning_steps[0] if r.reasoning_steps else r.explanation for r in results[:3])
        final_answer = combined_reasoning[:200] if combined_reasoning else ""

        return FusedResult(
            query_id=results[0].metadata.get("query_id", ""),
            final_answer=final_answer,
            confidence=min(1.0, avg_confidence + 0.1 * len(results) / 5),
            contributing_engines=[r.engine for r in results],
            all_results=results,
            fusion_method=self._fusion_method,
            consensus_score=consensus,
        )

    def _calculate_consensus(self, results: list[ReasoningResult]) -> float:
        """Calculate consensus level among results."""
        if len(results) < 2:
            return 1.0

        avg_confidence = sum(r.confidence for r in results) / len(results)
        confidence_variance = sum(
            (r.confidence - avg_confidence) ** 2 for r in results
        ) / len(results)

        consensus_score = max(0.0, 1.0 - (confidence_variance ** 0.5))
        return consensus_score

    def get_fusion_history(self) -> list[dict[str, Any]]:
        """Get history of fusion operations."""
        return self._fusion_history


# ── Reasoning Orchestrator ────────────────────────────────────────────────────

class ReasoningOrchestrator:
    """
    Orchestrates multi-engine reasoning.
    Routes queries, manages engines, and fuses results.
    """

    def __init__(
        self,
        engines: Optional[dict[ReasoningEngine, Callable]] = None,
        fusion_method: str = "weighted_confidence",
    ) -> None:
        self._engines: dict[ReasoningEngine, Callable] = engines or {}
        self._router = QueryRouter()
        self._fusion = ReasoningFusion(fusion_method=fusion_method)
        self._query_queue: list[Query] = []
        self._results_cache: dict[str, FusedResult] = {}
        logger.info(f"Initialized ReasoningOrchestrator with {len(self._engines)} engines")

    def register_engine(self, engine_type: ReasoningEngine, engine_fn: Callable) -> None:
        """Register a reasoning engine."""
        self._engines[engine_type] = engine_fn
        logger.debug(f"Registered engine {engine_type.value}")

    def process_query(self, query: Query, use_cache: bool = True) -> FusedResult:
        """Process a query using multiple reasoning engines."""
        logger.info(f"Processing query {query.query_id}: {query.content[:50]}...")
        start_time = time.time()

        cache_key = query.content
        if use_cache and cache_key in self._results_cache:
            logger.debug("Returning cached result")
            return self._results_cache[cache_key]

        engines_to_use = self._router.route_query(query)
        logger.debug(f"Using engines: {[e.value for e in engines_to_use]}")

        results = []
        for engine_type in engines_to_use:
            if engine_type not in self._engines:
                logger.warning(f"Engine {engine_type.value} not registered")
                continue

            engine_fn = self._engines[engine_type]
            try:
                result = engine_fn(query)
                results.append(result)
            except Exception as e:
                logger.error(f"Engine {engine_type.value} failed: {e}")
                continue

        if not results:
            logger.warning("No engines produced results")
            fused_result = FusedResult(
                query_id=query.query_id,
                final_answer="No answer generated",
                confidence=0.0,
            )
        else:
            fused_result = self._fusion.fuse_results(results)
            fused_result.query_id = query.query_id

        fused_result.execution_time_ms = (time.time() - start_time) * 1000

        if use_cache:
            self._results_cache[cache_key] = fused_result

        logger.info(f"Query processing completed: confidence={fused_result.confidence:.2f}")
        return fused_result

    def process_batch(self, queries: list[Query]) -> list[FusedResult]:
        """Process multiple queries."""
        logger.info(f"Processing batch of {len(queries)} queries")
        results = []

        for query in sorted(queries, key=lambda q: q.priority):
            result = self.process_query(query)
            results.append(result)

        return results

    def get_routing_suggestions(self, query: Query) -> dict[str, Any]:
        """Get routing suggestions for a query without executing."""
        engines = self._router.route_query(query)
        return {
            "query_id": query.query_id,
            "query_type": query.query_type.value,
            "suggested_engines": [e.value for e in engines],
            "available_engines": [e.value for e in self._engines.keys()],
        }

    def get_stats(self) -> dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "registered_engines": list(self._engines.keys()),
            "cached_results": len(self._results_cache),
            "queued_queries": len(self._query_queue),
            "fusion_method": self._fusion._fusion_method,
        }

    def clear_cache(self) -> None:
        """Clear the results cache."""
        self._results_cache.clear()
        logger.info("Cache cleared")
