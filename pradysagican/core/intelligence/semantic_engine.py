"""
Phase 7 - Semantic Understanding Engine (F631-F635)
=====================================================
Concept embeddings, cross-domain analogy detection, and semantic similarity.

Features:
- Concept embedding and representation
- Semantic space construction
- Cross-domain analogy detection
- Semantic similarity search
- Cross-domain knowledge transfer
"""

from __future__ import annotations

import logging
import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class ConceptEmbedding:
    """Embedded representation of a concept."""
    concept_id: str
    concept_name: str
    embedding: np.ndarray  # Dense vector representation
    domain: str = "general"
    dimensionality: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.dimensionality = len(self.embedding)

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "embedding": self.embedding.tolist(),
            "domain": self.domain,
            "dimensionality": self.dimensionality,
            "metadata": self.metadata,
        }


@dataclass
class Analogy:
    """Represents an analogical relationship between concepts."""
    analogy_id: str
    source_concept: str
    target_concept: str
    similarity_score: float
    common_features: list[str] = field(default_factory=list)
    domain_bridge: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "analogy_id": self.analogy_id,
            "source": self.source_concept,
            "target": self.target_concept,
            "similarity": self.similarity_score,
            "features": self.common_features,
            "domain_bridge": self.domain_bridge,
            "confidence": self.confidence,
        }


# ── Semantic Space ────────────────────────────────────────────────────────────

class SemanticSpace:
    """
    Multi-dimensional semantic space for concept embeddings.
    Supports similarity search and analogy detection.
    """

    def __init__(self, dimensionality: int = 128, domain: str = "general") -> None:
        self._embeddings: dict[str, ConceptEmbedding] = {}
        self._dimensionality = dimensionality
        self._domain = domain
        self._concept_index: list[str] = []
        self._embedding_matrix: Optional[np.ndarray] = None
        logger.info(f"Initialized SemanticSpace (dim={dimensionality}, domain={domain})")

    def embed_concept(
        self,
        concept_name: str,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[dict[str, Any]] = None,
        concept_id: Optional[str] = None,
    ) -> str:
        """Add a concept embedding to the semantic space."""
        concept_id = concept_id or str(uuid.uuid4())[:8]

        if concept_id in self._embeddings:
            logger.warning(f"Concept {concept_id} already exists")
            return concept_id

        if embedding is None:
            embedding = np.random.randn(self._dimensionality)
            embedding = embedding / np.linalg.norm(embedding)
        else:
            embedding = embedding / np.linalg.norm(embedding)

        if len(embedding) != self._dimensionality:
            raise ValueError(
                f"Embedding dimension {len(embedding)} != {self._dimensionality}"
            )

        concept = ConceptEmbedding(
            concept_id=concept_id,
            concept_name=concept_name,
            embedding=embedding,
            domain=self._domain,
            metadata=metadata or {},
        )

        self._embeddings[concept_id] = concept
        self._concept_index.append(concept_id)
        self._embedding_matrix = None

        logger.debug(f"Embedded concept {concept_id}: {concept_name}")
        return concept_id

    def semantic_similarity(self, concept_id1: str, concept_id2: str) -> float:
        """Calculate cosine similarity between two concepts."""
        emb1 = self._embeddings.get(concept_id1)
        emb2 = self._embeddings.get(concept_id2)

        if not emb1 or not emb2:
            return 0.0

        dot_product = np.dot(emb1.embedding, emb2.embedding)
        norm1 = np.linalg.norm(emb1.embedding)
        norm2 = np.linalg.norm(emb2.embedding)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def find_similar_concepts(
        self, concept_id: str, limit: int = 5, threshold: float = 0.3
    ) -> list[tuple[str, float]]:
        """Find concepts similar to a given concept."""
        if concept_id not in self._embeddings:
            logger.warning(f"Concept {concept_id} not found")
            return []

        similarities = []
        for other_id in self._embeddings:
            if other_id == concept_id:
                continue

            sim = self.semantic_similarity(concept_id, other_id)
            if sim >= threshold:
                similarities.append((other_id, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def nearest_neighbors(
        self, embedding: np.ndarray, limit: int = 5
    ) -> list[tuple[str, float]]:
        """Find nearest neighbors to an arbitrary embedding."""
        if not self._embeddings:
            return []

        embedding = embedding / np.linalg.norm(embedding)
        similarities = []

        for concept in self._embeddings.values():
            # Normalize the concept embedding
            concept_norm = concept.embedding / np.linalg.norm(concept.embedding)
            # Compute cosine similarity and map from [-1, 1] to [0, 1]
            cosine_sim = float(np.dot(embedding, concept_norm))
            normalized_sim = (cosine_sim + 1.0) / 2.0  # Map [-1, 1] to [0, 1]
            similarities.append((concept.concept_id, normalized_sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

    def get_concept(self, concept_id: str) -> Optional[ConceptEmbedding]:
        """Retrieve a concept embedding."""
        return self._embeddings.get(concept_id)

    def stats(self) -> dict[str, Any]:
        """Get statistics about the semantic space."""
        return {
            "num_concepts": len(self._embeddings),
            "dimensionality": self._dimensionality,
            "domain": self._domain,
            "embedding_size_mb": len(self._embeddings) * self._dimensionality * 8 / (1024**2),
        }


# ── Analogy Detection ──────────────────────────────────────────────────────────

class AnalogyDetector:
    """
    Detects and analyzes analogical relationships between concepts.
    Supports both within-domain and cross-domain analogy detection.
    """

    def __init__(self, similarity_threshold: float = 0.6) -> None:
        self._similarity_threshold = similarity_threshold
        self._detected_analogies: dict[str, Analogy] = {}
        self._domain_bridges: dict[tuple[str, str], list[str]] = {}
        logger.info(f"Initialized AnalogyDetector (threshold={similarity_threshold})")

    def find_analogies(
        self,
        source_concept: ConceptEmbedding,
        target_space: SemanticSpace,
        limit: int = 5,
    ) -> list[Analogy]:
        """
        Find analogical relationships between a concept and a semantic space.
        """
        logger.info(f"Finding analogies for {source_concept.concept_name}")

        analogies = []
        target_embedding = source_concept.embedding

        similar_targets = target_space.nearest_neighbors(target_embedding, limit=limit * 2)

        for target_id, similarity in similar_targets:
            target_concept = target_space.get_concept(target_id)
            if not target_concept:
                continue

            if similarity < self._similarity_threshold:
                continue

            analogy_id = str(uuid.uuid4())[:8]
            common_features = self._extract_common_features(
                source_concept, target_concept
            )

            domain_bridge = None
            if source_concept.domain != target_concept.domain:
                domain_bridge = f"{source_concept.domain}<->{target_concept.domain}"
                key = (source_concept.domain, target_concept.domain)
                if key not in self._domain_bridges:
                    self._domain_bridges[key] = []
                self._domain_bridges[key].append(source_concept.concept_name)

            analogy = Analogy(
                analogy_id=analogy_id,
                source_concept=source_concept.concept_name,
                target_concept=target_concept.concept_name,
                similarity_score=similarity,
                common_features=common_features,
                domain_bridge=domain_bridge,
                confidence=min(1.0, similarity * len(common_features) / 3),
            )

            analogies.append(analogy)
            self._detected_analogies[analogy_id] = analogy

        logger.info(f"Found {len(analogies)} analogies")
        return analogies[:limit]

    def _extract_common_features(
        self, concept1: ConceptEmbedding, concept2: ConceptEmbedding
    ) -> list[str]:
        """Extract common features between two concepts."""
        features = []

        common_metadata_keys = set(concept1.metadata.keys()) & set(concept2.metadata.keys())
        for key in common_metadata_keys:
            if concept1.metadata[key] == concept2.metadata[key]:
                features.append(f"{key}:{concept1.metadata[key]}")

        if concept1.domain == concept2.domain:
            features.append(f"domain:{concept1.domain}")

        return features[:5]

    def detect_cross_domain_analogies(
        self, spaces: dict[str, SemanticSpace], limit: int = 5
    ) -> list[Analogy]:
        """
        Detect analogies across multiple semantic spaces (domains).
        """
        logger.info(f"Detecting cross-domain analogies across {len(spaces)} spaces")

        cross_domain_analogies = []
        domain_names = list(spaces.keys())

        for i, source_domain in enumerate(domain_names):
            for target_domain in domain_names[i + 1 :]:
                source_space = spaces[source_domain]
                target_space = spaces[target_domain]

                for source_id in list(source_space._embeddings.keys())[:limit]:
                    source_concept = source_space.get_concept(source_id)
                    if not source_concept:
                        continue

                    analogies = self.find_analogies(source_concept, target_space, limit=2)
                    cross_domain_analogies.extend(analogies)

        logger.info(f"Found {len(cross_domain_analogies)} cross-domain analogies")
        return cross_domain_analogies

    def get_analogy(self, analogy_id: str) -> Optional[Analogy]:
        """Retrieve an analogy by ID."""
        return self._detected_analogies.get(analogy_id)

    def get_domain_bridges(self) -> dict[tuple[str, str], list[str]]:
        """Get all domain bridges (connections between domains)."""
        return self._domain_bridges


# ── Knowledge Transfer ────────────────────────────────────────────────────────

class CrossDomainTransfer:
    """
    Transfers knowledge from one domain to another using analogies.
    Supports analogical reasoning and transfer learning.
    """

    def __init__(self) -> None:
        self._transfer_rules: dict[str, dict[str, Any]] = {}
        self._learned_mappings: dict[str, list[tuple[str, str]]] = {}
        logger.info("Initialized CrossDomainTransfer")

    def transfer_knowledge(
        self,
        source_concept: str,
        target_concept: str,
        source_properties: dict[str, Any],
        analogy_confidence: float = 0.8,
    ) -> dict[str, Any]:
        """
        Transfer knowledge from source to target based on analogy.
        """
        logger.info(f"Transferring knowledge: {source_concept} -> {target_concept}")

        transferred_properties = {}

        for prop_name, prop_value in source_properties.items():
            if isinstance(prop_value, (int, float, str, bool)):
                transferred_properties[prop_name] = {
                    "value": prop_value,
                    "source": source_concept,
                    "confidence": analogy_confidence,
                    "transfer_type": "direct",
                }
            elif isinstance(prop_value, list):
                transferred_properties[prop_name] = {
                    "value": prop_value,
                    "source": source_concept,
                    "confidence": analogy_confidence * 0.8,
                    "transfer_type": "structural",
                }
            elif isinstance(prop_value, dict):
                transferred_properties[prop_name] = {
                    "value": prop_value,
                    "source": source_concept,
                    "confidence": analogy_confidence * 0.6,
                    "transfer_type": "relational",
                }

        transfer_id = f"{source_concept}_to_{target_concept}"
        self._transfer_rules[transfer_id] = {
            "source": source_concept,
            "target": target_concept,
            "properties": transferred_properties,
            "confidence": analogy_confidence,
        }

        logger.info(f"Knowledge transfer completed: {len(transferred_properties)} properties")
        return {
            "transfer_id": transfer_id,
            "properties": transferred_properties,
            "overall_confidence": analogy_confidence,
        }

    def get_transfer_rule(self, transfer_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a transfer rule."""
        return self._transfer_rules.get(transfer_id)

    def apply_learned_mapping(
        self, source_vector: np.ndarray, source_domain: str, target_domain: str
    ) -> Optional[np.ndarray]:
        """
        Apply a learned domain mapping to transform a vector.
        """
        mapping_key = f"{source_domain}_to_{target_domain}"

        if mapping_key in self._learned_mappings:
            vector = source_vector.copy()
            for transform_matrix, _ in self._learned_mappings[mapping_key]:
                if transform_matrix.shape == (len(vector), len(vector)):
                    vector = transform_matrix @ vector

            return vector

        return None

    def learn_domain_mapping(
        self,
        source_pairs: list[tuple[np.ndarray, np.ndarray]],
        source_domain: str,
        target_domain: str,
    ) -> bool:
        """
        Learn a mapping between domains from paired examples.
        """
        if not source_pairs:
            return False

        source_vectors = np.array([p[0] for p in source_pairs])
        target_vectors = np.array([p[1] for p in source_pairs])

        try:
            mapping_matrix = np.linalg.lstsq(source_vectors, target_vectors, rcond=None)[0]
            mapping_key = f"{source_domain}_to_{target_domain}"

            if mapping_key not in self._learned_mappings:
                self._learned_mappings[mapping_key] = []

            self._learned_mappings[mapping_key].append((mapping_matrix, len(source_pairs)))
            logger.info(f"Learned mapping {mapping_key} from {len(source_pairs)} pairs")
            return True
        except Exception as e:
            logger.error(f"Failed to learn domain mapping: {e}")
            return False
