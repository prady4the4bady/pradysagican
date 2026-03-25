"""
Phase 7 - Graph-Based Reasoning Engine (F621-F625)
====================================================
Neo4j-like graph structure for knowledge representation and reasoning.
Implements semantic relationship discovery, multi-hop reasoning, and belief propagation.

Features:
- Knowledge graph construction and manipulation
- Semantic relationship discovery
- Multi-hop reasoning for complex inference
- Belief propagation for uncertainty quantification
- Graph query language support
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

class RelationshipType(Enum):
    """Types of semantic relationships."""
    CAUSALITY = "causality"
    CORRELATION = "correlation"
    EQUIVALENCE = "equivalence"
    COMPOSITION = "composition"
    INHERITANCE = "inheritance"
    PART_OF = "part_of"
    ATTRIBUTE = "attribute"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"
    CUSTOM = "custom"


class NodeType(Enum):
    """Types of knowledge graph nodes."""
    ENTITY = "entity"
    CONCEPT = "concept"
    EVENT = "event"
    PROPERTY = "property"
    RELATION = "relation"
    BELIEF = "belief"


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class Node:
    """Node in the knowledge graph."""
    id: str
    label: str
    node_type: NodeType
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.node_type.value,
            "properties": self.properties,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


@dataclass
class Relationship:
    """Directed relationship between nodes."""
    id: str
    source_id: str
    target_id: str
    rel_type: RelationshipType
    strength: float = 0.5
    properties: dict[str, Any] = field(default_factory=dict)
    bidirectional: bool = False
    confidence: float = 1.0
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "type": self.rel_type.value,
            "strength": self.strength,
            "properties": self.properties,
            "bidirectional": self.bidirectional,
            "confidence": self.confidence,
            "created_at": self.created_at,
        }


@dataclass
class GraphQuery:
    """Query specification for graph operations."""
    query_type: str  # "path", "neighborhood", "pattern", "semantic"
    source_id: Optional[str] = None
    target_id: Optional[str] = None
    max_hops: int = 3
    relationship_filter: Optional[list[RelationshipType]] = None
    properties_filter: Optional[dict[str, Any]] = None
    confidence_threshold: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_type": self.query_type,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "max_hops": self.max_hops,
            "relationship_filter": [r.value for r in (self.relationship_filter or [])],
            "confidence_threshold": self.confidence_threshold,
        }


@dataclass
class QueryResult:
    """Result of a graph query."""
    paths: list[list[str]] = field(default_factory=list)
    nodes: list[Node] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    confidence: float = 1.0
    execution_time_ms: float = 0.0
    hops_used: int = 0


# ── Knowledge Graph ───────────────────────────────────────────────────────────

class KnowledgeGraph:
    """
    Neo4j-like graph database for semantic knowledge representation.
    Supports multi-hop reasoning and belief propagation.
    """

    def __init__(self, max_nodes: int = 10000, max_relationships: int = 50000) -> None:
        self._nodes: dict[str, Node] = {}
        self._relationships: dict[str, Relationship] = {}
        self._adjacency: dict[str, list[str]] = {}  # node_id -> relationship_ids
        self._reverse_adjacency: dict[str, list[str]] = {}
        self._max_nodes = max_nodes
        self._max_relationships = max_relationships
        self._query_cache: dict[str, QueryResult] = {}
        logger.info(f"Initialized KnowledgeGraph with max_nodes={max_nodes}")

    def add_node(
        self,
        label: str,
        node_type: NodeType,
        properties: Optional[dict[str, Any]] = None,
        confidence: float = 1.0,
        node_id: Optional[str] = None,
    ) -> str:
        """Add a node to the graph."""
        if len(self._nodes) >= self._max_nodes:
            logger.warning(f"Graph at capacity ({self._max_nodes} nodes)")
            return ""

        node_id = node_id or str(uuid.uuid4())[:8]
        if node_id in self._nodes:
            logger.warning(f"Node {node_id} already exists")
            return node_id

        node = Node(
            id=node_id,
            label=label,
            node_type=node_type,
            properties=properties or {},
            confidence=confidence,
        )
        self._nodes[node_id] = node
        self._adjacency[node_id] = []
        self._reverse_adjacency[node_id] = []

        logger.debug(f"Added node {node_id}: {label}")
        return node_id

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType,
        strength: float = 0.5,
        properties: Optional[dict[str, Any]] = None,
        bidirectional: bool = False,
        confidence: float = 1.0,
    ) -> str:
        """Add a relationship between two nodes."""
        if len(self._relationships) >= self._max_relationships:
            logger.warning(f"Graph at capacity ({self._max_relationships} relationships)")
            return ""

        if source_id not in self._nodes or target_id not in self._nodes:
            logger.error(f"Source or target node not found")
            return ""

        rel_id = str(uuid.uuid4())[:8]
        relationship = Relationship(
            id=rel_id,
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            strength=strength,
            properties=properties or {},
            bidirectional=bidirectional,
            confidence=confidence,
        )
        self._relationships[rel_id] = relationship
        self._adjacency[source_id].append(rel_id)
        self._reverse_adjacency[target_id].append(rel_id)

        if bidirectional:
            rev_id = str(uuid.uuid4())[:8]
            reverse_rel = Relationship(
                id=rev_id,
                source_id=target_id,
                target_id=source_id,
                rel_type=rel_type,
                strength=strength,
                properties=properties or {},
                bidirectional=True,
                confidence=confidence,
            )
            self._relationships[rev_id] = reverse_rel
            self._adjacency[target_id].append(rev_id)
            self._reverse_adjacency[source_id].append(rev_id)

        logger.debug(f"Added relationship {rel_id}: {source_id} -> {target_id}")
        return rel_id

    def get_node(self, node_id: str) -> Optional[Node]:
        """Retrieve a node by ID."""
        return self._nodes.get(node_id)

    def get_relationship(self, rel_id: str) -> Optional[Relationship]:
        """Retrieve a relationship by ID."""
        return self._relationships.get(rel_id)

    def query(self, query: GraphQuery) -> QueryResult:
        """Execute a graph query."""
        start_time = time.time()

        if query.query_type == "path":
            result = self._query_path(query)
        elif query.query_type == "neighborhood":
            result = self._query_neighborhood(query)
        elif query.query_type == "pattern":
            result = self._query_pattern(query)
        elif query.query_type == "semantic":
            result = self._query_semantic(query)
        else:
            logger.error(f"Unknown query type: {query.query_type}")
            result = QueryResult()

        result.execution_time_ms = (time.time() - start_time) * 1000
        self._query_cache[json.dumps(query.to_dict())] = result
        return result

    def _query_path(self, query: GraphQuery) -> QueryResult:
        """Find paths between two nodes."""
        if not query.source_id or not query.target_id:
            return QueryResult()

        paths = self._find_paths(
            query.source_id,
            query.target_id,
            max_depth=query.max_hops,
            rel_filter=query.relationship_filter,
        )

        result = QueryResult(paths=paths, hops_used=query.max_hops)
        if paths:
            result.confidence = min(1.0, 1.0 - len(paths[0]) / 10)
        return result

    def _query_neighborhood(self, query: GraphQuery) -> QueryResult:
        """Find all neighbors within N hops."""
        if not query.source_id:
            return QueryResult()

        nodes, relationships = self._get_neighborhood(
            query.source_id, query.max_hops, query.relationship_filter
        )

        return QueryResult(nodes=nodes, relationships=relationships, hops_used=query.max_hops)

    def _query_pattern(self, query: GraphQuery) -> QueryResult:
        """Find patterns in the graph."""
        result = QueryResult()
        nodes_list = list(self._nodes.values())

        for node in nodes_list:
            if query.properties_filter:
                if all(
                    node.properties.get(k) == v
                    for k, v in query.properties_filter.items()
                ):
                    result.nodes.append(node)

        return result

    def _query_semantic(self, query: GraphQuery) -> QueryResult:
        """Semantic similarity search."""
        if not query.source_id:
            return QueryResult()

        source_node = self._nodes.get(query.source_id)
        if not source_node:
            return QueryResult()

        similar_nodes = []
        for node in self._nodes.values():
            if node.id == query.source_id:
                continue
            similarity = self._calculate_semantic_similarity(source_node, node)
            if similarity >= query.confidence_threshold:
                similar_nodes.append((node, similarity))

        similar_nodes.sort(key=lambda x: x[1], reverse=True)
        return QueryResult(
            nodes=[n[0] for n in similar_nodes[:10]],
            confidence=similar_nodes[0][1] if similar_nodes else 0.0,
        )

    def _find_paths(
        self,
        source: str,
        target: str,
        max_depth: int = 3,
        rel_filter: Optional[list[RelationshipType]] = None,
    ) -> list[list[str]]:
        """Find all paths between source and target using BFS."""
        if source not in self._nodes or target not in self._nodes:
            return []

        paths = []
        visited_per_path: dict[str, bool] = {source: True}
        queue = [(source, [source], visited_per_path)]

        while queue:
            current, path, visited = queue.pop(0)
            if len(path) > max_depth + 1:
                continue

            if current == target:
                paths.append(path)
                continue

            for rel_id in self._adjacency.get(current, []):
                rel = self._relationships[rel_id]
                if rel_filter and rel.rel_type not in rel_filter:
                    continue

                next_node = rel.target_id
                if next_node not in visited:
                    new_visited = visited.copy()
                    new_visited[next_node] = True
                    queue.append((next_node, path + [next_node], new_visited))

        return paths

    def _get_neighborhood(
        self,
        node_id: str,
        depth: int,
        rel_filter: Optional[list[RelationshipType]] = None,
    ) -> tuple[list[Node], list[Relationship]]:
        """Get all nodes and relationships within N hops."""
        nodes_set = {node_id}
        rels_set = set()
        current_level = {node_id}

        for _ in range(depth):
            next_level = set()
            for current in current_level:
                for rel_id in self._adjacency.get(current, []):
                    rel = self._relationships[rel_id]
                    if rel_filter and rel.rel_type not in rel_filter:
                        continue

                    rels_set.add(rel_id)
                    if rel.target_id not in nodes_set:
                        next_level.add(rel.target_id)
                        nodes_set.add(rel.target_id)

            current_level = next_level

        nodes = [self._nodes[n_id] for n_id in nodes_set if n_id in self._nodes]
        relationships = [self._relationships[r_id] for r_id in rels_set]
        return nodes, relationships

    def _calculate_semantic_similarity(self, node1: Node, node2: Node) -> float:
        """Calculate semantic similarity between two nodes."""
        if node1.node_type != node2.node_type:
            similarity = 0.1
        else:
            similarity = 0.5

        common_props = set(node1.properties.keys()) & set(node2.properties.keys())
        if common_props:
            similarity += 0.3 * len(common_props) / max(
                len(node1.properties), len(node2.properties), 1
            )

        return min(1.0, similarity * node1.confidence * node2.confidence)

    def multi_hop_reasoning(
        self, query: str, max_hops: int = 5, confidence_threshold: float = 0.5
    ) -> dict[str, Any]:
        """
        Perform multi-hop reasoning by traversing the graph.
        Returns conclusions drawn from multi-step inference.
        """
        logger.info(f"Starting multi-hop reasoning: {query}")

        results = {
            "query": query,
            "max_hops": max_hops,
            "conclusions": [],
            "confidence": 0.0,
            "hops_performed": 0,
        }

        reasoning_queue = [(query, 0)]
        visited_queries = set()

        while reasoning_queue and results["hops_performed"] < max_hops:
            current_query, hop_count = reasoning_queue.pop(0)

            if current_query in visited_queries:
                continue
            visited_queries.add(current_query)

            candidates = self._find_related_nodes(current_query)
            for candidate in candidates:
                if candidate.confidence >= confidence_threshold:
                    results["conclusions"].append(
                        {
                            "content": candidate.label,
                            "confidence": candidate.confidence,
                            "hop_level": hop_count,
                        }
                    )

                    if hop_count < max_hops - 1:
                        reasoning_queue.append((candidate.label, hop_count + 1))

            results["hops_performed"] = hop_count + 1

        if results["conclusions"]:
            confidences = [c["confidence"] for c in results["conclusions"]]
            results["confidence"] = sum(confidences) / len(confidences)

        logger.info(f"Multi-hop reasoning completed: {len(results['conclusions'])} conclusions")
        return results

    def _find_related_nodes(self, query: str, limit: int = 5) -> list[Node]:
        """Find nodes related to a query string."""
        related = []
        query_lower = query.lower()

        for node in self._nodes.values():
            if query_lower in node.label.lower() or any(
                query_lower in str(v).lower() for v in node.properties.values()
            ):
                related.append(node)

        return sorted(related, key=lambda n: n.confidence, reverse=True)[:limit]

    def graph_stats(self) -> dict[str, Any]:
        """Get statistics about the graph."""
        return {
            "num_nodes": len(self._nodes),
            "num_relationships": len(self._relationships),
            "max_nodes": self._max_nodes,
            "max_relationships": self._max_relationships,
            "node_types": {
                nt.value: len([n for n in self._nodes.values() if n.node_type == nt])
                for nt in NodeType
            },
            "relationship_types": {
                rt.value: len([r for r in self._relationships.values() if r.rel_type == rt])
                for rt in RelationshipType
            },
        }

    def export_graph(self) -> dict[str, Any]:
        """Export graph to dictionary format."""
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "relationships": [r.to_dict() for r in self._relationships.values()],
            "stats": self.graph_stats(),
        }


# ── Belief Propagation ────────────────────────────────────────────────────────

class BelievePropagation:
    """
    Uncertainty quantification and belief propagation over the graph.
    Propagates confidence values through relationships.
    """

    def __init__(self, graph: KnowledgeGraph, damping_factor: float = 0.85) -> None:
        self._graph = graph
        self._damping_factor = damping_factor
        self._belief_history: dict[str, list[float]] = {}

    def propagate_beliefs(
        self, iterations: int = 10, convergence_threshold: float = 0.01
    ) -> dict[str, float]:
        """
        Propagate belief values through the graph.
        Returns node confidences after convergence.
        """
        logger.info(f"Starting belief propagation ({iterations} iterations)")

        current_beliefs = {
            node_id: node.confidence for node_id, node in self._graph._nodes.items()
        }
        previous_beliefs = current_beliefs.copy()

        for iteration in range(iterations):
            new_beliefs = current_beliefs.copy()

            for node_id, node in self._graph._nodes.items():
                incoming_beliefs = []

                for rel_id in self._graph._reverse_adjacency.get(node_id, []):
                    rel = self._graph._relationships[rel_id]
                    source_node = self._graph._nodes.get(rel.source_id)
                    if source_node:
                        belief_value = (
                            current_beliefs.get(rel.source_id, 0.5)
                            * rel.strength
                            * rel.confidence
                        )
                        incoming_beliefs.append(belief_value)

                if incoming_beliefs:
                    propagated = sum(incoming_beliefs) / len(incoming_beliefs)
                    new_beliefs[node_id] = (
                        self._damping_factor * propagated
                        + (1 - self._damping_factor) * current_beliefs[node_id]
                    )

            max_change = max(
                abs(new_beliefs.get(n, 0) - previous_beliefs.get(n, 0))
                for n in current_beliefs
            )

            current_beliefs = new_beliefs
            if max_change < convergence_threshold:
                logger.info(f"Belief propagation converged at iteration {iteration}")
                break

        for node_id, belief in current_beliefs.items():
            if node_id not in self._belief_history:
                self._belief_history[node_id] = []
            self._belief_history[node_id].append(belief)

        logger.info(f"Belief propagation completed after {iteration + 1} iterations")
        return current_beliefs

    def get_belief_trajectory(self, node_id: str) -> list[float]:
        """Get the history of belief values for a node."""
        return self._belief_history.get(node_id, [])
