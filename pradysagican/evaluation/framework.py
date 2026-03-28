"""
PHASE 18: EVALUATION FRAMEWORK
==============================
Production-grade quality, performance, cost, and regression evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EvaluationCase:
    """Single evaluation input + expected characteristics."""

    case_id: str
    prompt: str
    expected_keywords: List[str] = field(default_factory=list)
    max_latency_ms: float = 2500.0
    max_cost_usd: float = 0.05


@dataclass
class EvaluationResult:
    """Result for a single evaluated case."""

    case_id: str
    model_name: str
    output: str
    latency_ms: float
    token_input: int
    token_output: int
    estimated_cost_usd: float
    quality_score: float
    relevance_score: float
    coherence_score: float
    passed: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class BenchmarkReport:
    """Aggregate report across all evaluated cases."""

    model_name: str
    total_cases: int
    passed_cases: int
    pass_rate: float
    avg_latency_ms: float
    avg_cost_usd: float
    avg_quality_score: float
    avg_relevance_score: float
    avg_coherence_score: float
    regressions_detected: int
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class QualityEvaluator:
    """Evaluate output quality, relevance, and coherence."""

    def score_quality(self, output: str, case: EvaluationCase) -> float:
        # Length-normalized quality proxy.
        if not output.strip():
            return 0.0
        base = min(len(output.strip()) / 600.0, 1.0)
        return round(base, 3)

    def score_relevance(self, output: str, case: EvaluationCase) -> float:
        if not case.expected_keywords:
            return 1.0
        text = output.lower()
        hits = sum(1 for k in case.expected_keywords if k.lower() in text)
        return round(hits / len(case.expected_keywords), 3)

    def score_coherence(self, output: str) -> float:
        # Very lightweight coherence proxy.
        sentences = [s.strip() for s in output.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        if not sentences:
            return 0.0
        avg_sentence_len = mean(len(s.split()) for s in sentences)
        # Prefer non-trivial, moderately-sized sentences.
        if avg_sentence_len < 3:
            return 0.4
        if avg_sentence_len > 40:
            return 0.7
        return 0.95


class PerformanceEvaluator:
    """Evaluate latency and throughput-related metrics."""

    def latency_pass(self, latency_ms: float, case: EvaluationCase) -> bool:
        return latency_ms <= case.max_latency_ms


class CostEvaluator:
    """Evaluate token and estimated monetary cost."""

    def __init__(self, input_token_rate: float = 0.000002, output_token_rate: float = 0.000006):
        self.input_token_rate = input_token_rate
        self.output_token_rate = output_token_rate

    def estimate_cost_usd(self, token_input: int, token_output: int) -> float:
        return round(token_input * self.input_token_rate + token_output * self.output_token_rate, 6)

    def cost_pass(self, estimated_cost_usd: float, case: EvaluationCase) -> bool:
        return estimated_cost_usd <= case.max_cost_usd


class RegressionDetector:
    """Detect regressions compared to a baseline report."""

    def detect(self, current: BenchmarkReport, baseline: Optional[BenchmarkReport]) -> int:
        if baseline is None:
            return 0
        regressions = 0
        if current.pass_rate < baseline.pass_rate:
            regressions += 1
        if current.avg_quality_score < baseline.avg_quality_score:
            regressions += 1
        if current.avg_relevance_score < baseline.avg_relevance_score:
            regressions += 1
        if current.avg_coherence_score < baseline.avg_coherence_score:
            regressions += 1
        if current.avg_latency_ms > baseline.avg_latency_ms:
            regressions += 1
        if current.avg_cost_usd > baseline.avg_cost_usd:
            regressions += 1
        return regressions


class DatasetManager:
    """Manage evaluation datasets in memory."""

    def __init__(self) -> None:
        self.datasets: Dict[str, List[EvaluationCase]] = {}

    def register_dataset(self, name: str, cases: List[EvaluationCase]) -> None:
        self.datasets[name] = cases

    def get_dataset(self, name: str) -> List[EvaluationCase]:
        return self.datasets.get(name, [])

    def list_datasets(self) -> List[str]:
        return sorted(self.datasets.keys())


class ABTestRunner:
    """Compare two models side-by-side on the same dataset."""

    def run(self, report_a: BenchmarkReport, report_b: BenchmarkReport) -> Dict[str, Any]:
        return {
            "winner_quality": report_a.model_name
            if report_a.avg_quality_score >= report_b.avg_quality_score
            else report_b.model_name,
            "winner_latency": report_a.model_name
            if report_a.avg_latency_ms <= report_b.avg_latency_ms
            else report_b.model_name,
            "winner_cost": report_a.model_name
            if report_a.avg_cost_usd <= report_b.avg_cost_usd
            else report_b.model_name,
            "delta_pass_rate": round(report_a.pass_rate - report_b.pass_rate, 4),
        }


class ModelComparator:
    """Rank models from benchmark reports."""

    def rank(self, reports: List[BenchmarkReport]) -> List[Tuple[str, float]]:
        # Weighted composite score: pass rate and quality prioritized.
        scored: List[Tuple[str, float]] = []
        for r in reports:
            score = (
                0.35 * r.pass_rate
                + 0.30 * r.avg_quality_score
                + 0.20 * r.avg_relevance_score
                + 0.10 * r.avg_coherence_score
                + 0.03 * max(0.0, 1.0 - min(r.avg_latency_ms / 3000.0, 1.0))
                + 0.02 * max(0.0, 1.0 - min(r.avg_cost_usd / 0.05, 1.0))
            )
            scored.append((r.model_name, round(score, 4)))
        return sorted(scored, key=lambda x: x[1], reverse=True)


class EvaluationFramework:
    """Orchestrates full evaluation lifecycle."""

    def __init__(self) -> None:
        self.quality = QualityEvaluator()
        self.performance = PerformanceEvaluator()
        self.cost = CostEvaluator()
        self.regression = RegressionDetector()
        self.datasets = DatasetManager()
        self.ab = ABTestRunner()
        self.comparator = ModelComparator()

    def evaluate_case(
        self,
        *,
        model_name: str,
        case: EvaluationCase,
        output: str,
        latency_ms: float,
        token_input: int,
        token_output: int,
    ) -> EvaluationResult:
        quality_score = self.quality.score_quality(output, case)
        relevance_score = self.quality.score_relevance(output, case)
        coherence_score = self.quality.score_coherence(output)
        estimated_cost_usd = self.cost.estimate_cost_usd(token_input, token_output)
        passed = (
            relevance_score >= 0.5
            and quality_score >= 0.1
            and coherence_score >= 0.6
            and self.performance.latency_pass(latency_ms, case)
            and self.cost.cost_pass(estimated_cost_usd, case)
        )
        return EvaluationResult(
            case_id=case.case_id,
            model_name=model_name,
            output=output,
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            estimated_cost_usd=estimated_cost_usd,
            quality_score=quality_score,
            relevance_score=relevance_score,
            coherence_score=coherence_score,
            passed=passed,
        )

    def build_report(
        self,
        model_name: str,
        results: List[EvaluationResult],
        baseline: Optional[BenchmarkReport] = None,
    ) -> BenchmarkReport:
        if not results:
            empty = BenchmarkReport(
                model_name=model_name,
                total_cases=0,
                passed_cases=0,
                pass_rate=0.0,
                avg_latency_ms=0.0,
                avg_cost_usd=0.0,
                avg_quality_score=0.0,
                avg_relevance_score=0.0,
                avg_coherence_score=0.0,
                regressions_detected=0,
            )
            empty.regressions_detected = self.regression.detect(empty, baseline)
            return empty

        total_cases = len(results)
        passed_cases = sum(1 for r in results if r.passed)
        report = BenchmarkReport(
            model_name=model_name,
            total_cases=total_cases,
            passed_cases=passed_cases,
            pass_rate=round(passed_cases / total_cases, 4),
            avg_latency_ms=round(mean(r.latency_ms for r in results), 3),
            avg_cost_usd=round(mean(r.estimated_cost_usd for r in results), 6),
            avg_quality_score=round(mean(r.quality_score for r in results), 4),
            avg_relevance_score=round(mean(r.relevance_score for r in results), 4),
            avg_coherence_score=round(mean(r.coherence_score for r in results), 4),
            regressions_detected=0,
        )
        report.regressions_detected = self.regression.detect(report, baseline)
        return report
