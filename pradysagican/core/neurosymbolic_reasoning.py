#!/usr/bin/env python3
"""
PHASE 15: ADVANCED NEUROSYMBOLIC REASONING
Hybrid neural-symbolic integration for reasoning beyond both paradigms
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict


@dataclass
class SymbolicRule:
    """Symbolic rule (if-then logic)"""
    antecedent: str          # Condition
    consequent: str          # Conclusion
    confidence: float        # 0-1 confidence
    origin: str              # Where rule came from
    activation_count: int = 0


@dataclass
class NeuralPattern:
    """Neural pattern (learned from data)"""
    pattern_id: str
    embedding: List[float]
    activation_history: List[float] = field(default_factory=list)
    confidence: float = 0.5


class SymbolicKnowledgeBase:
    """Symbolic reasoning with rules"""
    
    def __init__(self):
        self.rules: Dict[str, SymbolicRule] = {}
        self.facts: Set[str] = set()
        self.inference_chain: List[str] = []
        self.contradiction_log: List[Tuple[str, str]] = []
    
    async def add_rule(self, rule: SymbolicRule) -> None:
        """Add symbolic rule"""
        self.rules[rule.antecedent] = rule
    
    async def add_fact(self, fact: str) -> None:
        """Add ground truth fact"""
        self.facts.add(fact)
    
    async def forward_chain(self, max_iterations: int = 5) -> List[str]:
        """Forward chaining inference"""
        
        new_facts = set(self.facts)
        self.inference_chain = []
        
        for iteration in range(max_iterations):
            derived_this_iteration = False
            
            for antecedent, rule in self.rules.items():
                # Check if antecedent matches facts
                if antecedent in new_facts:
                    # Derive consequent
                    if rule.confidence > 0.7:  # High confidence threshold
                        new_facts.add(rule.consequent)
                        self.inference_chain.append(f"{antecedent} → {rule.consequent}")
                        rule.activation_count += 1
                        derived_this_iteration = True
            
            if not derived_this_iteration:
                break
        
        return self.inference_chain
    
    async def detect_contradictions(self, new_fact: str) -> List[str]:
        """Detect contradictions with existing facts"""
        
        contradictions = []
        
        # Simple negation-based contradiction detection
        negation_prefixes = ['NOT', 'no', 'not', '¬']
        
        for existing_fact in self.facts:
            for prefix in negation_prefixes:
                if f"{prefix}_{new_fact}" == existing_fact or \
                   existing_fact.startswith(f"{prefix}") and \
                   existing_fact.replace(f"{prefix}_", "") == new_fact:
                    contradictions.append((existing_fact, new_fact))
                    self.contradiction_log.append((existing_fact, new_fact))
        
        return contradictions


class NeuralPatternLearner:
    """Learn neural patterns from data"""
    
    def __init__(self, embedding_dim: int = 8):
        self.embedding_dim = embedding_dim
        self.patterns: Dict[str, NeuralPattern] = {}
        self.learned_embeddings: List[List[float]] = []
    
    async def learn_pattern(self, pattern_id: str, data_points: List[float]) -> NeuralPattern:
        """Learn pattern embedding from data"""
        
        if not data_points:
            embedding = [0.0] * self.embedding_dim
        else:
            # Simulate neural learning: create embedding from data statistics
            avg = sum(data_points) / len(data_points) if data_points else 0
            max_val = max(data_points) if data_points else 0
            min_val = min(data_points) if data_points else 0
            
            embedding = [
                avg / (max_val - min_val + 0.1),
                len(data_points) / 100.0,
                max_val / 100.0,
                min_val / 100.0
            ]
            
            # Pad to embedding_dim
            while len(embedding) < self.embedding_dim:
                embedding.append(0.0)
            embedding = embedding[:self.embedding_dim]
        
        pattern = NeuralPattern(
            pattern_id=pattern_id,
            embedding=embedding,
            confidence=min(1.0, len(data_points) / 10.0)  # Confidence from data volume
        )
        
        self.patterns[pattern_id] = pattern
        self.learned_embeddings.append(embedding)
        
        return pattern
    
    async def find_similar_patterns(self, pattern_id: str, k: int = 3) -> List[Tuple[str, float]]:
        """Find similar patterns (nearest neighbors)"""
        
        if pattern_id not in self.patterns:
            return []
        
        query_embedding = self.patterns[pattern_id].embedding
        
        similarities = []
        
        for other_id, other_pattern in self.patterns.items():
            if other_id != pattern_id:
                # Compute cosine similarity
                dot_product = sum(a * b for a, b in zip(query_embedding, other_pattern.embedding))
                norm_query = sum(x**2 for x in query_embedding) ** 0.5
                norm_other = sum(x**2 for x in other_pattern.embedding) ** 0.5
                
                similarity = dot_product / (norm_query * norm_other + 0.001)
                similarities.append((other_id, similarity))
        
        return sorted(similarities, key=lambda x: x[1], reverse=True)[:k]


class NeuroSymbolicIntegrator:
    """Integrate neural and symbolic reasoning"""
    
    def __init__(self):
        self.symbolic_kb = SymbolicKnowledgeBase()
        self.neural_learner = NeuralPatternLearner()
        self.integration_log: List[Dict] = []
        self.hybrid_conclusions: List[str] = []
    
    async def neural_to_symbolic(self) -> List[SymbolicRule]:
        """Convert learned neural patterns to symbolic rules"""
        
        extracted_rules = []
        
        for pattern_id, pattern in self.neural_learner.patterns.items():
            # Extract rule from pattern (simplified)
            if pattern.confidence > 0.5:
                # Create symbolic rule from neural pattern
                rule = SymbolicRule(
                    antecedent=f"Pattern_{pattern_id}_detected",
                    consequent=f"Activate_{pattern_id}",
                    confidence=pattern.confidence,
                    origin=f"neural_{pattern_id}"
                )
                
                await self.symbolic_kb.add_rule(rule)
                extracted_rules.append(rule)
        
        return extracted_rules
    
    async def symbolic_to_neural(self, rule: SymbolicRule) -> Optional[NeuralPattern]:
        """Convert symbolic rule to neural pattern"""
        
        # Create synthetic data from rule
        synthetic_data = []
        
        for i in range(10):
            # Generate data consistent with rule
            value = 0.5 + (i * 0.1) if rule.confidence > 0.5 else 0.3
            synthetic_data.append(value)
        
        # Learn pattern
        pattern = await self.neural_learner.learn_pattern(
            f"from_rule_{rule.antecedent}",
            synthetic_data
        )
        
        return pattern
    
    async def hybrid_reasoning(self, query: str) -> Dict:
        """Hybrid neural-symbolic reasoning"""
        
        result = {
            'query': query,
            'symbolic_conclusions': [],
            'neural_conclusions': [],
            'hybrid_conclusion': None,
            'confidence': 0.0
        }
        
        # 1. Symbolic forward chaining
        await self.symbolic_kb.add_fact(query)
        symbolic_chain = await self.symbolic_kb.forward_chain()
        result['symbolic_conclusions'] = symbolic_chain
        
        # 2. Neural pattern matching
        if query in self.neural_learner.patterns:
            similar = await self.neural_learner.find_similar_patterns(query, k=2)
            result['neural_conclusions'] = [f"Similar to {pid}" for pid, sim in similar]
        
        # 3. Integrate conclusions
        if symbolic_chain and result['neural_conclusions']:
            hybrid = f"Symbolic: {symbolic_chain[-1] if symbolic_chain else 'none'} + Neural: {result['neural_conclusions'][0] if result['neural_conclusions'] else 'none'}"
            result['hybrid_conclusion'] = hybrid
            result['confidence'] = 0.8
        elif symbolic_chain:
            result['hybrid_conclusion'] = symbolic_chain[-1] if symbolic_chain else None
            result['confidence'] = 0.6
        elif result['neural_conclusions']:
            result['hybrid_conclusion'] = result['neural_conclusions'][0]
            result['confidence'] = 0.5
        
        self.integration_log.append(result)
        return result


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_neurosymbolic_reasoning():
    """Demonstrate neurosymbolic reasoning"""
    
    print("\n" + "=" * 70)
    print("ADVANCED NEUROSYMBOLIC REASONING (PHASE 15)")
    print("=" * 70)
    
    integrator = NeuroSymbolicIntegrator()
    
    # 1. Set up symbolic rules
    print("\n[Symbolic] Building knowledge base...")
    
    rule1 = SymbolicRule(
        antecedent="problem_complex",
        consequent="use_ensemble",
        confidence=0.9,
        origin="heuristic"
    )
    
    rule2 = SymbolicRule(
        antecedent="use_ensemble",
        consequent="aggregate_results",
        confidence=0.85,
        origin="heuristic"
    )
    
    await integrator.symbolic_kb.add_rule(rule1)
    await integrator.symbolic_kb.add_rule(rule2)
    
    print(f"  Rules loaded: {len(integrator.symbolic_kb.rules)}")
    
    # 2. Learn neural patterns
    print("\n[Neural] Learning patterns...")
    
    data1 = [0.1, 0.2, 0.15, 0.18, 0.12, 0.22, 0.18, 0.20, 0.14, 0.19]
    pattern1 = await integrator.neural_learner.learn_pattern("feature_A", data1)
    
    data2 = [0.8, 0.85, 0.82, 0.87, 0.81, 0.86, 0.83, 0.88, 0.84, 0.86]
    pattern2 = await integrator.neural_learner.learn_pattern("feature_B", data2)
    
    print(f"  Patterns learned: {len(integrator.neural_learner.patterns)}")
    print(f"  Embeddings created: {len(integrator.neural_learner.learned_embeddings)}")
    
    # 3. Neural-to-symbolic extraction
    print("\n[Extraction] Converting neural to symbolic...")
    extracted = await integrator.neural_to_symbolic()
    print(f"  Rules extracted: {len(extracted)}")
    
    # 4. Forward chaining
    print("\n[Inference] Forward chaining...")
    chain = await integrator.symbolic_kb.forward_chain()
    print(f"  Inferences: {len(chain)}")
    for step in chain[:3]:
        print(f"    - {step}")
    
    # 5. Hybrid reasoning
    print("\n[Hybrid] Performing hybrid reasoning...")
    result1 = await integrator.hybrid_reasoning("problem_complex")
    print(f"  Query: {result1['query']}")
    print(f"  Symbolic: {result1['symbolic_conclusions'][:1] if result1['symbolic_conclusions'] else 'none'}")
    print(f"  Neural: {result1['neural_conclusions'][:1] if result1['neural_conclusions'] else 'none'}")
    print(f"  Hybrid: {result1['hybrid_conclusion']}")
    print(f"  Confidence: {result1['confidence']:.1%}")
    
    # 6. Pattern similarity
    print("\n[Similarity] Finding similar patterns...")
    if "feature_A" in integrator.neural_learner.patterns:
        similar = await integrator.neural_learner.find_similar_patterns("feature_A", k=1)
        for pattern_id, similarity in similar:
            print(f"  Similar pattern: {pattern_id} (similarity: {similarity:.3f})")
    
    # Statistics
    print("\n[Statistics]:")
    print(f"  Symbolic rules: {len(integrator.symbolic_kb.rules)}")
    print(f"  Neural patterns: {len(integrator.neural_learner.patterns)}")
    print(f"  Integration events: {len(integrator.integration_log)}")
    print(f"  Contradictions detected: {len(integrator.symbolic_kb.contradiction_log)}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_neurosymbolic_reasoning())
