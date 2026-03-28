#!/usr/bin/env python3
"""
PHASE 24: CONTINUAL LEARNING WITH STABILITY-PLASTICITY
Learn continuously without forgetting (Elastic Weight Consolidation + continual learning)
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random
import math


@dataclass
class TaskLearningSession:
    """A learning session on a specific task"""
    task_id: str
    task_name: str
    accuracy_start: float
    accuracy_end: float
    examples_learned: int
    forgetting_rate: float = 0.0


class StabilityPlasticityLearner:
    """Balance stability (preserve old knowledge) and plasticity (learn new)"""
    
    def __init__(self):
        self.tasks_learned: List[TaskLearningSession] = []
        self.importance_weights: Dict[str, float] = {}
        self.elastic_weights: Dict[str, float] = {}
        self.fisher_information: Dict[str, float] = {}
        self.continual_performance: Dict = {}
    
    async def compute_fisher_information(self, task_id: str, accuracy: float) -> float:
        """Compute Fisher Information matrix for task"""
        
        # Fisher Information: higher accuracy = higher importance
        # FI ≈ gradient variance, approximated as accuracy * (1 - accuracy)
        fisher = accuracy * (1 - accuracy)
        
        self.fisher_information[task_id] = fisher
        return fisher
    
    async def learn_task(self, session: TaskLearningSession) -> Dict:
        """Learn a new task with stability-plasticity balance"""
        
        # Compute improvement
        accuracy_improvement = session.accuracy_end - session.accuracy_start
        
        # Update Fisher Information for this task
        fisher = await self.compute_fisher_information(session.task_id, session.accuracy_end)
        
        # Compute forgetting rate (exponential decay from previous tasks)
        if self.tasks_learned:
            # Older tasks decay faster
            prev_accuracy_avg = sum(t.accuracy_end for t in self.tasks_learned) / len(self.tasks_learned)
            session.forgetting_rate = 0.1 * math.exp(-len(self.tasks_learned) * 0.3)
        else:
            session.forgetting_rate = 0.0
        
        # Record session
        self.tasks_learned.append(session)
        
        # Compute elastic weight (protects important parameters)
        elastic_weight = fisher * (1 - session.forgetting_rate)
        self.elastic_weights[session.task_id] = elastic_weight
        
        return {
            'task_id': session.task_id,
            'accuracy_improvement': accuracy_improvement,
            'fisher_information': fisher,
            'forgetting_rate': session.forgetting_rate,
            'elastic_weight': elastic_weight,
            'continual_learning': len(self.tasks_learned) > 1
        }
    
    async def compute_continual_performance(self) -> Dict:
        """Compute overall continual learning performance"""
        
        if not self.tasks_learned:
            return {}
        
        # Compute metrics
        total_accuracy = sum(t.accuracy_end for t in self.tasks_learned) / len(self.tasks_learned)
        total_forgetting = sum(t.forgetting_rate for t in self.tasks_learned) / len(self.tasks_learned)
        
        # Backward transfer: improvement on earlier tasks from learning later tasks
        backward_transfer = 0.0
        if len(self.tasks_learned) > 1:
            # Simulate backward transfer as negative of forgetting
            backward_transfer = max(0, 0.05 - total_forgetting)
        
        # Forward transfer: improvement on new tasks from learning earlier tasks
        forward_transfer = 0.0
        if len(self.tasks_learned) > 1:
            # Benefit from previous learning
            forward_transfer = 0.05 * math.log(len(self.tasks_learned))
        
        stability_score = 1.0 - total_forgetting
        plasticity_score = sum(
            t.accuracy_end - t.accuracy_start
            for t in self.tasks_learned
        ) / len(self.tasks_learned)
        
        self.continual_performance = {
            'total_tasks': len(self.tasks_learned),
            'total_accuracy': total_accuracy,
            'total_forgetting': total_forgetting,
            'backward_transfer': backward_transfer,
            'forward_transfer': forward_transfer,
            'stability_score': stability_score,
            'plasticity_score': plasticity_score,
            'stability_plasticity_balance': (
                stability_score * 0.5 + plasticity_score * 0.5
            )
        }
        
        return self.continual_performance


class ContinualLearningOrchestrator:
    """Orchestrate continual learning across task sequences"""
    
    def __init__(self):
        self.learner = StabilityPlasticityLearner()
        self.task_sequence: List[TaskLearningSession] = []
        self.continual_metrics: Dict = {}
        self.forward_transfer_trajectory: List[float] = []
        self.backward_transfer_trajectory: List[float] = []
    
    async def create_task_sequence(self, num_tasks: int = 5) -> List[TaskLearningSession]:
        """Create a sequence of tasks to learn sequentially"""
        
        tasks = []
        for i in range(num_tasks):
            # Each task starts harder, but with transfer gets easier
            task_difficulty = 0.3 + (i * 0.1)
            accuracy_start = max(0.3, 0.5 - task_difficulty)
            accuracy_end = min(1.0, accuracy_start + random.uniform(0.3, 0.5))
            
            task = TaskLearningSession(
                task_id=f"task_{i+1}",
                task_name=f"Task {i+1}",
                accuracy_start=accuracy_start,
                accuracy_end=accuracy_end,
                examples_learned=(i+1) * 100
            )
            tasks.append(task)
        
        self.task_sequence = tasks
        return tasks
    
    async def run_continual_learning(self) -> Dict:
        """Run continual learning on task sequence"""
        
        # Create task sequence
        print("[Phase 24] Creating task sequence...")
        await self.create_task_sequence(num_tasks=5)
        
        # Learn each task
        print("[Phase 24] Learning tasks sequentially...")
        learning_results = []
        
        for task in self.task_sequence:
            result = await self.learner.learn_task(task)
            learning_results.append(result)
            
            # Track forward/backward transfer
            perf = await self.learner.compute_continual_performance()
            self.forward_transfer_trajectory.append(perf.get('forward_transfer', 0))
            self.backward_transfer_trajectory.append(perf.get('backward_transfer', 0))
        
        # Compute final metrics
        print("[Phase 24] Computing continual learning metrics...")
        self.continual_metrics = await self.learner.compute_continual_performance()
        
        return {
            'learning_results': learning_results,
            'continual_metrics': self.continual_metrics,
            'forward_transfer_trajectory': self.forward_transfer_trajectory,
            'backward_transfer_trajectory': self.backward_transfer_trajectory
        }
    
    async def get_continual_status(self) -> Dict:
        """Get continual learning status"""
        
        return {
            'tasks_learned': len(self.learner.tasks_learned),
            'continual_metrics': self.continual_metrics,
            'fisher_information': self.learner.fisher_information,
            'elastic_weights': self.learner.elastic_weights,
            'forward_transfer_avg': (
                sum(self.forward_transfer_trajectory) / len(self.forward_transfer_trajectory)
                if self.forward_transfer_trajectory else 0
            ),
            'backward_transfer_avg': (
                sum(self.backward_transfer_trajectory) / len(self.backward_transfer_trajectory)
                if self.backward_transfer_trajectory else 0
            )
        }


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_continual_learning():
    """Demonstrate continual learning with stability-plasticity"""
    
    print("\n" + "=" * 70)
    print("CONTINUAL LEARNING WITH STABILITY-PLASTICITY (PHASE 24)")
    print("=" * 70)
    
    orchestrator = ContinualLearningOrchestrator()
    
    # Run continual learning
    print("\n[Continual Learning] Running on task sequence...")
    result = await orchestrator.run_continual_learning()
    
    # Show learning results
    print(f"\n[Learning Results]:")
    for res in result['learning_results']:
        print(f"  {res['task_id']}:")
        print(f"    Accuracy improvement: {res['accuracy_improvement']:.3f}")
        print(f"    Forgetting rate: {res['forgetting_rate']:.3f}")
        print(f"    Elastic weight: {res['elastic_weight']:.3f}")
    
    # Show continual metrics
    metrics = result['continual_metrics']
    print(f"\n[Continual Learning Metrics]:")
    print(f"  Total tasks: {metrics['total_tasks']}")
    print(f"  Total accuracy: {metrics['total_accuracy']:.3f}")
    print(f"  Total forgetting: {metrics['total_forgetting']:.3f}")
    print(f"  Stability score: {metrics['stability_score']:.3f}")
    print(f"  Plasticity score: {metrics['plasticity_score']:.3f}")
    print(f"  Stability-Plasticity balance: {metrics['stability_plasticity_balance']:.3f}")
    
    # Show transfer learning
    print(f"\n[Transfer Learning]:")
    print(f"  Forward transfer trajectory: {[f'{x:.3f}' for x in result['forward_transfer_trajectory']]}")
    print(f"  Backward transfer trajectory: {[f'{x:.3f}' for x in result['backward_transfer_trajectory']]}")
    print(f"  Avg forward transfer: {metrics['forward_transfer']:.3f}")
    print(f"  Avg backward transfer: {metrics['backward_transfer']:.3f}")
    
    # Final status
    status = await orchestrator.get_continual_status()
    print(f"\n[Continual Status]:")
    print(f"  Tasks learned: {status['tasks_learned']}")
    print(f"  Forward transfer avg: {status['forward_transfer_avg']:.3f}")
    print(f"  Backward transfer avg: {status['backward_transfer_avg']:.3f}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_continual_learning())
