#!/usr/bin/env python3
"""
PHASE 7D: CROSS-DOMAIN SYNTHESIS
Analogical reasoning, knowledge recombination, emergent capabilities
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum


class RelationType(Enum):
    """Types of relationships in analogies"""
    STRUCTURAL = "structural"   # X has same structure as Y
    FUNCTIONAL = "functional"   # X does what Y does
    CAUSAL = "causal"          # X causes what Y causes
    COMPOSITIONAL = "compositional"  # X is made of Y


@dataclass
class DomainConcept:
    """Concept within a domain"""
    name: str
    domain: str
    attributes: Dict[str, float]
    relationships: Dict[str, List[str]]


@dataclass
class Analogy:
    """Mapping between domains"""
    source_concept: DomainConcept
    target_concept: DomainConcept
    relation_type: RelationType
    similarity_score: float
    bridging_properties: List[str]


@dataclass
class SynthesizedConcept:
    """Novel concept created by synthesizing domains"""
    name: str
    source_domains: List[str]
    properties: Dict[str, float]
    analogies: List[Analogy]
    novelty_score: float


class AnalogyEngine:
    """Find and apply analogies across domains"""
    
    def __init__(self):
        self.analogies: List[Analogy] = []
        self.concept_cache: Dict[str, DomainConcept] = {}
    
    async def compute_structural_similarity(self, concept_a: DomainConcept, 
                                           concept_b: DomainConcept) -> float:
        """Compute similarity based on attribute structure"""
        
        # Shared attributes
        attrs_a = set(concept_a.attributes.keys())
        attrs_b = set(concept_b.attributes.keys())
        
        shared = len(attrs_a & attrs_b)
        total = len(attrs_a | attrs_b)
        
        if total == 0:
            return 0.0
        
        # Jaccard similarity
        similarity = shared / total
        
        # Check value alignment
        if shared > 0:
            value_diff = 0.0
            for attr in (attrs_a & attrs_b):
                val_a = concept_a.attributes[attr]
                val_b = concept_b.attributes[attr]
                value_diff += abs(val_a - val_b)
            
            value_alignment = 1.0 - (value_diff / shared)
            similarity = 0.6 * similarity + 0.4 * value_alignment
        
        return similarity
    
    async def find_analogies(self, domain_a_concepts: List[DomainConcept],
                            domain_b_concepts: List[DomainConcept],
                            threshold: float = 0.5) -> List[Analogy]:
        """Find analogies between domains"""
        
        analogies = []
        
        for concept_a in domain_a_concepts:
            for concept_b in domain_b_concepts:
                # Compute similarity
                similarity = await self.compute_structural_similarity(concept_a, concept_b)
                
                # Determine relation type (simplified)
                if similarity > threshold:
                    # Find common attributes for bridging
                    bridging = list(set(concept_a.attributes.keys()) & 
                                  set(concept_b.attributes.keys()))
                    
                    analogy = Analogy(
                        source_concept=concept_a,
                        target_concept=concept_b,
                        relation_type=RelationType.STRUCTURAL,
                        similarity_score=similarity,
                        bridging_properties=bridging
                    )
                    
                    analogies.append(analogy)
        
        self.analogies = analogies
        return analogies
    
    async def transfer_property(self, source_concept: DomainConcept,
                               target_concept: DomainConcept,
                               property_name: str) -> Optional[float]:
        """Transfer property from source to target via analogy"""
        
        # Find analogy connecting them
        matching_analogy = None
        for analogy in self.analogies:
            if (analogy.source_concept.name == source_concept.name and
                analogy.target_concept.name == target_concept.name):
                matching_analogy = analogy
                break
        
        if not matching_analogy:
            return None
        
        # Transfer if property is in bridging set
        if property_name in matching_analogy.bridging_properties:
            source_value = source_concept.attributes.get(property_name, 0.0)
            # Scale by similarity
            transferred = source_value * matching_analogy.similarity_score
            return transferred
        
        return None


class KnowledgeRecombination:
    """Recombine knowledge from multiple domains"""
    
    def __init__(self):
        self.synthesis_operations: List[Dict] = []
    
    async def mix_concepts(self, concepts: List[DomainConcept],
                          mix_ratios: Optional[List[float]] = None) -> Dict[str, float]:
        """Mix properties from multiple concepts"""
        
        if not concepts:
            return {}
        
        if mix_ratios is None:
            mix_ratios = [1.0 / len(concepts)] * len(concepts)
        
        # Collect all unique attributes
        all_attrs: Set[str] = set()
        for concept in concepts:
            all_attrs.update(concept.attributes.keys())
        
        # Blend attributes using ratios
        blended = {}
        for attr in all_attrs:
            blended_value = 0.0
            for concept, ratio in zip(concepts, mix_ratios):
                attr_val = concept.attributes.get(attr, 0.0)
                blended_value += attr_val * ratio
            
            blended[attr] = blended_value
        
        return blended
    
    async def detect_emergent_properties(self, 
                                        blended_attributes: Dict[str, float],
                                        original_concepts: List[DomainConcept]) -> List[str]:
        """Detect properties that emerge from combination"""
        
        emergent = []
        
        # Emergent = properties that didn't exist individually but appear in blend
        for attr, blend_val in blended_attributes.items():
            exists_individually = any(
                attr in concept.attributes for concept in original_concepts
            )
            
            if not exists_individually and blend_val > 0.1:
                emergent.append(attr)
        
        return emergent
    
    async def compute_novelty(self, blended: Dict[str, float],
                             original_concepts: List[DomainConcept]) -> float:
        """Compute novelty of synthesized concept"""
        
        # Novelty = fraction of emergent properties
        emergent = await self.detect_emergent_properties(blended, original_concepts)
        
        total_properties = len(blended) if blended else 1
        novelty = len(emergent) / total_properties if total_properties > 0 else 0.0
        
        return novelty


class CrossDomainSynthesisEngine:
    """Synthesize novel concepts from multiple domains"""
    
    def __init__(self):
        self.analogy_engine = AnalogyEngine()
        self.recombination = KnowledgeRecombination()
        self.synthesized: List[SynthesizedConcept] = []
    
    async def synthesize_concept(self, 
                                domain_a_concepts: List[DomainConcept],
                                domain_b_concepts: List[DomainConcept],
                                concept_name: str) -> SynthesizedConcept:
        """Synthesize novel concept from two domains"""
        
        # Step 1: Find analogies
        analogies = await self.analogy_engine.find_analogies(
            domain_a_concepts, domain_b_concepts, threshold=0.4
        )
        
        # Step 2: Combine concepts from both domains
        all_concepts = domain_a_concepts + domain_b_concepts
        blended = await self.recombination.mix_concepts(all_concepts)
        
        # Step 3: Detect emergent properties
        emergent = await self.recombination.detect_emergent_properties(blended, all_concepts)
        
        # Step 4: Compute novelty
        novelty = await self.recombination.compute_novelty(blended, all_concepts)
        
        # Create synthesized concept
        source_domains = list(set(c.domain for c in all_concepts))
        synthesized = SynthesizedConcept(
            name=concept_name,
            source_domains=source_domains,
            properties=blended,
            analogies=analogies,
            novelty_score=novelty
        )
        
        self.synthesized.append(synthesized)
        
        return synthesized
    
    async def get_statistics(self) -> Dict:
        """Get synthesis statistics"""
        
        total_synthesized = len(self.synthesized)
        total_analogies = sum(len(s.analogies) for s in self.synthesized)
        avg_novelty = sum(s.novelty_score for s in self.synthesized) / total_synthesized if total_synthesized > 0 else 0.0
        
        return {
            'total_synthesized': total_synthesized,
            'total_analogies': total_analogies,
            'avg_novelty': avg_novelty,
            'avg_analogies_per_concept': total_analogies / total_synthesized if total_synthesized > 0 else 0
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_cross_domain_synthesis():
    """Demonstrate cross-domain synthesis"""
    
    print("\n" + "=" * 70)
    print("CROSS-DOMAIN SYNTHESIS (PHASE 7D)")
    print("=" * 70)
    
    # Create domain concepts
    print("\n[Setup] Creating domain concepts...")
    
    # Supply Chain Domain
    supply_chain_concepts = [
        DomainConcept(
            name="routing",
            domain="supply_chain",
            attributes={"efficiency": 0.8, "cost": 0.4, "speed": 0.6},
            relationships={"uses": ["inventory"], "optimizes": ["cost"]}
        ),
        DomainConcept(
            name="inventory",
            domain="supply_chain",
            attributes={"capacity": 0.7, "cost": 0.5, "availability": 0.9},
            relationships={"managed_by": ["planning"]}
        )
    ]
    
    # Neural Network Domain
    neural_concepts = [
        DomainConcept(
            name="layer_routing",
            domain="neural_network",
            attributes={"efficiency": 0.75, "latency": 0.3, "accuracy": 0.9},
            relationships={"uses": ["weights"], "optimizes": ["accuracy"]}
        ),
        DomainConcept(
            name="attention",
            domain="neural_network",
            attributes={"selectivity": 0.8, "cost": 0.6, "expressiveness": 0.95},
            relationships={"manages": ["information_flow"]}
        )
    ]
    
    print(f"  Supply chain concepts: {len(supply_chain_concepts)}")
    print(f"  Neural concepts: {len(neural_concepts)}")
    
    # Initialize synthesis engine
    engine = CrossDomainSynthesisEngine()
    
    # Find analogies
    print("\n[Analogies] Finding cross-domain analogies...")
    analogies = await engine.analogy_engine.find_analogies(
        supply_chain_concepts, neural_concepts, threshold=0.4
    )
    print(f"  Found {len(analogies)} analogies")
    for analogy in analogies:
        print(f"    {analogy.source_concept.name} ↔ {analogy.target_concept.name}: {analogy.similarity_score:.3f}")
    
    # Synthesize novel concept
    print("\n[Synthesis] Creating novel architecture...")
    synthesized = await engine.synthesize_concept(
        supply_chain_concepts, neural_concepts, "adaptive_routing_network"
    )
    
    print(f"  Name: {synthesized.name}")
    print(f"  Source domains: {synthesized.source_domains}")
    print(f"  Novelty score: {synthesized.novelty_score:.3f}")
    print(f"  Properties:")
    for prop, val in list(synthesized.properties.items())[:5]:
        print(f"    {prop}: {val:.3f}")
    
    # Test property transfer
    print("\n[Transfer] Transferring properties across domains...")
    if supply_chain_concepts and neural_concepts:
        transferred = await engine.analogy_engine.transfer_property(
            supply_chain_concepts[0], neural_concepts[0], "efficiency"
        )
        if transferred is not None:
            print(f"  Transferred 'efficiency': {transferred:.3f}")
    
    # Statistics
    print("\n[Statistics]:")
    stats = await engine.get_statistics()
    print(f"  Total synthesized: {stats['total_synthesized']}")
    print(f"  Total analogies: {stats['total_analogies']}")
    print(f"  Avg novelty: {stats['avg_novelty']:.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_cross_domain_synthesis())
