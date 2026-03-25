"""
F620: Fitness Tracker - Performance Analysis & Prediction
==========================================================

Track and analyze fitness trends:
- Historical performance metrics
- Trend detection and extrapolation
- Performance prediction
- Convergence analysis
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import uuid

logger = logging.getLogger(__name__)


@dataclass
class FitnessReading:
    """Single fitness measurement."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    generation: int = 0
    agent_id: str = ""
    fitness_value: float = 0.0
    novelty_value: float = 0.0
    population_size: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "generation": self.generation,
            "agent_id": self.agent_id,
            "fitness": self.fitness_value,
            "novelty": self.novelty_value,
            "population_size": self.population_size,
        }


class TrendAnalysis:
    """Analyzes fitness trends over time."""

    def __init__(self, window_size: int = 10):
        """Initialize trend analyzer.

        Args:
            window_size: Window size for trend calculation
        """
        self.window_size = window_size
        self.readings: List[FitnessReading] = []
        self.trend_points: List[Tuple[int, float]] = []

    def add_reading(self, reading: FitnessReading) -> None:
        """Add fitness reading.

        Args:
            reading: Fitness measurement to add
        """
        self.readings.append(reading)
        self._update_trend()

    def _update_trend(self) -> None:
        """Update trend analysis."""
        if len(self.readings) < 2:
            return

        # Linear regression on last window
        recent = self.readings[-self.window_size:]
        values = [r.fitness_value for r in recent]
        
        if len(values) < 2:
            return

        n = len(values)
        x_mean = n / 2
        y_mean = sum(values) / n
        
        numerator = sum(
            (i - x_mean) * (values[i] - y_mean)
            for i in range(n)
        )
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0.0
        else:
            slope = numerator / denominator

        self.trend_points.append((len(self.readings), slope))

    def get_trend_direction(self) -> str:
        """Get overall trend direction.

        Returns:
            "improving", "stable", or "declining"
        """
        if not self.readings or len(self.readings) < 5:
            return "stable"

        recent_values = [r.fitness_value for r in self.readings[-10:]]
        change = recent_values[-1] - recent_values[0]

        if change > 0.05:
            return "improving"
        elif change < -0.05:
            return "declining"
        else:
            return "stable"

    def get_trend_velocity(self) -> float:
        """Get trend velocity (fitness change per generation).

        Returns:
            Velocity (fitness units per generation)
        """
        if len(self.readings) < 2:
            return 0.0

        recent = self.readings[-self.window_size:]
        if len(recent) < 2:
            return 0.0

        first_fitness = recent[0].fitness_value
        last_fitness = recent[-1].fitness_value
        generations = recent[-1].generation - recent[0].generation

        if generations == 0:
            return 0.0

        return (last_fitness - first_fitness) / generations

    def get_acceleration(self) -> float:
        """Get trend acceleration (second derivative).

        Returns:
            Acceleration value
        """
        if len(self.readings) < 5:
            return 0.0

        # Split readings into two halves
        mid = len(self.readings) // 2
        first_half = self.readings[:mid]
        second_half = self.readings[mid:]

        vel1 = self._compute_velocity(first_half)
        vel2 = self._compute_velocity(second_half)

        if vel1 == 0:
            return 0.0

        return (vel2 - vel1) / vel1

    def _compute_velocity(self, readings: List[FitnessReading]) -> float:
        """Compute velocity for a set of readings."""
        if len(readings) < 2:
            return 0.0

        first_fitness = readings[0].fitness_value
        last_fitness = readings[-1].fitness_value
        generations = readings[-1].generation - readings[0].generation

        if generations == 0:
            return 0.0

        return (last_fitness - first_fitness) / generations

    def predict_future_fitness(self, generations_ahead: int = 10) -> float:
        """Predict future fitness based on trend.

        Args:
            generations_ahead: Number of generations to predict ahead

        Returns:
            Predicted fitness value
        """
        if not self.readings:
            return 0.0

        velocity = self.get_trend_velocity()
        acceleration = self.get_acceleration()

        current_fitness = self.readings[-1].fitness_value

        # Simple kinematic prediction with acceleration
        predicted = (
            current_fitness +
            velocity * generations_ahead +
            0.5 * acceleration * (generations_ahead ** 2)
        )

        # Bound prediction to [0, 1]
        return max(0.0, min(1.0, predicted))

    def get_convergence_rate(self) -> float:
        """Estimate rate of convergence.

        Returns:
            Convergence rate (0.0-1.0)
        """
        if len(self.readings) < 5:
            return 0.0

        recent = self.readings[-self.window_size:]
        if len(recent) < 2:
            return 0.0

        # High convergence = low velocity and low variance
        velocity = abs(self.get_trend_velocity())
        variance = statistics.variance([r.fitness_value for r in recent]) if len(recent) > 1 else 0.0

        # Normalize to 0-1
        convergence = 1.0 - min(1.0, velocity + variance)
        return convergence


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics."""
    best_fitness: float = 0.0
    worst_fitness: float = 1.0
    average_fitness: float = 0.5
    fitness_std_dev: float = 0.0
    best_novelty: float = 0.0
    average_novelty: float = 0.0
    population_mean: float = 0.0
    population_std_dev: float = 0.0
    diversity_index: float = 0.0
    convergence_index: float = 0.0
    generation: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "best_fitness": round(self.best_fitness, 4),
            "worst_fitness": round(self.worst_fitness, 4),
            "average_fitness": round(self.average_fitness, 4),
            "std_dev": round(self.fitness_std_dev, 4),
            "best_novelty": round(self.best_novelty, 4),
            "average_novelty": round(self.average_novelty, 4),
            "diversity_index": round(self.diversity_index, 4),
            "convergence_index": round(self.convergence_index, 4),
            "generation": self.generation,
        }


class FitnessHistory:
    """Maintains historical fitness data."""

    def __init__(self, max_history: int = 1000):
        """Initialize fitness history.

        Args:
            max_history: Maximum readings to retain
        """
        self.max_history = max_history
        self.history: List[FitnessReading] = []
        self.per_agent_history: Dict[str, List[FitnessReading]] = {}
        self.per_generation_metrics: Dict[int, PerformanceMetrics] = {}
        self.trend_analysis = TrendAnalysis()

    def record_reading(
        self,
        generation: int,
        agent_id: str,
        fitness: float,
        novelty: float,
        population_size: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a fitness reading.

        Args:
            generation: Generation number
            agent_id: Agent identifier
            fitness: Fitness value
            novelty: Novelty value
            population_size: Current population size
            metadata: Additional metadata
        """
        reading = FitnessReading(
            generation=generation,
            agent_id=agent_id,
            fitness_value=fitness,
            novelty_value=novelty,
            population_size=population_size,
            metadata=metadata or {},
        )

        # Add to history
        self.history.append(reading)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Add to per-agent history
        if agent_id not in self.per_agent_history:
            self.per_agent_history[agent_id] = []
        self.per_agent_history[agent_id].append(reading)

        # Add to trend analysis
        self.trend_analysis.add_reading(reading)

    def compute_generation_metrics(self, generation: int) -> PerformanceMetrics:
        """Compute metrics for a generation.

        Args:
            generation: Generation number

        Returns:
            Performance metrics
        """
        # Get readings for this generation
        gen_readings = [r for r in self.history if r.generation == generation]

        if not gen_readings:
            return PerformanceMetrics(generation=generation)

        fitness_values = [r.fitness_value for r in gen_readings]
        novelty_values = [r.novelty_value for r in gen_readings]

        # Compute metrics
        metrics = PerformanceMetrics(
            best_fitness=max(fitness_values),
            worst_fitness=min(fitness_values),
            average_fitness=sum(fitness_values) / len(fitness_values),
            fitness_std_dev=(
                statistics.stdev(fitness_values) if len(fitness_values) > 1 else 0.0
            ),
            best_novelty=max(novelty_values),
            average_novelty=sum(novelty_values) / len(novelty_values),
            population_mean=sum(r.population_size for r in gen_readings) / len(gen_readings),
            diversity_index=statistics.stdev(fitness_values) if len(fitness_values) > 1 else 0.0,
            convergence_index=self.trend_analysis.get_convergence_rate(),
            generation=generation,
        )

        self.per_generation_metrics[generation] = metrics
        return metrics

    def get_agent_progression(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get fitness progression for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            List of readings sorted by generation
        """
        if agent_id not in self.per_agent_history:
            return []

        readings = self.per_agent_history[agent_id]
        sorted_readings = sorted(readings, key=lambda r: r.generation)
        return [r.to_dict() for r in sorted_readings]

    def get_generational_progression(self) -> List[Dict[str, Any]]:
        """Get metrics progression by generation.

        Returns:
            List of generation metrics sorted by generation
        """
        gen_numbers = sorted(self.per_generation_metrics.keys())
        return [
            self.per_generation_metrics[gen].to_dict()
            for gen in gen_numbers
        ]

    def get_recent_trend(self, num_generations: int = 20) -> Dict[str, Any]:
        """Get recent trend information.

        Args:
            num_generations: Number of recent generations to analyze

        Returns:
            Trend information
        """
        if not self.history:
            return {"trend": "no_data"}

        recent_readings = self.history[-num_generations * 10:]
        if not recent_readings:
            recent_readings = self.history

        return {
            "trend_direction": self.trend_analysis.get_trend_direction(),
            "trend_velocity": round(self.trend_analysis.get_trend_velocity(), 4),
            "acceleration": round(self.trend_analysis.get_acceleration(), 4),
            "convergence_rate": round(self.trend_analysis.get_convergence_rate(), 4),
            "predicted_fitness_in_10": round(
                self.trend_analysis.predict_future_fitness(10), 4
            ),
            "recent_readings_count": len(recent_readings),
        }

    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get overall performance statistics.

        Returns:
            Performance statistics
        """
        if not self.history:
            return {"status": "no_data"}

        all_fitness = [r.fitness_value for r in self.history]
        all_novelty = [r.novelty_value for r in self.history]

        return {
            "total_readings": len(self.history),
            "unique_agents": len(self.per_agent_history),
            "max_fitness": max(all_fitness),
            "min_fitness": min(all_fitness),
            "avg_fitness": sum(all_fitness) / len(all_fitness),
            "max_novelty": max(all_novelty),
            "avg_novelty": sum(all_novelty) / len(all_novelty),
            "generations_tracked": len(self.per_generation_metrics),
        }

    def export_history(self) -> List[Dict[str, Any]]:
        """Export complete history.

        Returns:
            List of all readings as dictionaries
        """
        return [r.to_dict() for r in self.history]

    def clear_history(self) -> None:
        """Clear all history."""
        self.history.clear()
        self.per_agent_history.clear()
        self.per_generation_metrics.clear()
        self.trend_analysis = TrendAnalysis()
        logger.debug("Fitness history cleared")
