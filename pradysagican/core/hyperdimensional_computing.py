#!/usr/bin/env python3
"""
PHASE 23: HYPERDIMENSIONAL COMPUTING
Encoding/manipulation in high-dimensional spaces for reasoning and memory
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional
import random
import math


@dataclass
class HyperVector:
    """A vector in high-dimensional space (10,000+ dimensions)"""
    name: str
    dimensions: int
    vector: List[float]  # In practice, use sparse representation
    semantic_meaning: str


class HyperdimensionalProcessor:
    """Process information in high-dimensional spaces"""
    
    def __init__(self, dim: int = 10000):
        self.dimension: int = dim
        self.concept_vectors: Dict[str, HyperVector] = {}
        self.binding_operations: List[Dict] = []
        self.bundling_operations: List[Dict] = []
        self.semantic_space: Dict[str, float] = {}
    
    async def create_concept_vector(self, concept: str) -> HyperVector:
        """Create a random binary hypervector for a concept"""
        
        # Generate random binary vector
        vector = [random.choice([0.0, 1.0]) for _ in range(self.dimension)]
        
        hv = HyperVector(
            name=concept,
            dimensions=self.dimension,
            vector=vector,
            semantic_meaning=f"Vector representation of '{concept}'"
        )
        
        self.concept_vectors[concept] = hv
        return hv
    
    async def bind_concepts(self, concept_a: str, concept_b: str) -> List[float]:
        """Bind two concepts using XOR operation"""
        
        if concept_a not in self.concept_vectors:
            await self.create_concept_vector(concept_a)
        if concept_b not in self.concept_vectors:
            await self.create_concept_vector(concept_b)
        
        hv_a = self.concept_vectors[concept_a].vector
        hv_b = self.concept_vectors[concept_b].vector
        
        # XOR binding
        bound_vector = [
            1.0 if hv_a[i] != hv_b[i] else 0.0
            for i in range(self.dimension)
        ]
        
        self.binding_operations.append({
            'operation': f"bind({concept_a}, {concept_b})",
            'result_sparsity': sum(bound_vector) / self.dimension,
            'hamming_distance': sum(bound_vector)
        })
        
        return bound_vector
    
    async def bundle_concepts(self, concepts: List[str]) -> List[float]:
        """Bundle multiple concepts using addition"""
        
        # Ensure all concepts are vectorized
        for concept in concepts:
            if concept not in self.concept_vectors:
                await self.create_concept_vector(concept)
        
        # Add all vectors element-wise
        bundled = [0.0] * self.dimension
        for concept in concepts:
            vector = self.concept_vectors[concept].vector
            for i in range(self.dimension):
                bundled[i] += vector[i]
        
        # Normalize
        max_val = max(bundled) if max(bundled) > 0 else 1
        bundled = [v / max_val for v in bundled]
        
        sparsity = sum(1 for v in bundled if v > 0.5) / self.dimension
        
        self.bundling_operations.append({
            'operation': f"bundle({', '.join(concepts)})",
            'result_sparsity': sparsity,
            'num_concepts': len(concepts)
        })
        
        return bundled
    
    async def compute_similarity(self, vector_a: List[float], vector_b: List[float]) -> float:
        """Compute cosine similarity between two vectors"""
        
        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        magnitude_a = math.sqrt(sum(a * a for a in vector_a))
        magnitude_b = math.sqrt(sum(b * b for b in vector_b))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    async def cleanup_memory_recall(self, noisy_vector: List[float], candidates: List[str]) -> str:
        """Recall from memory using cleanup (similarity-based)"""
        
        similarities = {}
        for candidate in candidates:
            if candidate in self.concept_vectors:
                vector = self.concept_vectors[candidate].vector
                sim = await self.compute_similarity(noisy_vector, vector)
                similarities[candidate] = sim
        
        if not similarities:
            return "No candidate found"
        
        best_match = max(similarities.items(), key=lambda x: x[1])
        return best_match[0]


class HyperdimensionalMemorySystem:
    """Memory system using hyperdimensional computing"""
    
    def __init__(self):
        self.processor = HyperdimensionalProcessor(dim=10000)
        self.memory_capacity: Dict = {}
        self.semantic_compression: Dict = {}
        self.reasoning_performance: Dict = {}
    
    async def demonstrate_holistic_binding(self) -> Dict:
        """Demonstrate holistic property binding"""
        
        # Create concept vectors
        print("[Phase 23] Creating concept vectors...")
        await self.processor.create_concept_vector("object")
        await self.processor.create_concept_vector("red")
        await self.processor.create_concept_vector("ball")
        
        # Bind concepts
        print("[Phase 23] Binding concepts...")
        object_red = await self.processor.bind_concepts("object", "red")
        object_ball = await self.processor.bind_concepts("object", "ball")
        
        # Bundle to create compound memory
        print("[Phase 23] Bundling to memory...")
        compound_memory = await self.processor.bundle_concepts(["object", "red", "ball"])
        
        return {
            'concept_count': len(self.processor.concept_vectors),
            'binding_operations': len(self.processor.binding_operations),
            'bundling_operations': len(self.processor.bundling_operations),
            'compound_memory_created': True
        }
    
    async def run_holistic_reasoning(self) -> Dict:
        """Run holistic reasoning in hyperdimensional space"""
        
        # Create working examples
        concepts = ["intelligence", "learning", "reasoning", "knowledge", "wisdom"]
        
        for concept in concepts:
            await self.processor.create_concept_vector(concept)
        
        # Perform binding and bundling
        print("[Phase 23] Holistic reasoning...")
        
        # Bind related pairs
        learning_reasoning = await self.processor.bind_concepts("learning", "reasoning")
        knowledge_wisdom = await self.processor.bind_concepts("knowledge", "wisdom")
        
        # Bundle into composite idea
        composite = await self.processor.bundle_concepts(concepts)
        
        # Compute space statistics
        total_operations = (
            len(self.processor.binding_operations) +
            len(self.processor.bundling_operations)
        )
        
        compression_ratio = 10000 / (total_operations * 100) if total_operations > 0 else 0
        
        self.reasoning_performance = {
            'total_operations': total_operations,
            'binding_ops': len(self.processor.binding_operations),
            'bundling_ops': len(self.processor.bundling_operations),
            'semantic_space_dim': 10000,
            'compression_ratio': compression_ratio,
            'holistic_concepts': len(concepts)
        }
        
        return self.reasoning_performance
    
    async def get_hyperdimensional_status(self) -> Dict:
        """Get complete hyperdimensional system status"""
        
        return {
            'processor_dimension': self.processor.dimension,
            'concept_vectors': len(self.processor.concept_vectors),
            'binding_operations': len(self.processor.binding_operations),
            'bundling_operations': len(self.processor.bundling_operations),
            'semantic_space': self.processor.semantic_space,
            'reasoning_performance': self.reasoning_performance,
            'memory_capacity': len(self.processor.concept_vectors) * 10000  # Total bits
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_hyperdimensional_computing():
    """Demonstrate hyperdimensional computing"""
    
    print("\n" + "=" * 70)
    print("HYPERDIMENSIONAL COMPUTING (PHASE 23)")
    print("=" * 70)
    
    system = HyperdimensionalMemorySystem()
    
    # Demonstrate holistic binding
    print("\n[Holistic Binding] Creating compound memories...")
    binding_result = await system.demonstrate_holistic_binding()
    print(f"  Concepts created: {binding_result['concept_count']}")
    print(f"  Binding operations: {binding_result['binding_operations']}")
    print(f"  Bundling operations: {binding_result['bundling_operations']}")
    
    # Run holistic reasoning
    print("\n[Holistic Reasoning] Running reasoning in hyperdimensional space...")
    reasoning_result = await system.run_holistic_reasoning()
    print(f"  Total operations: {reasoning_result['total_operations']}")
    print(f"  Binding ops: {reasoning_result['binding_ops']}")
    print(f"  Bundling ops: {reasoning_result['bundling_ops']}")
    print(f"  Holistic concepts: {reasoning_result['holistic_concepts']}")
    print(f"  Compression ratio: {reasoning_result['compression_ratio']:.3f}")
    
    # Final status
    print("\n[Hyperdimensional Status]:")
    status = await system.get_hyperdimensional_status()
    print(f"  Processor dimension: {status['processor_dimension']:,}")
    print(f"  Concept vectors: {status['concept_vectors']}")
    print(f"  Memory capacity: {status['memory_capacity']:,} bits")
    print(f"  Total operations: {status['binding_operations'] + status['bundling_operations']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_hyperdimensional_computing())
