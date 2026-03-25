"""Test suite for Phase 7 Graph Engine (F621-F625)."""

import pytest
from unittest.mock import Mock, patch
import numpy as np

from pradysagican.core.intelligence.graph_engine import (
    KnowledgeGraph,
    Node,
    Relationship,
    NodeType,
    RelationshipType,
    GraphQuery,
    QueryResult,
    BelievePropagation,
)


class TestNode:
    """Test Node data structure."""

    def test_node_creation(self):
        """Test creating a node."""
        node = Node(
            id="node1",
            label="Entity A",
            node_type=NodeType.ENTITY,
            confidence=0.9,
        )
        assert node.id == "node1"
        assert node.label == "Entity A"
        assert node.node_type == NodeType.ENTITY
        assert node.confidence == 0.9

    def test_node_to_dict(self):
        """Test node serialization."""
        node = Node(
            id="node1",
            label="Test",
            node_type=NodeType.CONCEPT,
            properties={"key": "value"},
        )
        node_dict = node.to_dict()
        assert node_dict["id"] == "node1"
        assert node_dict["type"] == "concept"
        assert node_dict["properties"] == {"key": "value"}


class TestRelationship:
    """Test Relationship data structure."""

    def test_relationship_creation(self):
        """Test creating a relationship."""
        rel = Relationship(
            id="rel1",
            source_id="node1",
            target_id="node2",
            rel_type=RelationshipType.CAUSALITY,
            strength=0.8,
        )
        assert rel.id == "rel1"
        assert rel.source_id == "node1"
        assert rel.target_id == "node2"
        assert rel.rel_type == RelationshipType.CAUSALITY
        assert rel.strength == 0.8

    def test_bidirectional_relationship(self):
        """Test bidirectional relationship flag."""
        rel = Relationship(
            id="rel1",
            source_id="node1",
            target_id="node2",
            rel_type=RelationshipType.EQUIVALENCE,
            bidirectional=True,
        )
        assert rel.bidirectional is True


class TestKnowledgeGraph:
    """Test KnowledgeGraph functionality."""

    def test_graph_initialization(self):
        """Test graph initialization."""
        graph = KnowledgeGraph(max_nodes=100, max_relationships=500)
        assert len(graph._nodes) == 0
        assert len(graph._relationships) == 0

    def test_add_node(self):
        """Test adding nodes to graph."""
        graph = KnowledgeGraph()
        node_id = graph.add_node(
            label="Entity A",
            node_type=NodeType.ENTITY,
            properties={"type": "test"},
        )
        assert node_id in graph._nodes
        assert graph._nodes[node_id].label == "Entity A"

    def test_add_multiple_nodes(self):
        """Test adding multiple nodes."""
        graph = KnowledgeGraph()
        node1 = graph.add_node("Node1", NodeType.ENTITY)
        node2 = graph.add_node("Node2", NodeType.CONCEPT)
        node3 = graph.add_node("Node3", NodeType.EVENT)

        assert len(graph._nodes) == 3
        assert graph._nodes[node1].label == "Node1"
        assert graph._nodes[node2].label == "Node2"
        assert graph._nodes[node3].label == "Node3"

    def test_add_relationship(self):
        """Test adding relationships between nodes."""
        graph = KnowledgeGraph()
        node1 = graph.add_node("A", NodeType.ENTITY)
        node2 = graph.add_node("B", NodeType.ENTITY)

        rel_id = graph.add_relationship(
            node1, node2, RelationshipType.CAUSALITY, strength=0.7
        )
        assert rel_id in graph._relationships
        assert graph._relationships[rel_id].source_id == node1
        assert graph._relationships[rel_id].target_id == node2

    def test_bidirectional_relationship_creation(self):
        """Test bidirectional relationship creation."""
        graph = KnowledgeGraph()
        node1 = graph.add_node("A", NodeType.ENTITY)
        node2 = graph.add_node("B", NodeType.ENTITY)

        rel_id = graph.add_relationship(
            node1, node2, RelationshipType.EQUIVALENCE, bidirectional=True
        )

        assert len(graph._adjacency[node1]) >= 1
        assert len(graph._adjacency[node2]) >= 1

    def test_get_node(self):
        """Test retrieving nodes."""
        graph = KnowledgeGraph()
        node_id = graph.add_node("Test", NodeType.ENTITY)
        node = graph.get_node(node_id)

        assert node is not None
        assert node.label == "Test"

    def test_get_nonexistent_node(self):
        """Test retrieving nonexistent node."""
        graph = KnowledgeGraph()
        node = graph.get_node("nonexistent")
        assert node is None

    def test_path_query(self):
        """Test path finding query."""
        graph = KnowledgeGraph()
        node1 = graph.add_node("A", NodeType.ENTITY)
        node2 = graph.add_node("B", NodeType.ENTITY)
        node3 = graph.add_node("C", NodeType.ENTITY)

        graph.add_relationship(node1, node2, RelationshipType.CAUSALITY)
        graph.add_relationship(node2, node3, RelationshipType.CAUSALITY)

        query = GraphQuery(
            query_type="path",
            source_id=node1,
            target_id=node3,
            max_hops=3,
        )
        result = graph.query(query)

        assert len(result.paths) > 0
        assert node1 in result.paths[0]
        assert node3 in result.paths[0]

    def test_neighborhood_query(self):
        """Test neighborhood discovery."""
        graph = KnowledgeGraph()
        center = graph.add_node("Center", NodeType.ENTITY)
        neighbor1 = graph.add_node("N1", NodeType.ENTITY)
        neighbor2 = graph.add_node("N2", NodeType.ENTITY)

        graph.add_relationship(center, neighbor1, RelationshipType.ATTRIBUTE)
        graph.add_relationship(center, neighbor2, RelationshipType.ATTRIBUTE)

        query = GraphQuery(
            query_type="neighborhood",
            source_id=center,
            max_hops=1,
        )
        result = graph.query(query)

        assert len(result.nodes) >= 2
        assert any(n.id == neighbor1 for n in result.nodes)
        assert any(n.id == neighbor2 for n in result.nodes)

    def test_pattern_query(self):
        """Test pattern matching query."""
        graph = KnowledgeGraph()
        node1 = graph.add_node("Test", NodeType.ENTITY, properties={"status": "active"})
        node2 = graph.add_node("Test", NodeType.ENTITY, properties={"status": "inactive"})

        query = GraphQuery(
            query_type="pattern",
            properties_filter={"status": "active"},
        )
        result = graph.query(query)

        assert len(result.nodes) >= 1
        assert any(n.id == node1 for n in result.nodes)

    def test_semantic_similarity_query(self):
        """Test semantic similarity search."""
        graph = KnowledgeGraph()
        node1 = graph.add_node("Dog", NodeType.CONCEPT)
        node2 = graph.add_node("Animal", NodeType.CONCEPT)

        query = GraphQuery(
            query_type="semantic",
            source_id=node1,
            max_hops=2,
        )
        result = graph.query(query)

        assert result.confidence >= 0.0
        assert result.confidence <= 1.0

    def test_multi_hop_reasoning(self):
        """Test multi-hop reasoning."""
        graph = KnowledgeGraph()
        n1 = graph.add_node("A", NodeType.ENTITY)
        n2 = graph.add_node("B", NodeType.ENTITY)
        n3 = graph.add_node("C", NodeType.ENTITY)

        graph.add_relationship(n1, n2, RelationshipType.CAUSALITY)
        graph.add_relationship(n2, n3, RelationshipType.CAUSALITY)

        result = graph.multi_hop_reasoning("A causes effect", max_hops=2)

        assert "conclusions" in result
        assert result["hops_performed"] >= 0

    def test_graph_stats(self):
        """Test graph statistics."""
        graph = KnowledgeGraph()
        graph.add_node("N1", NodeType.ENTITY)
        graph.add_node("N2", NodeType.CONCEPT)

        stats = graph.graph_stats()
        assert stats["num_nodes"] == 2
        assert "node_types" in stats
        assert "relationship_types" in stats

    def test_export_graph(self):
        """Test graph export."""
        graph = KnowledgeGraph()
        n1 = graph.add_node("Test", NodeType.ENTITY)
        n2 = graph.add_node("Test2", NodeType.CONCEPT)
        graph.add_relationship(n1, n2, RelationshipType.ATTRIBUTE)

        export = graph.export_graph()
        assert "nodes" in export
        assert "relationships" in export
        assert "stats" in export
        assert len(export["nodes"]) == 2
        assert len(export["relationships"]) >= 1

    def test_relationship_filtering(self):
        """Test relationship type filtering."""
        graph = KnowledgeGraph()
        n1 = graph.add_node("A", NodeType.ENTITY)
        n2 = graph.add_node("B", NodeType.ENTITY)
        n3 = graph.add_node("C", NodeType.ENTITY)

        graph.add_relationship(n1, n2, RelationshipType.CAUSALITY)
        graph.add_relationship(n1, n3, RelationshipType.ATTRIBUTE)

        query = GraphQuery(
            query_type="neighborhood",
            source_id=n1,
            relationship_filter=[RelationshipType.CAUSALITY],
        )
        result = graph.query(query)

        causal_rels = [r for r in result.relationships if r.rel_type == RelationshipType.CAUSALITY]
        assert len(causal_rels) > 0

    def test_confidence_threshold(self):
        """Test confidence threshold in queries."""
        graph = KnowledgeGraph()
        n1 = graph.add_node("A", NodeType.ENTITY, confidence=0.9)
        n2 = graph.add_node("B", NodeType.ENTITY, confidence=0.2)

        query = GraphQuery(
            query_type="semantic",
            source_id=n1,
            confidence_threshold=0.5,
        )
        result = graph.query(query)

        assert result.confidence >= 0.0


class TestBelievePropagation:
    """Test Belief Propagation functionality."""

    def test_belief_propagation_initialization(self):
        """Test belief propagation initialization."""
        graph = KnowledgeGraph()
        bp = BelievePropagation(graph)
        assert bp._graph == graph
        assert bp._damping_factor == 0.85

    def test_propagate_beliefs(self):
        """Test belief propagation."""
        graph = KnowledgeGraph()
        n1 = graph.add_node("A", NodeType.ENTITY, confidence=0.9)
        n2 = graph.add_node("B", NodeType.ENTITY, confidence=0.5)
        n3 = graph.add_node("C", NodeType.ENTITY, confidence=0.3)

        graph.add_relationship(n1, n2, RelationshipType.CAUSALITY, strength=0.8)
        graph.add_relationship(n2, n3, RelationshipType.CAUSALITY, strength=0.7)

        bp = BelievePropagation(graph)
        beliefs = bp.propagate_beliefs(iterations=5)

        assert len(beliefs) >= 3
        for node_id, belief_value in beliefs.items():
            assert 0.0 <= belief_value <= 1.0

    def test_belief_trajectory(self):
        """Test belief trajectory tracking."""
        graph = KnowledgeGraph()
        n1 = graph.add_node("A", NodeType.ENTITY, confidence=0.5)

        bp = BelievePropagation(graph)
        bp.propagate_beliefs(iterations=3)

        trajectory = bp.get_belief_trajectory(n1)
        assert len(trajectory) == 1

    def test_damping_factor(self):
        """Test custom damping factor."""
        graph = KnowledgeGraph()
        n1 = graph.add_node("A", NodeType.ENTITY, confidence=0.9)
        n2 = graph.add_node("B", NodeType.ENTITY, confidence=0.5)

        graph.add_relationship(n1, n2, RelationshipType.CAUSALITY, strength=0.8)

        bp = BelievePropagation(graph, damping_factor=0.9)
        beliefs = bp.propagate_beliefs(iterations=2)

        assert n2 in beliefs


class TestGraphQuery:
    """Test GraphQuery data structure."""

    def test_query_creation(self):
        """Test creating a query."""
        query = GraphQuery(
            query_type="path",
            source_id="n1",
            target_id="n2",
            max_hops=3,
        )
        assert query.query_type == "path"
        assert query.max_hops == 3

    def test_query_serialization(self):
        """Test query serialization."""
        query = GraphQuery(
            query_type="semantic",
            source_id="n1",
            confidence_threshold=0.7,
        )
        query_dict = query.to_dict()
        assert query_dict["query_type"] == "semantic"
        assert query_dict["confidence_threshold"] == 0.7


class TestQueryResult:
    """Test QueryResult data structure."""

    def test_result_creation(self):
        """Test creating a result."""
        result = QueryResult(
            paths=[["n1", "n2", "n3"]],
            confidence=0.95,
            execution_time_ms=100.0,
        )
        assert len(result.paths) == 1
        assert result.confidence == 0.95


# Integration Tests

class TestGraphIntegration:
    """Integration tests for graph engine."""

    def test_complex_graph_reasoning(self):
        """Test complex multi-hop reasoning scenario."""
        graph = KnowledgeGraph()

        # Build a knowledge graph
        person = graph.add_node("Alice", NodeType.ENTITY)
        place = graph.add_node("Boston", NodeType.ENTITY)
        action = graph.add_node("Teaching", NodeType.EVENT)
        skill = graph.add_node("Python", NodeType.CONCEPT)

        graph.add_relationship(person, place, RelationshipType.SPATIAL)
        graph.add_relationship(person, action, RelationshipType.TEMPORAL)
        graph.add_relationship(action, skill, RelationshipType.ATTRIBUTE)

        # Test multi-hop reasoning
        result = graph.multi_hop_reasoning("Alice teaching Python", max_hops=3)
        assert "conclusions" in result
        assert result["hops_performed"] >= 0

    def test_graph_with_belief_propagation(self):
        """Test graph with belief propagation."""
        graph = KnowledgeGraph()

        n1 = graph.add_node("Source", NodeType.ENTITY, confidence=0.95)
        n2 = graph.add_node("Intermediate", NodeType.ENTITY, confidence=0.5)
        n3 = graph.add_node("Target", NodeType.ENTITY, confidence=0.2)

        graph.add_relationship(n1, n2, RelationshipType.CAUSALITY, strength=0.9, confidence=0.8)
        graph.add_relationship(n2, n3, RelationshipType.CAUSALITY, strength=0.7, confidence=0.6)

        bp = BelievePropagation(graph)
        beliefs = bp.propagate_beliefs(iterations=10)

        assert beliefs[n1] > beliefs[n3]

    def test_query_caching(self):
        """Test query result caching."""
        graph = KnowledgeGraph()
        n1 = graph.add_node("A", NodeType.ENTITY)
        n2 = graph.add_node("B", NodeType.ENTITY)
        graph.add_relationship(n1, n2, RelationshipType.CAUSALITY)

        query = GraphQuery(query_type="path", source_id=n1, target_id=n2)

        result1 = graph.query(query)
        result2 = graph.query(query)

        assert result1.paths == result2.paths
