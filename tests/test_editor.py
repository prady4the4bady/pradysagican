"""
Tests for F604: SELF-REF EDITOR module
======================================
Tests for self-referential code editing.
"""

import pytest
import asyncio
from pathlib import Path
from pradysagican.core.self_ref.editor import (
    SelfRefEditor,
    EditResult,
    Improvement,
    ImprovementType,
    CodeMetrics,
)


@pytest.fixture
def editor(tmp_path):
    """Create test editor instance."""
    return SelfRefEditor(repo_root=tmp_path, enable_git=False)


@pytest.fixture
def sample_code():
    """Sample Python code for testing."""
    return """
import asyncio

async def process_data():
    try:
        for item in items:
            await asyncio.sleep(0.1)
    except Exception as exc:
        print(f"Error: {exc}")
"""


class TestEditorInitialization:
    """Test editor initialization."""

    def test_editor_init(self, tmp_path):
        """Test basic initialization."""
        editor = SelfRefEditor(repo_root=tmp_path)
        assert editor.repo_root == tmp_path
        assert editor.enable_git is True
        assert editor.sandbox_enabled is True

    def test_editor_git_disabled(self, tmp_path):
        """Test initialization with Git disabled."""
        editor = SelfRefEditor(repo_root=tmp_path, enable_git=False)
        assert editor.enable_git is False


class TestAnalysis:
    """Test code analysis."""

    @pytest.mark.asyncio
    async def test_analyze_file(self, editor, tmp_path, sample_code):
        """Test file analysis."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_code)
        
        improvements = await editor.analyze_file(test_file)
        assert isinstance(improvements, list)
        # Should find some improvements
        assert len(improvements) > 0

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self, editor, tmp_path):
        """Test analyzing non-existent file."""
        nonexistent = tmp_path / "nonexistent.py"
        improvements = await editor.analyze_file(nonexistent)
        
        assert improvements == []

    @pytest.mark.asyncio
    async def test_improvement_types(self, editor, sample_code):
        """Test that different improvement types are identified."""
        improvements = await editor._propose_improvements(sample_code, Path("test.py"))
        
        types = [i.improvement_type for i in improvements]
        assert len(types) > 0
        assert all(isinstance(t, ImprovementType) for t in types)


class TestImprovement:
    """Test improvement application."""

    def test_improvement_creation(self):
        """Test creating improvement object."""
        improvement = Improvement(
            improvement_type=ImprovementType.ERROR_HANDLING,
            file_path="test.py",
            original_snippet="except Exception:",
            improved_snippet="except ValueError:",
            description="Use specific exception",
            estimated_improvement_pct=10.0,
        )
        assert improvement.file_path == "test.py"
        assert improvement.confidence == 0.8

    @pytest.mark.asyncio
    async def test_apply_improvement_dry_run(self, editor, tmp_path, sample_code):
        """Test applying improvement in dry-run mode."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_code)
        
        improvement = Improvement(
            improvement_type=ImprovementType.ERROR_HANDLING,
            file_path=str(test_file),
            original_snippet="except Exception:",
            improved_snippet="except Exception as exc:",
            description="Capture exception",
            estimated_improvement_pct=5.0,
        )
        
        result = await editor.apply_improvement(improvement, dry_run=True)
        assert result.success
        assert result.applied is False  # Dry run should not apply

    @pytest.mark.asyncio
    async def test_improvement_result_structure(self, editor, tmp_path, sample_code):
        """Test EditResult structure."""
        test_file = tmp_path / "test.py"
        test_file.write_text(sample_code)
        
        improvement = Improvement(
            improvement_type=ImprovementType.READABILITY,
            file_path=str(test_file),
            original_snippet="print(f\"Error: {exc}\")",
            improved_snippet="logger.error(\"Error: %s\", exc)",
            description="Use logging instead of print",
            estimated_improvement_pct=15.0,
        )
        
        result = await editor.apply_improvement(improvement, dry_run=True)
        
        assert isinstance(result, EditResult)
        assert result.improvement_type == ImprovementType.READABILITY
        assert result.file_path == str(test_file)
        assert isinstance(result.original_metrics, dict)
        assert isinstance(result.improved_metrics, dict)


class TestMetrics:
    """Test code metrics computation."""

    @pytest.mark.asyncio
    async def test_compute_metrics(self, editor):
        """Test computing code metrics."""
        code = """
def add(a, b):
    if a > 0:
        return a + b
    else:
        return b
"""
        metrics = await editor._compute_metrics(code)
        
        assert isinstance(metrics, CodeMetrics)
        assert metrics.lines_of_code > 0
        assert metrics.cyclomatic_complexity >= 1.0
        assert metrics.function_count >= 1
        assert 0 <= metrics.test_coverage_pct <= 100

    @pytest.mark.asyncio
    async def test_metrics_improvement(self, editor):
        """Test metrics show improvement."""
        original = "x = 1\ny = 2\nif x > 0:\n    z = x + y"
        improved = "x = 1\ny = 2\nz = x + y"
        
        original_metrics = await editor._compute_metrics(original)
        improved_metrics = await editor._compute_metrics(improved)
        
        assert improved_metrics.cyclomatic_complexity <= original_metrics.cyclomatic_complexity


class TestSandbox:
    """Test sandbox testing."""

    @pytest.mark.asyncio
    async def test_sandbox_valid_code(self, editor, tmp_path):
        """Test sandbox with valid code."""
        valid_code = "def test():\n    return 42"
        result = await editor._test_in_sandbox(valid_code, tmp_path / "test.py")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_sandbox_invalid_code(self, editor, tmp_path):
        """Test sandbox with invalid code."""
        invalid_code = "def test(\n    invalid syntax"
        result = await editor._test_in_sandbox(invalid_code, tmp_path / "test.py")
        
        assert result is False


class TestHistory:
    """Test edit history tracking."""

    @pytest.mark.asyncio
    async def test_edit_history(self, editor):
        """Test edit history is tracked."""
        assert len(editor.edit_history) == 0
        
        # History is populated when improvements are applied
        # (checked in other tests)

    def test_get_edit_history(self, editor):
        """Test retrieving edit history."""
        history = editor.get_edit_history(limit=10)
        assert isinstance(history, list)


class TestImprovementSummary:
    """Test improvement summary."""

    def test_empty_summary(self, editor):
        """Test summary with no improvements."""
        summary = editor.get_improvement_summary()
        
        assert summary["total_improvements"] == 0
        assert "successful" in summary or summary["total_improvements"] == 0

    def test_summary_structure(self, editor):
        """Test summary structure."""
        summary = editor.get_improvement_summary()
        
        assert isinstance(summary, dict)
        assert "total_improvements" in summary
        if summary["total_improvements"] > 0:
            assert "successful" in summary
            assert "failed" in summary


class TestCodeMetrics:
    """Test CodeMetrics data structure."""

    def test_metrics_initialization(self):
        """Test CodeMetrics initialization."""
        metrics = CodeMetrics()
        
        assert metrics.lines_of_code == 0
        assert metrics.cyclomatic_complexity == 0.0
        assert metrics.cognitive_complexity == 0.0

    def test_metrics_with_values(self):
        """Test CodeMetrics with values."""
        metrics = CodeMetrics(
            lines_of_code=100,
            cyclomatic_complexity=5.0,
            function_count=10,
        )
        
        assert metrics.lines_of_code == 100
        assert metrics.cyclomatic_complexity == 5.0
        assert metrics.function_count == 10
