#!/usr/bin/env python3
"""
PHASE 22: META-LEARNING ACROSS DOMAINS
Learn how to learn in different domains and transfer that meta-knowledge
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random


@dataclass
class LearningTask:
    """A learning task in a specific domain"""
    task_id: str
    domain: str
    task_type: str
    examples: int
    target_accuracy: float


@dataclass
class MetaStrategy:
    """A meta-learning strategy (how to learn)"""
    strategy_id: str
    name: str
    steps: List[str]
    success_rate: float
    applicable_domains: List[str]
    transfer_potential: float


class DomainMetaLearner:
    """Learn meta-strategies for different domains"""
    
    def __init__(self):
        self.domains: Dict[str, Dict] = {}
        self.meta_strategies: Dict[str, MetaStrategy] = {}
        self.cross_domain_strategies: List[MetaStrategy] = []
        self.meta_learning_curve: List[float] = []
        self.strategy_effectiveness: Dict[str, float] = {}
    
    async def learn_domain_strategy(self, domain: str, tasks: List[LearningTask]) -> MetaStrategy:
        """Learn a meta-strategy for a specific domain"""
        
        # Simulate learning from multiple tasks in domain
        success_count = 0
        total_accuracy = 0
        
        for task in tasks:
            # Simulate learning: more examples = higher accuracy
            base_accuracy = 0.5 + (task.examples / (task.examples + 100))
            accuracy = min(1.0, base_accuracy + random.random() * 0.2)
            
            if accuracy >= task.target_accuracy:
                success_count += 1
            total_accuracy += accuracy
        
        # Infer meta-strategy from successful tasks
        success_rate = success_count / len(tasks) if tasks else 0
        avg_accuracy = total_accuracy / len(tasks) if tasks else 0
        
        strategy = MetaStrategy(
            strategy_id=f"META_{domain}_{len(self.meta_strategies)}",
            name=f"{domain} Learning Strategy",
            steps=[
                "data_augmentation",
                "feature_engineering",
                "model_selection",
                "hyperparameter_tuning",
                "ensemble_voting",
                "transfer_learning"
            ],
            success_rate=success_rate,
            applicable_domains=[domain],
            transfer_potential=avg_accuracy * 0.8  # 80% of accuracy transfers
        )
        
        self.meta_strategies[strategy.strategy_id] = strategy
        self.meta_learning_curve.append(success_rate)
        
        return strategy
    
    async def transfer_strategy_to_domain(self, strategy: MetaStrategy, target_domain: str) -> MetaStrategy:
        """Transfer a meta-strategy to a different domain"""
        
        # Create adapted strategy for target domain
        transfer_effectiveness = strategy.transfer_potential
        
        adapted_strategy = MetaStrategy(
            strategy_id=f"TRANSFER_{strategy.strategy_id}_{target_domain}",
            name=f"{strategy.name} (→ {target_domain})",
            steps=strategy.steps,
            success_rate=strategy.success_rate * transfer_effectiveness,
            applicable_domains=strategy.applicable_domains + [target_domain],
            transfer_potential=transfer_effectiveness * 0.9  # Decreases with transfers
        )
        
        self.cross_domain_strategies.append(adapted_strategy)
        
        return adapted_strategy
    
    async def combine_strategies(self, strategies: List[MetaStrategy]) -> MetaStrategy:
        """Combine multiple strategies into ensemble meta-strategy"""
        
        # Ensemble: take best steps from each
        all_steps = []
        for strategy in strategies:
            all_steps.extend(strategy.steps)
        
        # Deduplicate and order
        unique_steps = list(dict.fromkeys(all_steps))
        
        # Combined success rate
        avg_success = sum(s.success_rate for s in strategies) / len(strategies) if strategies else 0
        avg_transfer = sum(s.transfer_potential for s in strategies) / len(strategies) if strategies else 0
        
        combined = MetaStrategy(
            strategy_id=f"ENSEMBLE_{len(self.meta_strategies)}",
            name="Ensemble Meta-Strategy",
            steps=unique_steps,
            success_rate=min(1.0, avg_success * 1.2),  # Ensemble boost
            applicable_domains=list(set(
                domain for s in strategies for domain in s.applicable_domains
            )),
            transfer_potential=avg_transfer
        )
        
        return combined


class MetaLearningOrchestrator:
    """Orchestrate meta-learning across domains"""
    
    def __init__(self):
        self.learner = DomainMetaLearner()
        self.domains: Dict[str, List[LearningTask]] = {}
        self.meta_knowledge: Dict = {}
        self.universal_meta_strategy: Optional[MetaStrategy] = None
    
    async def populate_domains(self):
        """Populate learning tasks for multiple domains"""
        
        domains_tasks = {
            "Computer Vision": [
                LearningTask(f"cv_task_{i}", "Computer Vision", "classification", 100+i*50, 0.85)
                for i in range(3)
            ],
            "Natural Language Processing": [
                LearningTask(f"nlp_task_{i}", "NLP", "sequence_labeling", 150+i*50, 0.82)
                for i in range(3)
            ],
            "Time Series": [
                LearningTask(f"ts_task_{i}", "Time Series", "forecasting", 200+i*50, 0.80)
                for i in range(3)
            ],
            "Reinforcement Learning": [
                LearningTask(f"rl_task_{i}", "RL", "control", 300+i*50, 0.75)
                for i in range(3)
            ],
            "Graph Learning": [
                LearningTask(f"gn_task_{i}", "Graph", "node_classification", 250+i*50, 0.78)
                for i in range(3)
            ],
        }
        
        self.domains = domains_tasks
    
    async def run_meta_learning_across_domains(self) -> Dict:
        """Run meta-learning across all domains"""
        
        await self.populate_domains()
        
        # Learn domain-specific strategies
        domain_strategies = {}
        for domain, tasks in self.domains.items():
            strategy = await self.learner.learn_domain_strategy(domain, tasks)
            domain_strategies[domain] = strategy
        
        # Transfer strategies between domains
        transferred_strategies = []
        for source_domain, strategy in list(domain_strategies.items())[:2]:
            target_domain = list(self.domains.keys())[3]
            transferred = await self.learner.transfer_strategy_to_domain(strategy, target_domain)
            transferred_strategies.append(transferred)
        
        # Combine into universal meta-strategy
        all_strategies = list(domain_strategies.values()) + transferred_strategies
        universal_strategy = await self.learner.combine_strategies(all_strategies)
        self.universal_meta_strategy = universal_strategy
        
        # Build meta-knowledge
        self.meta_knowledge = {
            'domain_count': len(self.domains),
            'domain_strategies': {
                domain: {
                    'success_rate': s.success_rate,
                    'transfer_potential': s.transfer_potential
                }
                for domain, s in domain_strategies.items()
            },
            'transferred_strategies': len(transferred_strategies),
            'universal_strategy': {
                'name': universal_strategy.name,
                'success_rate': universal_strategy.success_rate,
                'domains': len(universal_strategy.applicable_domains),
                'transfer_potential': universal_strategy.transfer_potential
            },
            'meta_learning_curve': self.learner.meta_learning_curve,
            'avg_meta_success': sum(self.learner.meta_learning_curve) / len(self.learner.meta_learning_curve)
            if self.learner.meta_learning_curve else 0
        }
        
        return {
            'domain_strategies': domain_strategies,
            'universal_strategy': universal_strategy,
            'meta_knowledge': self.meta_knowledge
        }
    
    async def get_meta_status(self) -> Dict:
        """Get meta-learning status"""
        
        return {
            'domains_learned': len(self.domains),
            'domain_strategies': len(self.learner.meta_strategies),
            'cross_domain_transfers': len(self.learner.cross_domain_strategies),
            'universal_strategy': self.universal_meta_strategy.name if self.universal_meta_strategy else None,
            'avg_success_rate': self.meta_knowledge.get('avg_meta_success', 0),
            'meta_knowledge': self.meta_knowledge
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_meta_learning():
    """Demonstrate meta-learning across domains"""
    
    print("\n" + "=" * 70)
    print("META-LEARNING ACROSS DOMAINS (PHASE 22)")
    print("=" * 70)
    
    orchestrator = MetaLearningOrchestrator()
    
    # Run meta-learning
    print("\n[Meta-Learning] Running across multiple domains...")
    result = await orchestrator.run_meta_learning_across_domains()
    
    # Show domain strategies
    print(f"\n[Domain Strategies]:")
    for domain, strategy in result['domain_strategies'].items():
        print(f"  {domain}:")
        print(f"    Success rate: {strategy.success_rate:.3f}")
        print(f"    Transfer potential: {strategy.transfer_potential:.3f}")
    
    # Show universal strategy
    universal = result['universal_strategy']
    print(f"\n[Universal Strategy]: {universal.name}")
    print(f"  Success rate: {universal.success_rate:.3f}")
    print(f"  Transfer potential: {universal.transfer_potential:.3f}")
    print(f"  Applicable domains: {len(universal.applicable_domains)}")
    print(f"  Strategy steps: {len(universal.steps)}")
    
    # Show meta-knowledge
    meta = result['meta_knowledge']
    print(f"\n[Meta-Knowledge]:")
    print(f"  Average meta-success: {meta['avg_meta_success']:.3f}")
    print(f"  Domain count: {meta['domain_count']}")
    print(f"  Cross-domain transfers: {meta['transferred_strategies']}")
    print(f"  Learning curve trajectory: {len(meta['meta_learning_curve'])} points")
    
    # Final status
    status = await orchestrator.get_meta_status()
    print(f"\n[Status]:")
    print(f"  Domains learned: {status['domains_learned']}")
    print(f"  Domain strategies: {status['domain_strategies']}")
    print(f"  Cross-domain transfers: {status['cross_domain_transfers']}")
    print(f"  Avg success rate: {status['avg_success_rate']:.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_meta_learning())
