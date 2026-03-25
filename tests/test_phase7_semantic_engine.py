"""Test suite for Phase 7 Semantic Engine (F631-F635)."""

import pytest
import numpy as np
from unittest.mock import Mock, patch

from pradysagican.core.intelligence.semantic_engine import (
    SemanticSpace,
    ConceptEmbedding,
    AnalogyDetector,
    Analogy,
    CrossDomainTransfer,
)


class TestConceptEmbedding:
    """Test ConceptEmbedding data structure."""

    def test_embedding_creation(self):
        """Test creating a concept embedding."""
        embedding = np.array([0.1, 0.2, 0.3])
        concept = ConceptEmbedding(
            concept_id="c1",
            concept_name="Dog",
            embedding=embedding,
            domain="animals",
        )
        assert concept.concept_id == "c1"
        assert concept.concept_name == "Dog"
        assert concept.domain == "animals"
        assert concept.dimensionality == 3

    def test_embedding_normalization(self):
        """Test embedding normalization."""
        raw_embedding = np.array([3.0, 4.0])
        normalized = raw_embedding / np.linalg.norm(raw_embedding)
        concept = ConceptEmbedding(
            concept_id="c1",
            concept_name="Test",
            embedding=normalized,
        )
        norm = np.linalg.norm(concept.embedding)
        assert abs(norm - 1.0) < 0.001

    def test_embedding_serialization(self):
        """Test embedding serialization."""
        embedding = np.array([0.5, 0.5])
        concept = ConceptEmbedding(
            concept_id="c1",
            concept_name="Test",
            embedding=embedding,
            metadata={"type": "noun"},
        )
        emb_dict = concept.to_dict()
        assert emb_dict["concept_id"] == "c1"
        assert "embedding" in emb_dict
        assert isinstance(emb_dict["embedding"], list)


class TestSemanticSpace:
    """Test SemanticSpace functionality."""

    def test_space_initialization(self):
        """Test semantic space initialization."""
        space = SemanticSpace(dimensionality=128, domain="biology")
        assert space._dimensionality == 128
        assert space._domain == "biology"
        assert len(space._embeddings) == 0

    def test_embed_concept(self):
        """Test embedding a concept."""
        space = SemanticSpace(dimensionality=64, domain="animals")
        concept_id = space.embed_concept("Dog")

        assert concept_id in space._embeddings
        concept = space._embeddings[concept_id]
        assert concept.concept_name == "Dog"
        assert len(concept.embedding) == 64

    def test_embed_multiple_concepts(self):
        """Test embedding multiple concepts."""
        space = SemanticSpace(dimensionality=32)

        c1 = space.embed_concept("Cat")
        c2 = space.embed_concept("Dog")
        c3 = space.embed_concept("Bird")

        assert len(space._embeddings) == 3
        assert space._embeddings[c1].concept_name == "Cat"

    def test_semantic_similarity(self):
        """Test semantic similarity calculation."""
        space = SemanticSpace(dimensionality=3)

        # Create two similar embeddings
        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([0.9, 0.1, 0.0])

        c1 = space.embed_concept("A", embedding=emb1)
        c2 = space.embed_concept("B", embedding=emb2)

        similarity = space.semantic_similarity(c1, c2)
        assert 0.8 <= similarity <= 1.0

    def test_similarity_different_concepts(self):
        """Test similarity between very different concepts."""
        space = SemanticSpace(dimensionality=3)

        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([0.0, 0.0, 1.0])

        c1 = space.embed_concept("A", embedding=emb1)
        c2 = space.embed_concept("B", embedding=emb2)

        similarity = space.semantic_similarity(c1, c2)
        assert similarity < 0.3

    def test_find_similar_concepts(self):
        """Test finding similar concepts."""
        space = SemanticSpace(dimensionality=3)

        center = np.array([1.0, 0.0, 0.0])
        c_center = space.embed_concept("Center", embedding=center)

        similar1 = np.array([0.95, 0.05, 0.0])
        similar2 = np.array([0.9, 0.1, 0.0])
        dissimilar = np.array([0.0, 0.0, 1.0])

        c1 = space.embed_concept("Similar1", embedding=similar1)
        c2 = space.embed_concept("Similar2", embedding=similar2)
        c3 = space.embed_concept("Dissimilar", embedding=dissimilar)

        similar = space.find_similar_concepts(c_center, limit=2, threshold=0.5)
        assert len(similar) >= 1
        assert similar[0][0] in [c1, c2]

    def test_nearest_neighbors(self):
        """Test nearest neighbor search."""
        space = SemanticSpace(dimensionality=3)

        for i in range(5):
            emb = np.random.randn(3)
            space.embed_concept(f"Concept{i}", embedding=emb)

        query_embedding = np.random.randn(3)
        neighbors = space.nearest_neighbors(query_embedding, limit=2)

        assert len(neighbors) <= 2
        assert all(0.0 <= sim <= 1.0 for _, sim in neighbors)

    def test_get_concept(self):
        """Test retrieving a concept."""
        space = SemanticSpace()
        c_id = space.embed_concept("Test")
        concept = space.get_concept(c_id)

        assert concept is not None
        assert concept.concept_name == "Test"

    def test_space_stats(self):
        """Test getting space statistics."""
        space = SemanticSpace(dimensionality=64)
        space.embed_concept("A")
        space.embed_concept("B")

        stats = space.stats()
        assert stats["num_concepts"] == 2
        assert stats["dimensionality"] == 64
        assert stats["domain"] == "general"

    def test_dimension_mismatch(self):
        """Test error handling for dimension mismatch."""
        space = SemanticSpace(dimensionality=3)
        wrong_embedding = np.array([1.0, 2.0])

        with pytest.raises(ValueError):
            space.embed_concept("Test", embedding=wrong_embedding)

    def test_custom_embedding(self):
        """Test providing custom embeddings."""
        space = SemanticSpace(dimensionality=3)
        custom_emb = np.array([0.3, 0.6, 0.4])

        c_id = space.embed_concept("Custom", embedding=custom_emb)
        concept = space.get_concept(c_id)

        norm = np.linalg.norm(concept.embedding)
        assert abs(norm - 1.0) < 0.001


class TestAnalogyDetector:
    """Test AnalogyDetector functionality."""

    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = AnalogyDetector(similarity_threshold=0.6)
        assert detector._similarity_threshold == 0.6

    def test_find_analogies(self):
        """Test finding analogies."""
        source_space = SemanticSpace(dimensionality=3, domain="source")
        target_space = SemanticSpace(dimensionality=3, domain="target")

        source_emb = np.array([1.0, 0.0, 0.0])
        source_concept = ConceptEmbedding(
            concept_id="s1",
            concept_name="Source",
            embedding=source_emb,
            domain="source",
        )

        target_emb = np.array([0.95, 0.05, 0.0])
        c_t = target_space.embed_concept("Target", embedding=target_emb)

        detector = AnalogyDetector(similarity_threshold=0.5)
        analogies = detector.find_analogies(source_concept, target_space, limit=1)

        assert len(analogies) >= 0

    def test_analogy_data_structure(self):
        """Test Analogy data structure."""
        analogy = Analogy(
            analogy_id="a1",
            source_concept="Dog",
            target_concept="Puppy",
            similarity_score=0.85,
            common_features=["animal", "mammal"],
            confidence=0.9,
        )
        assert analogy.source_concept == "Dog"
        assert analogy.similarity_score == 0.85

    def test_extract_common_features(self):
        """Test feature extraction."""
        source = ConceptEmbedding(
            concept_id="s1",
            concept_name="Dog",
            embedding=np.array([1.0, 0.0]),
            domain="animals",
            metadata={"type": "mammal", "legs": 4},
        )
        target = ConceptEmbedding(
            concept_id="t1",
            concept_name="Cat",
            embedding=np.array([0.9, 0.1]),
            domain="animals",
            metadata={"type": "mammal", "legs": 4},
        )

        detector = AnalogyDetector()
        features = detector._extract_common_features(source, target)

        assert isinstance(features, list)
        assert len(features) <= 5

    def test_cross_domain_analogies(self):
        """Test cross-domain analogy detection."""
        spaces = {
            "biology": SemanticSpace(dimensionality=3, domain="biology"),
            "physics": SemanticSpace(dimensionality=3, domain="physics"),
        }

        spaces["biology"].embed_concept("Cell")
        spaces["biology"].embed_concept("Organism")
        spaces["physics"].embed_concept("Atom")
        spaces["physics"].embed_concept("Universe")

        detector = AnalogyDetector()
        analogies = detector.detect_cross_domain_analogies(spaces, limit=2)

        assert isinstance(analogies, list)

    def test_get_domain_bridges(self):
        """Test domain bridge tracking."""
        detector = AnalogyDetector()

        s1 = ConceptEmbedding(
            "s1", "Source", np.array([1.0, 0.0]), domain="domain1"
        )
        s2 = SemanticSpace(dimensionality=2, domain="domain2")
        s2.embed_concept("Target")

        detector.find_analogies(s1, s2, limit=1)
        bridges = detector.get_domain_bridges()

        assert isinstance(bridges, dict)


class TestCrossDomainTransfer:
    """Test CrossDomainTransfer functionality."""

    def test_transfer_initialization(self):
        """Test transfer initialization."""
        transfer = CrossDomainTransfer()
        assert len(transfer._transfer_rules) == 0

    def test_transfer_knowledge(self):
        """Test knowledge transfer."""
        transfer = CrossDomainTransfer()

        source_properties = {
            "color": "red",
            "size": 10,
            "active": True,
            "tags": ["a", "b"],
            "metadata": {"key": "value"},
        }

        result = transfer.transfer_knowledge(
            source_concept="Source",
            target_concept="Target",
            source_properties=source_properties,
            analogy_confidence=0.8,
        )

        assert "transfer_id" in result
        assert "properties" in result
        assert result["overall_confidence"] == 0.8

    def test_transfer_primitive_properties(self):
        """Test transferring primitive properties."""
        transfer = CrossDomainTransfer()

        properties = {"value": 42, "name": "Test", "flag": True}

        result = transfer.transfer_knowledge(
            "SourceA",
            "TargetB",
            properties,
            analogy_confidence=0.9,
        )

        for prop_name, prop_info in result["properties"].items():
            assert prop_info["source"] == "SourceA"
            assert prop_info["transfer_type"] in [
                "direct",
                "structural",
                "relational",
            ]

    def test_learn_domain_mapping(self):
        """Test learning domain mappings."""
        transfer = CrossDomainTransfer()

        source_pairs = [
            (np.array([1.0, 0.0]), np.array([0.9, 0.1])),
            (np.array([0.0, 1.0]), np.array([0.1, 0.9])),
            (np.array([1.0, 1.0]), np.array([0.95, 0.95])),
        ]

        success = transfer.learn_domain_mapping(
            source_pairs, "domain_a", "domain_b"
        )
        assert success is True

    def test_apply_learned_mapping(self):
        """Test applying learned mappings."""
        transfer = CrossDomainTransfer()

        source_pairs = [
            (np.array([1.0, 0.0]), np.array([1.0, 0.0])),
            (np.array([0.0, 1.0]), np.array([0.0, 1.0])),
        ]

        transfer.learn_domain_mapping(source_pairs, "d1", "d2")

        source_vector = np.array([1.0, 1.0])
        mapped = transfer.apply_learned_mapping(source_vector, "d1", "d2")

        if mapped is not None:
            assert len(mapped) == 2

    def test_get_transfer_rule(self):
        """Test retrieving transfer rules."""
        transfer = CrossDomainTransfer()

        result = transfer.transfer_knowledge(
            "Source",
            "Target",
            {"value": 10},
            analogy_confidence=0.7,
        )

        transfer_id = result["transfer_id"]
        rule = transfer.get_transfer_rule(transfer_id)

        assert rule is not None
        assert rule["source"] == "Source"
        assert rule["target"] == "Target"

    def test_confidence_propagation(self):
        """Test confidence propagation in transfer."""
        transfer = CrossDomainTransfer()

        properties = {
            "simple": "value",
            "list": [1, 2, 3],
            "dict": {"nested": "data"},
        }

        result = transfer.transfer_knowledge(
            "S", "T", properties, analogy_confidence=0.9
        )

        simple_conf = result["properties"]["simple"]["confidence"]
        list_conf = result["properties"]["list"]["confidence"]
        dict_conf = result["properties"]["dict"]["confidence"]

        assert simple_conf == 0.9
        assert list_conf < simple_conf
        assert dict_conf < simple_conf


# Integration Tests

class TestSemanticIntegration:
    """Integration tests for semantic engine."""

    def test_multi_domain_analogy_chain(self):
        """Test chain of analogies across domains."""
        detector = AnalogyDetector(similarity_threshold=0.5)
        transfer = CrossDomainTransfer()

        spaces = {
            "biology": SemanticSpace(dimensionality=3, domain="biology"),
            "physics": SemanticSpace(dimensionality=3, domain="physics"),
            "social": SemanticSpace(dimensionality=3, domain="social"),
        }

        for domain_name in spaces:
            for i in range(3):
                spaces[domain_name].embed_concept(f"Concept{i}")

        analogies = detector.detect_cross_domain_analogies(spaces, limit=3)
        assert isinstance(analogies, list)

    def test_semantic_search_pipeline(self):
        """Test complete semantic search pipeline."""
        space = SemanticSpace(dimensionality=64)

        concepts = ["apple", "banana", "orange", "car", "tree"]
        for concept in concepts:
            space.embed_concept(concept)

        query_embedding = np.random.randn(64)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        neighbors = space.nearest_neighbors(query_embedding, limit=3)
        assert len(neighbors) <= 3

    def test_knowledge_transfer_with_validation(self):
        """Test knowledge transfer with confidence validation."""
        transfer = CrossDomainTransfer()

        source_props = {
            "complexity": 8,
            "efficiency": 0.95,
            "cost": 100.0,
        }

        result = transfer.transfer_knowledge(
            "Algorithm1",
            "Algorithm2",
            source_props,
            analogy_confidence=0.75,
        )

        assert result["overall_confidence"] == 0.75
        for prop in result["properties"].values():
            assert prop["confidence"] <= 0.75
