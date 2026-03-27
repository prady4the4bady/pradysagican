#!/usr/bin/env python3
"""
PHASE 7B: MULTI-MODAL KNOWLEDGE FUSION
Combining knowledge from multiple modalities (text, numeric, categorical)
"""

import asyncio
import random
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class Modality(Enum):
    """Types of data modalities"""
    TEXT = "text"
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    GRAPH = "graph"


@dataclass
class Embedding:
    """Multi-modal embedding"""
    modality: Modality
    vector: List[float]
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class FusedKnowledge:
    """Knowledge fused from multiple modalities"""
    concept: str
    embeddings: List[Embedding]
    fused_vector: List[float]
    trust_score: float
    source_modalities: List[Modality]


class ModalityEmbedder:
    """Embed different modalities into common vector space"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.text_projection = [random.random() for _ in range(embedding_dim)]
        self.numeric_projection = [random.random() for _ in range(embedding_dim)]
        self.categorical_projection = [random.random() for _ in range(embedding_dim)]
    
    async def embed_text(self, text: str) -> Embedding:
        """Embed text into vector space"""
        # Simple: word frequency based
        words = text.lower().split()
        vector = [0.0] * self.embedding_dim
        
        for i, word in enumerate(words[:self.embedding_dim]):
            hash_val = sum(ord(c) for c in word) % self.embedding_dim
            vector[hash_val] += 1.0 / (i + 1)
        
        # Normalize
        norm = math.sqrt(sum(v**2 for v in vector)) or 1.0
        vector = [v / norm for v in vector]
        
        return Embedding(
            modality=Modality.TEXT,
            vector=vector,
            confidence=0.8
        )
    
    async def embed_numeric(self, values: List[float]) -> Embedding:
        """Embed numeric values into vector space"""
        vector = [0.0] * self.embedding_dim
        
        for i, val in enumerate(values[:self.embedding_dim]):
            vector[i] = val
        
        # Normalize
        norm = math.sqrt(sum(v**2 for v in vector)) or 1.0
        vector = [v / norm for v in vector]
        
        return Embedding(
            modality=Modality.NUMERIC,
            vector=vector,
            confidence=0.95
        )
    
    async def embed_categorical(self, categories: List[str]) -> Embedding:
        """Embed categorical values into vector space"""
        vector = [0.0] * self.embedding_dim
        
        for i, cat in enumerate(categories):
            hash_val = sum(ord(c) for c in cat) % self.embedding_dim
            vector[hash_val] += 1.0 / (i + 1)
        
        # Normalize
        norm = math.sqrt(sum(v**2 for v in vector)) or 1.0
        vector = [v / norm for v in vector]
        
        return Embedding(
            modality=Modality.CATEGORICAL,
            vector=vector,
            confidence=0.85
        )


class ModalityFuser:
    """Fuse multiple modality embeddings"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
    
    async def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between vectors"""
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a**2 for a in vec_a)) or 1.0
        norm_b = math.sqrt(sum(b**2 for b in vec_b)) or 1.0
        
        return dot_product / (norm_a * norm_b)
    
    async def fuse_embeddings(self, embeddings: List[Embedding]) -> Tuple[List[float], float]:
        """
        Fuse embeddings using weighted average
        Weight by confidence scores
        """
        
        if not embeddings:
            return [0.0] * self.embedding_dim, 0.0
        
        # Weight by confidence
        total_weight = sum(e.confidence for e in embeddings)
        fused = [0.0] * self.embedding_dim
        
        for embedding in embeddings:
            weight = embedding.confidence / total_weight
            for i in range(self.embedding_dim):
                fused[i] += weight * embedding.vector[i]
        
        # Compute consensus score (how well embeddings agree)
        # Average pairwise similarity
        if len(embeddings) > 1:
            similarities = []
            for i, emb_a in enumerate(embeddings):
                for emb_b in embeddings[i+1:]:
                    sim = await self.cosine_similarity(emb_a.vector, emb_b.vector)
                    similarities.append(sim)
            
            consensus = sum(similarities) / len(similarities)
        else:
            consensus = 1.0
        
        return fused, consensus
    
    async def resolve_conflicts(self, embeddings_dict: Dict[str, List[Embedding]]) -> Dict[str, FusedKnowledge]:
        """
        Resolve conflicts when embeddings disagree
        Return fused knowledge with confidence scores
        """
        
        fused_knowledge = {}
        
        for concept, embeddings in embeddings_dict.items():
            # Check for conflicts (embeddings that disagree)
            conflicts = []
            for i, emb_a in enumerate(embeddings):
                for emb_b in embeddings[i+1:]:
                    if emb_a.modality != emb_b.modality:
                        similarity = await self.cosine_similarity(emb_a.vector, emb_b.vector)
                        if similarity < 0.5:  # Disagreement threshold
                            conflicts.append((emb_a.modality, emb_b.modality, similarity))
            
            # Fuse embeddings despite conflicts
            fused_vector, consensus = await self.fuse_embeddings(embeddings)
            
            # Trust score reflects consensus
            # Higher if no conflicts, lower if conflicts
            base_trust = 1.0
            conflict_penalty = len(conflicts) * 0.1
            trust = max(0.0, base_trust - conflict_penalty) * consensus
            
            # Record source modalities
            modalities = list(set(e.modality for e in embeddings))
            
            fused_knowledge[concept] = FusedKnowledge(
                concept=concept,
                embeddings=embeddings,
                fused_vector=fused_vector,
                trust_score=trust,
                source_modalities=modalities
            )
        
        return fused_knowledge
    
    async def cross_modal_transfer(self, 
                                  source_embedding: Embedding,
                                  target_modality: Modality) -> Embedding:
        """Transfer knowledge from one modality to another"""
        
        # Create target embedding by projecting source
        target_vector = source_embedding.vector.copy()
        
        # Add modality-specific transformation
        if target_modality == Modality.NUMERIC:
            # Normalize to [0, 1]
            target_vector = [(v + 1) / 2 for v in target_vector]
        
        elif target_modality == Modality.CATEGORICAL:
            # Quantize to top-k
            top_k = 5
            sorted_indices = sorted(range(len(target_vector)), 
                                  key=lambda i: target_vector[i], 
                                  reverse=True)[:top_k]
            new_vector = [0.0] * len(target_vector)
            for idx in sorted_indices:
                new_vector[idx] = 1.0 / top_k
            target_vector = new_vector
        
        # Confidence reduced for transferred knowledge
        return Embedding(
            modality=target_modality,
            vector=target_vector,
            confidence=source_embedding.confidence * 0.7,
            metadata={'transferred_from': source_embedding.modality.value}
        )


class MultiModalKnowledgeBase:
    """Knowledge base with multi-modal fusion"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.embedder = ModalityEmbedder(embedding_dim)
        self.fuser = ModalityFuser(embedding_dim)
        self.fused_concepts: Dict[str, FusedKnowledge] = {}
        self.fusion_history: List[Dict] = []
    
    async def add_multimodal_knowledge(self, concept: str, 
                                      text: Optional[str] = None,
                                      numeric: Optional[List[float]] = None,
                                      categorical: Optional[List[str]] = None) -> None:
        """Add knowledge about concept from multiple modalities"""
        
        embeddings = []
        
        if text:
            embedding = await self.embedder.embed_text(text)
            embeddings.append(embedding)
        
        if numeric is not None:
            embedding = await self.embedder.embed_numeric(numeric)
            embeddings.append(embedding)
        
        if categorical:
            embedding = await self.embedder.embed_categorical(categorical)
            embeddings.append(embedding)
        
        # Fuse
        embeddings_dict = {concept: embeddings}
        fused = await self.fuser.resolve_conflicts(embeddings_dict)
        
        self.fused_concepts.update(fused)
        
        self.fusion_history.append({
            'concept': concept,
            'num_modalities': len(embeddings),
            'trust_score': fused[concept].trust_score
        })
    
    async def query_concept(self, concept: str) -> Optional[FusedKnowledge]:
        """Retrieve fused knowledge about concept"""
        return self.fused_concepts.get(concept)
    
    async def find_similar_concepts(self, concept: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Find concepts similar to query"""
        
        if concept not in self.fused_concepts:
            return []
        
        query_vector = self.fused_concepts[concept].fused_vector
        
        similarities = []
        for other_concept, fused_knowledge in self.fused_concepts.items():
            if other_concept != concept:
                similarity = await self.fuser.cosine_similarity(
                    query_vector, fused_knowledge.fused_vector
                )
                similarities.append((other_concept, similarity))
        
        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    async def get_statistics(self) -> Dict:
        """Get knowledge base statistics"""
        
        total_concepts = len(self.fused_concepts)
        total_modalities = 0
        avg_trust = 0.0
        modality_dist = {}
        
        for fused_knowledge in self.fused_concepts.values():
            total_modalities += len(fused_knowledge.source_modalities)
            avg_trust += fused_knowledge.trust_score
            
            for mod in fused_knowledge.source_modalities:
                modality_dist[mod.value] = modality_dist.get(mod.value, 0) + 1
        
        if total_concepts > 0:
            avg_trust /= total_concepts
        
        return {
            'total_concepts': total_concepts,
            'avg_modalities_per_concept': total_modalities / total_concepts if total_concepts > 0 else 0,
            'avg_trust_score': avg_trust,
            'modality_distribution': modality_dist,
            'total_fusions': len(self.fusion_history)
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_multimodal_fusion():
    """Demonstrate multi-modal knowledge fusion"""
    
    print("\n" + "=" * 70)
    print("MULTI-MODAL KNOWLEDGE FUSION (PHASE 7B)")
    print("=" * 70)
    
    # Initialize KB
    print("\n[Setup] Initializing multi-modal knowledge base...")
    kb = MultiModalKnowledgeBase(embedding_dim=64)
    
    # Add concepts with multiple modalities
    print("\n[Learning] Adding multi-modal concepts...")
    
    await kb.add_multimodal_knowledge(
        "machine_learning",
        text="Machine learning is a branch of AI that learns from data",
        numeric=[0.8, 0.7, 0.9, 0.6],
        categorical=["AI", "data", "algorithms"]
    )
    
    await kb.add_multimodal_knowledge(
        "deep_learning",
        text="Deep learning uses neural networks with multiple layers",
        numeric=[0.9, 0.85, 0.95, 0.8],
        categorical=["neural", "networks", "layers"]
    )
    
    await kb.add_multimodal_knowledge(
        "natural_language",
        text="NLP processes and understands human language",
        numeric=[0.75, 0.8, 0.85, 0.7],
        categorical=["language", "text", "understanding"]
    )
    
    # Query concepts
    print("\n[Query] Retrieving fused knowledge...")
    concept = await kb.query_concept("machine_learning")
    if concept:
        print(f"  Concept: {concept.concept}")
        print(f"  Trust score: {concept.trust_score:.3f}")
        print(f"  Source modalities: {[m.value for m in concept.source_modalities]}")
    
    # Find similar concepts
    print("\n[Search] Finding similar concepts...")
    similar = await kb.find_similar_concepts("machine_learning", top_k=3)
    for similar_concept, similarity in similar:
        print(f"  {similar_concept}: {similarity:.3f}")
    
    # Transfer knowledge
    print("\n[Transfer] Cross-modal knowledge transfer...")
    ml_concept = await kb.query_concept("machine_learning")
    if ml_concept and ml_concept.embeddings:
        source_emb = ml_concept.embeddings[0]  # Text modality
        
        transferred = await kb.fuser.cross_modal_transfer(
            source_emb, Modality.NUMERIC
        )
        print(f"  Transferred from {source_emb.modality.value} to {transferred.modality.value}")
        print(f"  Confidence: {source_emb.confidence:.3f} → {transferred.confidence:.3f}")
    
    # Statistics
    print("\n[Statistics]:")
    stats = await kb.get_statistics()
    print(f"  Total concepts: {stats['total_concepts']}")
    print(f"  Avg modalities per concept: {stats['avg_modalities_per_concept']:.2f}")
    print(f"  Avg trust score: {stats['avg_trust_score']:.3f}")
    print(f"  Modality distribution: {stats['modality_distribution']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_multimodal_fusion())
