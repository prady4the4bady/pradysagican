#!/usr/bin/env python3
"""
PHASE 6C: ADVANCED META-LEARNING
Model-Agnostic Meta-Learning (MAML) for task adaptation
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional, Callable
from datetime import datetime


# ════════════════════════════════════════════════════════════════════════════
# TASK & LEARNING MODELS
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class Task:
    """Single learning task"""
    task_id: str
    task_type: str
    train_samples: List[Dict[str, float]]
    test_samples: List[Dict[str, float]]
    target_variable: str
    difficulty: float = 0.5


class SimpleLinearModel:
    """Simple linear model for demonstrations"""
    
    def __init__(self, input_dim: int = 3):
        self.weights = {f"w{i}": random.gauss(0, 0.1) for i in range(input_dim)}
        self.bias = random.gauss(0, 0.1)
        self.learning_history: List[float] = []
    
    async def predict(self, features: Dict[str, float]) -> float:
        """Make prediction"""
        output = self.bias
        for key, value in self.weights.items():
            if key in features:
                output += value * features[key]
        return output
    
    async def compute_loss(self, sample: Dict[str, float], target: str) -> float:
        """Compute MSE loss"""
        prediction = await self.predict(sample)
        actual = sample.get(target, 0.0)
        return (prediction - actual) ** 2
    
    async def update_weights(self, gradients: Dict[str, float], learning_rate: float = 0.01) -> None:
        """Update weights using gradients"""
        for key, grad in gradients.items():
            if key in self.weights:
                self.weights[key] -= learning_rate * grad
            elif key == 'bias':
                self.bias -= learning_rate * grad
    
    async def clone(self) -> 'SimpleLinearModel':
        """Create a copy of this model"""
        new_model = SimpleLinearModel(len(self.weights))
        new_model.weights = self.weights.copy()
        new_model.bias = self.bias
        return new_model


# ════════════════════════════════════════════════════════════════════════════
# MAML OPTIMIZER
# ════════════════════════════════════════════════════════════════════════════

class MAMLOptimizer:
    """Model-Agnostic Meta-Learning optimizer"""
    
    def __init__(self, inner_lr: float = 0.01, outer_lr: float = 0.001, inner_steps: int = 5):
        self.inner_lr = inner_lr          # Task adaptation learning rate
        self.outer_lr = outer_lr          # Meta-learning rate
        self.inner_steps = inner_steps    # Adaptation steps per task
        self.meta_model: Optional[SimpleLinearModel] = None
        self.meta_losses: List[float] = []
        self.task_adaptation_times: List[float] = []
    
    async def compute_gradients(self, model: SimpleLinearModel, 
                               samples: List[Dict[str, float]], 
                               target: str) -> Dict[str, float]:
        """Compute gradients for a batch"""
        gradients = {f"w{i}": 0.0 for i in range(len(model.weights))}
        gradients['bias'] = 0.0
        
        batch_size = len(samples)
        for sample in samples:
            loss = await model.compute_loss(sample, target)
            
            # Simple gradient estimation
            for key in model.weights.keys():
                feature_val = sample.get(key.replace('w', 'x'), 0.0)
                gradients[key] += 2 * (await model.predict(sample) - sample.get(target, 0.0)) * feature_val / batch_size
            
            gradients['bias'] += 2 * (await model.predict(sample) - sample.get(target, 0.0)) / batch_size
        
        return gradients
    
    async def inner_loop(self, model: SimpleLinearModel, task: Task) -> Tuple[SimpleLinearModel, float]:
        """Adapt model to a single task"""
        adapted_model = await model.clone()
        
        # Take gradient steps on task
        for step in range(self.inner_steps):
            grads = await self.compute_gradients(adapted_model, task.train_samples, task.target_variable)
            await adapted_model.update_weights(grads, learning_rate=self.inner_lr)
        
        # Evaluate on test set
        test_loss = 0.0
        for sample in task.test_samples:
            test_loss += await adapted_model.compute_loss(sample, task.target_variable)
        test_loss /= len(task.test_samples) if task.test_samples else 1.0
        
        return adapted_model, test_loss
    
    async def outer_loop(self, tasks: List[Task], batch_size: int = 4) -> float:
        """Meta-learning step across tasks"""
        
        if not self.meta_model:
            self.meta_model = SimpleLinearModel()
        
        # Sample batch of tasks
        task_batch = random.sample(tasks, min(batch_size, len(tasks)))
        
        meta_loss = 0.0
        
        for task in task_batch:
            # Inner loop: adapt to task
            adapted_model, task_loss = await self.inner_loop(self.meta_model, task)
            meta_loss += task_loss
        
        meta_loss /= len(task_batch)
        self.meta_losses.append(meta_loss)
        
        return meta_loss
    
    async def adapt_to_task(self, task: Task, steps: Optional[int] = None) -> SimpleLinearModel:
        """Quickly adapt meta-model to new task"""
        
        if not self.meta_model:
            self.meta_model = SimpleLinearModel()
        
        adapted_model = await self.meta_model.clone()
        
        # Quick adaptation
        adapt_steps = steps or self.inner_steps
        for step in range(adapt_steps):
            grads = await self.compute_gradients(adapted_model, task.train_samples, task.target_variable)
            await adapted_model.update_weights(grads, learning_rate=self.inner_lr)
        
        return adapted_model
    
    async def few_shot_learning(self, task: Task, num_samples: int = 3) -> SimpleLinearModel:
        """Learn from very few samples"""
        
        # Use only few samples for training
        few_samples = task.train_samples[:num_samples]
        few_task = Task(
            task_id=task.task_id,
            task_type=task.task_type,
            train_samples=few_samples,
            test_samples=task.test_samples,
            target_variable=task.target_variable
        )
        
        # Adapt
        adapted_model = await self.adapt_to_task(few_task, steps=3)
        
        return adapted_model


# ════════════════════════════════════════════════════════════════════════════
# TASK GENERATION & LEARNING CURVES
# ════════════════════════════════════════════════════════════════════════════

async def generate_tasks(num_tasks: int = 20) -> List[Task]:
    """Generate synthetic tasks"""
    tasks = []
    
    for i in range(num_tasks):
        # Generate task with random parameters
        task_type = random.choice(['regression', 'classification', 'ranking'])
        difficulty = random.random() * 0.5 + 0.25  # [0.25, 0.75]
        
        # Generate training samples
        train_samples = []
        for j in range(5):
            sample = {
                'x0': random.random(),
                'x1': random.random(),
                'x2': random.random(),
            }
            # Target is a simple function of inputs
            sample['y'] = sample['x0'] * 0.5 + sample['x1'] * 0.3 + sample['x2'] * 0.2 + random.gauss(0, 0.05)
            train_samples.append(sample)
        
        # Generate test samples
        test_samples = []
        for j in range(3):
            sample = {
                'x0': random.random(),
                'x1': random.random(),
                'x2': random.random(),
            }
            sample['y'] = sample['x0'] * 0.5 + sample['x1'] * 0.3 + sample['x2'] * 0.2 + random.gauss(0, 0.05)
            test_samples.append(sample)
        
        task = Task(
            task_id=f"task_{i:03d}",
            task_type=task_type,
            train_samples=train_samples,
            test_samples=test_samples,
            target_variable='y',
            difficulty=difficulty
        )
        
        tasks.append(task)
    
    return tasks


# ════════════════════════════════════════════════════════════════════════════
# DEMO
# ════════════════════════════════════════════════════════════════════════════

async def demo_meta_learning():
    """Demonstrate advanced meta-learning"""
    
    print("\n" + "=" * 70)
    print("ADVANCED META-LEARNING (MAML) - PHASE 6C")
    print("=" * 70)
    
    # Generate tasks
    print("\n[Setup] Generating tasks...")
    all_tasks = await generate_tasks(20)
    print(f"  Generated {len(all_tasks)} tasks")
    
    # Initialize MAML
    maml = MAMLOptimizer(inner_lr=0.01, outer_lr=0.001, inner_steps=5)
    
    # Meta-training
    print("\n[Meta-Training] Learning across tasks...")
    for epoch in range(5):
        meta_loss = await maml.outer_loop(all_tasks, batch_size=4)
        print(f"  Epoch {epoch}: Meta-loss = {meta_loss:.4f}")
    
    # Test on new task
    print("\n[Few-Shot Learning] Testing on new task...")
    new_task = await generate_tasks(1)
    new_task = new_task[0]
    
    # Few-shot adaptation
    adapted = await maml.few_shot_learning(new_task, num_samples=3)
    
    # Evaluate
    test_loss = 0.0
    for sample in new_task.test_samples:
        test_loss += await adapted.compute_loss(sample, new_task.target_variable)
    test_loss /= len(new_task.test_samples)
    
    print(f"  Few-shot task test loss: {test_loss:.4f}")
    
    # Test adaptation speed
    print("\n[Adaptation Speed] Testing quick adaptation...")
    quick_adapted = await maml.adapt_to_task(new_task, steps=3)
    quick_loss = 0.0
    for sample in new_task.test_samples:
        quick_loss += await quick_adapted.compute_loss(sample, new_task.target_variable)
    quick_loss /= len(new_task.test_samples)
    
    print(f"  3-step adaptation test loss: {quick_loss:.4f}")
    
    # Learning curve
    print("\n[Learning Curve] Meta-learning progress:")
    for i, loss in enumerate(maml.meta_losses):
        print(f"  Epoch {i}: {loss:.4f}")
    
    # Statistics
    print("\n[Statistics]:")
    print(f"  Meta-training epochs: {len(maml.meta_losses)}")
    print(f"  Final meta-loss: {maml.meta_losses[-1]:.4f}")
    print(f"  Meta-loss improvement: {(maml.meta_losses[0] - maml.meta_losses[-1]) / maml.meta_losses[0] * 100:.1f}%")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_meta_learning())
