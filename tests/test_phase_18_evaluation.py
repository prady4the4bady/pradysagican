"""PHASE 18 tests: evaluation framework."""

from pradysagican.evaluation.framework import (
    ABTestRunner,
    BenchmarkReport,
    DatasetManager,
    EvaluationCase,
    EvaluationFramework,
    ModelComparator,
    RegressionDetector,
)


def _sample_case(case_id: str = "c1") -> EvaluationCase:
    return EvaluationCase(
        case_id=case_id,
        prompt="Explain retrieval-augmented generation in practical terms.",
        expected_keywords=["retrieval", "generation", "context"],
        max_latency_ms=2000.0,
        max_cost_usd=0.02,
    )


def test_dataset_manager_register_and_list() -> None:
    manager = DatasetManager()
    manager.register_dataset("core", [_sample_case("c1"), _sample_case("c2")])
    assert manager.list_datasets() == ["core"]
    assert len(manager.get_dataset("core")) == 2


def test_evaluate_case_pass() -> None:
    framework = EvaluationFramework()
    case = _sample_case()
    result = framework.evaluate_case(
        model_name="gpt-5.3-codex",
        case=case,
        output="Use retrieval to fetch context, then generation to answer with grounded context.",
        latency_ms=550.0,
        token_input=120,
        token_output=180,
    )
    assert result.passed is True
    assert result.relevance_score >= 0.66
    assert result.estimated_cost_usd > 0


def test_evaluate_case_fail_latency() -> None:
    framework = EvaluationFramework()
    case = _sample_case()
    result = framework.evaluate_case(
        model_name="slow-model",
        case=case,
        output="retrieval generation context",
        latency_ms=2600.0,
        token_input=90,
        token_output=90,
    )
    assert result.passed is False
    assert result.latency_ms > case.max_latency_ms


def test_build_report_and_regression_detection() -> None:
    framework = EvaluationFramework()
    case = _sample_case()

    current_results = [
        framework.evaluate_case(
            model_name="model-a",
            case=case,
            output="retrieval generation context with practical grounding",
            latency_ms=700.0,
            token_input=150,
            token_output=200,
        ),
        framework.evaluate_case(
            model_name="model-a",
            case=case,
            output="retrieval + generation pipeline with context-aware output.",
            latency_ms=850.0,
            token_input=140,
            token_output=210,
        ),
    ]

    baseline = BenchmarkReport(
        model_name="model-a",
        total_cases=2,
        passed_cases=2,
        pass_rate=1.0,
        avg_latency_ms=500.0,
        avg_cost_usd=0.0012,
        avg_quality_score=0.95,
        avg_relevance_score=0.95,
        avg_coherence_score=0.95,
        regressions_detected=0,
    )

    report = framework.build_report("model-a", current_results, baseline=baseline)
    assert report.total_cases == 2
    assert 0 <= report.pass_rate <= 1
    assert report.regressions_detected >= 0


def test_ab_runner_outputs_winners() -> None:
    runner = ABTestRunner()
    a = BenchmarkReport(
        model_name="model-a",
        total_cases=10,
        passed_cases=9,
        pass_rate=0.9,
        avg_latency_ms=900.0,
        avg_cost_usd=0.01,
        avg_quality_score=0.88,
        avg_relevance_score=0.9,
        avg_coherence_score=0.92,
        regressions_detected=0,
    )
    b = BenchmarkReport(
        model_name="model-b",
        total_cases=10,
        passed_cases=8,
        pass_rate=0.8,
        avg_latency_ms=700.0,
        avg_cost_usd=0.015,
        avg_quality_score=0.82,
        avg_relevance_score=0.84,
        avg_coherence_score=0.86,
        regressions_detected=0,
    )
    result = runner.run(a, b)
    assert result["winner_quality"] == "model-a"
    assert result["winner_latency"] == "model-b"
    assert result["winner_cost"] == "model-a"


def test_model_comparator_ranking() -> None:
    comparator = ModelComparator()
    reports = [
        BenchmarkReport(
            model_name="x",
            total_cases=10,
            passed_cases=8,
            pass_rate=0.8,
            avg_latency_ms=900.0,
            avg_cost_usd=0.012,
            avg_quality_score=0.85,
            avg_relevance_score=0.82,
            avg_coherence_score=0.83,
            regressions_detected=0,
        ),
        BenchmarkReport(
            model_name="y",
            total_cases=10,
            passed_cases=9,
            pass_rate=0.9,
            avg_latency_ms=850.0,
            avg_cost_usd=0.011,
            avg_quality_score=0.9,
            avg_relevance_score=0.9,
            avg_coherence_score=0.88,
            regressions_detected=0,
        ),
    ]
    ranked = comparator.rank(reports)
    assert ranked[0][0] == "y"
    assert ranked[0][1] >= ranked[1][1]


def test_regression_detector_none_baseline() -> None:
    detector = RegressionDetector()
    current = BenchmarkReport(
        model_name="m",
        total_cases=1,
        passed_cases=1,
        pass_rate=1.0,
        avg_latency_ms=100.0,
        avg_cost_usd=0.001,
        avg_quality_score=0.9,
        avg_relevance_score=0.9,
        avg_coherence_score=0.9,
        regressions_detected=0,
    )
    assert detector.detect(current, None) == 0
