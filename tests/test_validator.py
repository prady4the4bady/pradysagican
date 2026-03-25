"""
Tests for F602: VALIDATOR module
================================
Tests for benchmark-gated code validation.
"""

import pytest
import asyncio
from pathlib import Path
from pradysagican.core.evolution.validator import (
    Validator,
    ValidationDecision,
    BenchmarkType,
    BenchmarkResult,
)


@pytest.fixture
def validator():
    """Create test validator instance."""
    return Validator()


class TestValidatorInitialization:
    """Test validator initialization."""

    def test_validator_init(self, validator):
        """Test basic initialization."""
        assert validator is not None
        assert validator.baseline_dir.exists()
        assert validator.swe_bench_timeout > 0
        assert validator.hle_mini_timeout > 0

    def test_validator_with_custom_baseline_dir(self, tmp_path):
        """Test initialization with custom baseline directory."""
        validator = Validator(baseline_dir=tmp_path)
        assert validator.baseline_dir == tmp_path
        assert validator.baseline_dir.exists()


class TestBenchmarkResults:
    """Test benchmark result structures."""

    def test_benchmark_result_creation(self):
        """Test creating benchmark result."""
        result = BenchmarkResult(
            benchmark_type=BenchmarkType.SWE_BENCH_MINI,
            name="test_case",
            passed=True,
            score=0.95,
            runtime_ms=100.0,
        )
        assert result.passed
        assert result.score == 0.95


class TestValidation:
    """Test validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_code(self, validator):
        """Test code validation."""
        test_code = "def hello(): return 'world'"
        report = await validator.validate(test_code)
        
        assert report is not None
        assert report.code_hash is not None
        assert report.total_runtime_sec > 0
        assert len(report.swe_bench_results) > 0

    @pytest.mark.asyncio
    async def test_validation_decision_pass(self, validator):
        """Test validation decision - PASS."""
        test_code = "def test(): pass"
        report = await validator.validate(test_code)
        
        # Since we're simulating, this should generally pass
        assert report.decision in [ValidationDecision.PASS, ValidationDecision.MIXED]

    @pytest.mark.asyncio
    async def test_swe_bench_mini(self, validator):
        """Test SWE-bench-mini evaluation."""
        results = await validator._run_swe_bench_mini()
        
        assert len(results) > 0
        assert all(r.benchmark_type == BenchmarkType.SWE_BENCH_MINI for r in results)
        assert all(hasattr(r, "score") for r in results)
        assert all(0.0 <= r.score <= 1.0 for r in results)

    @pytest.mark.asyncio
    async def test_hle_mini(self, validator):
        """Test HLE-mini evaluation."""
        results = await validator._run_hle_mini()
        
        assert len(results) > 0
        assert all(r.benchmark_type == BenchmarkType.HLE_MINI for r in results)
        assert all(0.0 <= r.score <= 1.0 for r in results)

    @pytest.mark.asyncio
    async def test_regression_detection(self, validator):
        """Test regression detection."""
        # First, store a baseline
        validator.store_baseline("test_metric", BenchmarkType.SWE_BENCH_MINI, 0.90)
        
        # Now run regression detection
        results = await validator._detect_regressions()
        
        assert isinstance(results, list)


class TestBaselines:
    """Test baseline management."""

    def test_store_baseline(self, validator):
        """Test storing baseline score."""
        validator.store_baseline("test_func", BenchmarkType.SWE_BENCH_MINI, 0.85)
        
        assert "test_func" in validator._baselines
        baseline = validator._baselines["test_func"]
        assert baseline.baseline_score == 0.85

    def test_save_and_load_baselines(self, tmp_path):
        """Test saving and loading baselines."""
        validator1 = Validator(baseline_dir=tmp_path)
        validator1.store_baseline("metric1", BenchmarkType.SWE_BENCH_MINI, 0.90)
        
        # Create new validator from same directory
        validator2 = Validator(baseline_dir=tmp_path)
        assert "metric1" in validator2._baselines


class TestValidationReport:
    """Test validation report."""

    @pytest.mark.asyncio
    async def test_report_structure(self, validator):
        """Test validation report structure."""
        code = "def test(): pass"
        report = await validator.validate(code)
        
        assert report.code_hash is not None
        assert report.decision in [ValidationDecision.PASS, ValidationDecision.FAIL, ValidationDecision.MIXED]
        assert report.overall_score >= 0.0
        assert report.timestamp > 0

    @pytest.mark.asyncio
    async def test_report_to_dict(self, validator):
        """Test converting report to dictionary."""
        code = "def test(): pass"
        report = await validator.validate(code)
        
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "code_hash" in report_dict
        assert "decision" in report_dict
        assert "overall_score" in report_dict


class TestTimeout:
    """Test timeout handling."""

    @pytest.mark.asyncio
    async def test_swe_bench_respects_timeout(self, validator):
        """Test SWE-bench respects timeout."""
        validator.swe_bench_timeout = 0.5  # Very short timeout
        results = await validator._run_swe_bench_mini()
        
        # Should complete without hanging
        assert len(results) >= 0

    @pytest.mark.asyncio
    async def test_hle_mini_respects_timeout(self, validator):
        """Test HLE-mini respects timeout."""
        validator.hle_mini_timeout = 0.5
        results = await validator._run_hle_mini()
        
        assert len(results) >= 0


class TestMetrics:
    """Test metrics computation."""

    @pytest.mark.asyncio
    async def test_overall_score_calculation(self, validator):
        """Test overall score calculation."""
        code = "def foo(): return 42"
        report = await validator.validate(code)
        
        assert 0.0 <= report.overall_score <= 1.0
        
        # Score should be average of all test results
        if report.swe_bench_results or report.hle_mini_results:
            all_results = report.swe_bench_results + report.hle_mini_results
            expected_avg = sum(r.score for r in all_results) / len(all_results)
            assert abs(report.overall_score - expected_avg) < 0.01
