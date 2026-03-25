"""
F614: MAE Judge - Quality Assessment & Fitness Evaluation
===========================================================

Evaluate solution quality through:
- Benchmark-based scoring
- Fitness metrics tracking
- Population score updates
- Convergence/diversity balance detection
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Types of benchmarks for evaluation."""
    UNIT_TEST = "unit_test"
    INTEGRATION_TEST = "integration_test"
    PERFORMANCE_TEST = "performance_test"
    SAFETY_TEST = "safety_test"
    REGRESSION_TEST = "regression_test"


@dataclass
class BenchmarkResult:
    """Result of a single benchmark evaluation."""
    benchmark_id: str
    benchmark_type: str
    score: float  # 0.0-1.0
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class FitnessScore:
    """Comprehensive fitness score for a solution."""
    solution_id: str
    overall_fitness: float  # 0.0-1.0
    component_scores: Dict[str, float] = field(default_factory=dict)
    benchmark_results: List[BenchmarkResult] = field(default_factory=list)
    reliability: float = 1.0  # Confidence in score
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    evaluation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_improvement(self, previous: Optional[FitnessScore]) -> bool:
        """Check if this is an improvement over previous score."""
        if previous is None:
            return True
        return self.overall_fitness > previous.overall_fitness

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "evaluation_id": self.evaluation_id,
            "solution_id": self.solution_id,
            "overall_fitness": self.overall_fitness,
            "component_scores": self.component_scores,
            "reliability": self.reliability,
            "num_benchmarks": len(self.benchmark_results),
            "passed_benchmarks": sum(1 for b in self.benchmark_results if b.passed),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PopulationMetrics:
    """Metrics for population fitness distribution."""
    generation: int
    population_size: int
    best_fitness: float
    worst_fitness: float
    avg_fitness: float
    fitness_variance: float
    diversity_index: float
    convergence_rate: float
    stagnation_counter: int = 0
    is_converged: bool = False
    is_diverse: bool = True


class MAEJudge:
    """Multi-Agent Evolution Judge for quality assessment."""

    def __init__(
        self,
        benchmark_timeout_seconds: float = 10.0,
        improvement_threshold: float = 0.02,
    ):
        """Initialize MAE Judge.

        Args:
            benchmark_timeout_seconds: Timeout for each benchmark
            improvement_threshold: Minimum improvement to consider progress
        """
        self.benchmark_timeout = benchmark_timeout_seconds
        self.improvement_threshold = improvement_threshold
        self.fitness_scores: Dict[str, FitnessScore] = {}
        self.benchmark_registry: Dict[str, Callable] = {}
        self.population_metrics_history: List[PopulationMetrics] = []
        self.stagnation_counter = 0
        self.best_fitness_ever = 0.0

    def register_benchmark(
        self,
        benchmark_id: str,
        benchmark_func: Callable,
        benchmark_type: BenchmarkType = BenchmarkType.UNIT_TEST,
        weight: float = 1.0,
    ) -> None:
        """Register a benchmark function.

        Args:
            benchmark_id: Unique benchmark identifier
            benchmark_func: Async function that returns score (0-1)
            benchmark_type: Type of benchmark
            weight: Weight in overall fitness calculation
        """
        self.benchmark_registry[benchmark_id] = {
            "func": benchmark_func,
            "type": benchmark_type.value,
            "weight": weight,
        }
        logger.info(f"Registered benchmark: {benchmark_id}")

    async def evaluate_solution(
        self,
        solution_id: str,
        solution_data: Dict[str, Any],
        benchmarks: Optional[List[str]] = None,
    ) -> FitnessScore:
        """Evaluate solution using registered benchmarks.

        Args:
            solution_id: ID of solution to evaluate
            solution_data: Solution data/implementation
            benchmarks: List of benchmark IDs to run (default: all)

        Returns:
            Fitness score for the solution
        """
        benchmarks_to_run = benchmarks or list(self.benchmark_registry.keys())

        if not benchmarks_to_run:
            return FitnessScore(solution_id=solution_id, overall_fitness=0.5)

        benchmark_results: List[BenchmarkResult] = []
        component_scores: Dict[str, float] = {}
        total_weight = 0.0
        weighted_score = 0.0

        # Run benchmarks in parallel with timeout
        tasks = [
            self._run_benchmark(benchmark_id, solution_data)
            for benchmark_id in benchmarks_to_run
            if benchmark_id in self.benchmark_registry
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for benchmark_id, result in zip(benchmarks_to_run, results):
            if isinstance(result, Exception):
                bench_result = BenchmarkResult(
                    benchmark_id=benchmark_id,
                    benchmark_type="error",
                    score=0.0,
                    passed=False,
                    duration_ms=0,
                    error_message=str(result),
                )
            else:
                bench_result = result

            benchmark_results.append(bench_result)

            # Update component score
            registry_entry = self.benchmark_registry.get(benchmark_id, {})
            weight = registry_entry.get("weight", 1.0)
            component_scores[benchmark_id] = bench_result.score
            weighted_score += bench_result.score * weight
            total_weight += weight

        # Calculate overall fitness
        overall_fitness = (
            weighted_score / total_weight if total_weight > 0 else 0.5
        )

        # Calculate reliability based on consistency
        reliability = self._calculate_reliability(benchmark_results)

        fitness_score = FitnessScore(
            solution_id=solution_id,
            overall_fitness=overall_fitness,
            component_scores=component_scores,
            benchmark_results=benchmark_results,
            reliability=reliability,
        )

        self.fitness_scores[solution_id] = fitness_score
        logger.info(
            f"Evaluated solution {solution_id}: fitness={overall_fitness:.3f}, "
            f"reliability={reliability:.3f}"
        )

        return fitness_score

    async def _run_benchmark(
        self,
        benchmark_id: str,
        solution_data: Dict[str, Any]
    ) -> BenchmarkResult:
        """Run a single benchmark with timeout."""
        registry_entry = self.benchmark_registry.get(benchmark_id, {})
        benchmark_func = registry_entry.get("func")
        benchmark_type = registry_entry.get("type", "unknown")

        if not benchmark_func:
            return BenchmarkResult(
                benchmark_id=benchmark_id,
                benchmark_type=benchmark_type,
                score=0.0,
                passed=False,
                duration_ms=0,
                error_message="Benchmark function not found",
            )

        try:
            start_time = datetime.now(timezone.utc)

            # Run with timeout
            score = await asyncio.wait_for(
                benchmark_func(solution_data),
                timeout=self.benchmark_timeout
            )

            duration_ms = (
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )

            # Ensure score is in [0, 1]
            score = max(0.0, min(1.0, float(score)))

            return BenchmarkResult(
                benchmark_id=benchmark_id,
                benchmark_type=benchmark_type,
                score=score,
                passed=score > 0.5,
                duration_ms=duration_ms,
            )

        except asyncio.TimeoutError:
            return BenchmarkResult(
                benchmark_id=benchmark_id,
                benchmark_type=benchmark_type,
                score=0.0,
                passed=False,
                duration_ms=self.benchmark_timeout * 1000,
                error_message="Benchmark timeout",
            )
        except Exception as e:
            return BenchmarkResult(
                benchmark_id=benchmark_id,
                benchmark_type=benchmark_type,
                score=0.0,
                passed=False,
                duration_ms=0,
                error_message=str(e),
            )

    async def evaluate_population(
        self,
        population: Dict[str, Dict[str, Any]],
        generation: int,
    ) -> PopulationMetrics:
        """Evaluate entire population fitness distribution.

        Args:
            population: Dict mapping solution_id to solution_data
            generation: Current generation number

        Returns:
            Population metrics
        """
        # Evaluate all solutions
        tasks = [
            self.evaluate_solution(sol_id, sol_data)
            for sol_id, sol_data in population.items()
        ]

        fitness_scores = await asyncio.gather(*tasks)
        scores = [fs.overall_fitness for fs in fitness_scores]

        if not scores:
            return PopulationMetrics(
                generation=generation,
                population_size=0,
                best_fitness=0,
                worst_fitness=0,
                avg_fitness=0,
                fitness_variance=0,
                diversity_index=0,
                convergence_rate=0,
            )

        # Calculate metrics
        best_fitness = max(scores)
        worst_fitness = min(scores)
        avg_fitness = sum(scores) / len(scores)

        # Variance as diversity metric
        variance = sum((s - avg_fitness) ** 2 for s in scores) / len(scores)
        diversity_index = min(1.0, variance / (avg_fitness + 1e-6))

        # Convergence rate (inverse diversity)
        convergence_rate = 1.0 - diversity_index

        # Track stagnation
        if best_fitness <= self.best_fitness_ever + self.improvement_threshold:
            self.stagnation_counter += 1
        else:
            self.stagnation_counter = 0
            self.best_fitness_ever = best_fitness

        metrics = PopulationMetrics(
            generation=generation,
            population_size=len(population),
            best_fitness=best_fitness,
            worst_fitness=worst_fitness,
            avg_fitness=avg_fitness,
            fitness_variance=variance,
            diversity_index=diversity_index,
            convergence_rate=convergence_rate,
            stagnation_counter=self.stagnation_counter,
            is_converged=convergence_rate >= 0.95,
            is_diverse=diversity_index >= 0.3,
        )

        self.population_metrics_history.append(metrics)
        logger.info(
            f"Generation {generation}: best={best_fitness:.3f}, "
            f"avg={avg_fitness:.3f}, diversity={diversity_index:.3f}"
        )

        return metrics

    def get_fitness_score(self, solution_id: str) -> Optional[FitnessScore]:
        """Get fitness score for a solution."""
        return self.fitness_scores.get(solution_id)

    def rank_solutions(self, solution_ids: List[str]) -> List[tuple[str, float]]:
        """Rank solutions by fitness score."""
        ranked = [
            (sid, self.fitness_scores.get(sid, FitnessScore(solution_id=sid, overall_fitness=0)).overall_fitness)
            for sid in solution_ids
        ]
        ranked.sort(key=lambda x: x[1], reverse=True)
        return ranked

    def get_population_metrics(self) -> Optional[PopulationMetrics]:
        """Get latest population metrics."""
        return self.population_metrics_history[-1] if self.population_metrics_history else None

    def get_metrics_history(self) -> List[Dict[str, Any]]:
        """Get population metrics history."""
        return [
            {
                "generation": m.generation,
                "best_fitness": m.best_fitness,
                "avg_fitness": m.avg_fitness,
                "diversity": m.diversity_index,
                "convergence": m.convergence_rate,
                "stagnation": m.stagnation_counter,
            }
            for m in self.population_metrics_history
        ]

    def _calculate_reliability(self, benchmark_results: List[BenchmarkResult]) -> float:
        """Calculate reliability score based on benchmark consistency."""
        if not benchmark_results:
            return 0.0

        # Count passed/failed
        passed = sum(1 for b in benchmark_results if b.passed)
        total = len(benchmark_results)

        # Reliability increases with pass rate
        pass_rate = passed / total if total > 0 else 0.0

        # Also consider error-free execution
        errors = sum(1 for b in benchmark_results if b.error_message)
        error_rate = errors / total if total > 0 else 0.0

        reliability = pass_rate * (1.0 - 0.5 * error_rate)
        return min(1.0, max(0.0, reliability))
