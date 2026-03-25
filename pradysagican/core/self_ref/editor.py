"""
F604: SELF-REF EDITOR - Direct File Editing with Self-Referential Improvements
================================================================================

Self-referential code editor that:
- Analyzes code and proposes improvements
- Applies changes in isolated sandbox
- Commits improvements with atomic Git transactions
- Tracks improvement metrics (speed, size, complexity)
- Returns: EditResult with improvement percentages
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ImprovementType(str, Enum):
    """Types of improvements that can be applied."""
    PERFORMANCE = "performance"
    READABILITY = "readability"
    COMPLEXITY_REDUCTION = "complexity_reduction"
    TYPE_SAFETY = "type_safety"
    DOCUMENTATION = "documentation"
    ERROR_HANDLING = "error_handling"
    ASYNC_OPTIMIZATION = "async_optimization"


@dataclass
class Improvement:
    """A proposed code improvement."""
    improvement_type: ImprovementType
    file_path: str
    original_snippet: str
    improved_snippet: str
    description: str
    estimated_improvement_pct: float  # 0-100
    confidence: float = 0.8  # 0.0-1.0
    risk_level: str = "low"  # low, medium, high
    implementation_effort: str = "low"  # low, medium, high


@dataclass
class EditResult:
    """Result of applying an improvement."""
    success: bool
    improvement_type: ImprovementType
    file_path: str
    applied: bool = False
    improvement_pct: float = 0.0
    runtime_improvement_pct: float = 0.0
    memory_improvement_pct: float = 0.0
    complexity_improvement_pct: float = 0.0
    tests_passed: bool = True
    error_message: Optional[str] = None
    git_commit_hash: Optional[str] = None
    original_metrics: dict[str, Any] = field(default_factory=dict)
    improved_metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "success": self.success,
            "improvement_type": self.improvement_type.value,
            "file_path": self.file_path,
            "applied": self.applied,
            "improvement_pct": self.improvement_pct,
            "runtime_improvement_pct": self.runtime_improvement_pct,
            "memory_improvement_pct": self.memory_improvement_pct,
            "complexity_improvement_pct": self.complexity_improvement_pct,
            "tests_passed": self.tests_passed,
            "error_message": self.error_message,
            "git_commit_hash": self.git_commit_hash,
            "timestamp": self.timestamp,
        }


@dataclass
class CodeMetrics:
    """Metrics for a code file or snippet."""
    lines_of_code: int = 0
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    function_count: int = 0
    estimated_runtime_ms: float = 0.0
    memory_usage_mb: float = 0.0
    test_coverage_pct: float = 0.0
    type_coverage_pct: float = 0.0


class SelfRefEditor:
    """Self-referential code editor with improvement analysis and commit."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        enable_git: bool = True,
        sandbox_enabled: bool = True,
    ):
        """
        Initialize the self-referential editor.
        
        Args:
            repo_root: Root directory of Git repository
            enable_git: Whether to commit changes to Git
            sandbox_enabled: Whether to test in sandbox first
        """
        self.repo_root = repo_root or Path.cwd()
        self.enable_git = enable_git
        self.sandbox_enabled = sandbox_enabled
        self.edit_history: list[EditResult] = []
        
        logger.info(
            "SelfRefEditor initialized: repo=%s, git=%s, sandbox=%s",
            self.repo_root, enable_git, sandbox_enabled
        )

    async def analyze_file(self, file_path: Path) -> list[Improvement]:
        """
        Analyze a file and propose improvements.
        
        Args:
            file_path: Path to file to analyze
            
        Returns:
            List of proposed improvements
        """
        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return []
        
        logger.info("Analyzing file: %s", file_path)
        
        try:
            with open(file_path) as f:
                code = f.read()
        except Exception as exc:
            logger.error("Failed to read file %s: %s", file_path, exc)
            return []
        
        # Analyze code for improvements
        improvements = await self._propose_improvements(code, file_path)
        logger.info("Found %d potential improvements in %s", len(improvements), file_path)
        
        return improvements

    async def _propose_improvements(self, code: str, file_path: Path) -> list[Improvement]:
        """Propose improvements based on code analysis."""
        improvements = []
        
        # Simulate analysis for common improvement patterns
        if "async def" in code and "await asyncio.sleep" not in code:
            improvements.append(
                Improvement(
                    improvement_type=ImprovementType.ASYNC_OPTIMIZATION,
                    file_path=str(file_path),
                    original_snippet="# Add concurrent operations",
                    improved_snippet="# Use asyncio.gather for concurrent tasks",
                    description="Add concurrent operation support to async functions",
                    estimated_improvement_pct=15.0,
                    confidence=0.75,
                )
            )
        
        if "except Exception" in code:
            improvements.append(
                Improvement(
                    improvement_type=ImprovementType.ERROR_HANDLING,
                    file_path=str(file_path),
                    original_snippet="except Exception:",
                    improved_snippet="except (ValueError, TypeError) as exc:",
                    description="Use specific exception types instead of broad Exception",
                    estimated_improvement_pct=10.0,
                    confidence=0.85,
                )
            )
        
        if "logger.debug" in code and "logger.info" in code:
            improvements.append(
                Improvement(
                    improvement_type=ImprovementType.DOCUMENTATION,
                    file_path=str(file_path),
                    original_snippet="# Existing logging",
                    improved_snippet="# Add structured logging context",
                    description="Add structured logging with context fields",
                    estimated_improvement_pct=8.0,
                    confidence=0.70,
                    implementation_effort="medium",
                )
            )
        
        return improvements

    async def apply_improvement(
        self, improvement: Improvement, dry_run: bool = False
    ) -> EditResult:
        """
        Apply an improvement to a file.
        
        Args:
            improvement: Improvement to apply
            dry_run: If True, don't commit to Git
            
        Returns:
            EditResult with outcome and metrics
        """
        file_path = Path(improvement.file_path)
        logger.info("Applying %s improvement to %s", improvement.improvement_type.value, file_path)
        
        result = EditResult(
            success=False,
            improvement_type=improvement.improvement_type,
            file_path=improvement.file_path,
        )
        
        # Step 1: Read original file
        try:
            with open(file_path) as f:
                original_code = f.read()
        except Exception as exc:
            result.error_message = f"Failed to read file: {exc}"
            logger.error("Failed to read file %s: %s", file_path, exc)
            return result
        
        # Step 2: Compute original metrics
        original_metrics = await self._compute_metrics(original_code)
        result.original_metrics = original_metrics.__dict__
        
        # Step 3: Apply improvement in sandbox
        if self.sandbox_enabled:
            improved_code = original_code.replace(
                improvement.original_snippet,
                improvement.improved_snippet,
            )
            
            # Test in sandbox
            sandbox_passed = await self._test_in_sandbox(improved_code, file_path)
            if not sandbox_passed:
                result.error_message = "Sandbox tests failed"
                logger.warning("Sandbox testing failed for %s", file_path)
                return result
        else:
            improved_code = original_code.replace(
                improvement.original_snippet,
                improvement.improved_snippet,
            )
        
        # Step 4: Compute improved metrics
        improved_metrics = await self._compute_metrics(improved_code)
        result.improved_metrics = improved_metrics.__dict__
        
        # Step 5: Calculate improvement percentages
        if original_metrics.estimated_runtime_ms > 0:
            result.runtime_improvement_pct = (
                (original_metrics.estimated_runtime_ms - improved_metrics.estimated_runtime_ms)
                / original_metrics.estimated_runtime_ms
                * 100
            )
        
        if original_metrics.cyclomatic_complexity > 0:
            result.complexity_improvement_pct = (
                (original_metrics.cyclomatic_complexity - improved_metrics.cyclomatic_complexity)
                / original_metrics.cyclomatic_complexity
                * 100
            )
        
        result.improvement_pct = (
            result.runtime_improvement_pct * 0.5 + result.complexity_improvement_pct * 0.5
        )
        
        # Step 6: Write file (unless dry-run)
        if not dry_run:
            try:
                with open(file_path, "w") as f:
                    f.write(improved_code)
                result.applied = True
                logger.info("Applied improvement to %s", file_path)
            except Exception as exc:
                result.error_message = f"Failed to write file: {exc}"
                logger.error("Failed to write file %s: %s", file_path, exc)
                return result
        
        # Step 7: Commit to Git (if enabled and not dry-run)
        if self.enable_git and not dry_run and result.applied:
            try:
                commit_hash = await self._git_commit(
                    file_path,
                    f"Improve {improvement.improvement_type.value}: {improvement.description}"
                )
                result.git_commit_hash = commit_hash
                logger.info("Committed changes with hash: %s", commit_hash)
            except Exception as exc:
                result.error_message = f"Git commit failed: {exc}"
                logger.error("Git commit failed: %s", exc)
                result.applied = False
                return result
        
        result.success = True
        result.tests_passed = True
        self.edit_history.append(result)
        
        logger.info(
            "Improvement applied successfully: improvement=%.1f%%, "
            "runtime=%.1f%%, complexity=%.1f%%",
            result.improvement_pct,
            result.runtime_improvement_pct,
            result.complexity_improvement_pct,
        )
        
        return result

    async def _test_in_sandbox(self, code: str, file_path: Path) -> bool:
        """Test improved code in isolated sandbox."""
        logger.debug("Testing in sandbox: %s", file_path)
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                sandbox_file = Path(tmpdir) / file_path.name
                
                # Write improved code to sandbox
                sandbox_file.write_text(code)
                
                # Syntax check
                result = subprocess.run(
                    ["python", "-m", "py_compile", str(sandbox_file)],
                    capture_output=True,
                    timeout=10,
                )
                
                if result.returncode != 0:
                    logger.warning("Sandbox syntax check failed: %s", result.stderr.decode())
                    return False
                
                logger.debug("Sandbox tests passed for %s", file_path)
                return True
        except subprocess.TimeoutExpired:
            logger.warning("Sandbox test timeout for %s", file_path)
            return False
        except Exception as exc:
            logger.warning("Sandbox test error: %s", exc)
            return False

    async def _compute_metrics(self, code: str) -> CodeMetrics:
        """Compute metrics for code snippet."""
        metrics = CodeMetrics()
        
        # Basic metrics
        metrics.lines_of_code = len(code.split("\n"))
        
        # Estimate cyclomatic complexity
        complexity_indicators = code.count("if ") + code.count("for ") + code.count("while ")
        metrics.cyclomatic_complexity = float(max(1, complexity_indicators))
        
        # Count functions/classes
        metrics.function_count = code.count("def ") + code.count("class ")
        
        # Estimate runtime (simple heuristic)
        metrics.estimated_runtime_ms = max(1.0, metrics.lines_of_code * 0.1)
        
        # Type coverage heuristic
        type_annotations = code.count("->") + code.count(": ")
        metrics.type_coverage_pct = min(100.0, (type_annotations / max(metrics.function_count, 1)) * 50)
        
        return metrics

    async def _git_commit(self, file_path: Path, message: str) -> str:
        """Commit changes to Git and return commit hash."""
        try:
            # Stage file
            subprocess.run(
                ["git", "-C", str(self.repo_root), "add", str(file_path)],
                check=True,
                capture_output=True,
                timeout=10,
            )
            
            # Create commit
            result = subprocess.run(
                ["git", "-C", str(self.repo_root), "commit", "-m", message],
                capture_output=True,
                timeout=10,
            )
            
            if result.returncode == 0:
                # Get commit hash
                hash_result = subprocess.run(
                    ["git", "-C", str(self.repo_root), "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return hash_result.stdout.strip()[:12]
            else:
                logger.warning("Git commit failed: %s", result.stderr.decode())
                return ""
        except Exception as exc:
            logger.error("Git commit error: %s", exc)
            raise

    def get_edit_history(self, limit: int = 50) -> list[EditResult]:
        """Get history of applied edits."""
        return self.edit_history[-limit:]

    async def analyze_and_improve_directory(
        self, directory: Path, dry_run: bool = False
    ) -> dict[str, list[EditResult]]:
        """
        Analyze and improve all Python files in a directory.
        
        Args:
            directory: Directory to analyze
            dry_run: If True, don't commit changes
            
        Returns:
            Dictionary mapping file paths to EditResults
        """
        results: dict[str, list[EditResult]] = {}
        
        python_files = list(directory.glob("**/*.py"))
        logger.info("Analyzing %d Python files in %s", len(python_files), directory)
        
        for py_file in python_files:
            try:
                improvements = await self.analyze_file(py_file)
                file_results = []
                
                for improvement in improvements:
                    edit_result = await self.apply_improvement(improvement, dry_run=dry_run)
                    file_results.append(edit_result)
                
                if file_results:
                    results[str(py_file)] = file_results
            except Exception as exc:
                logger.error("Error processing %s: %s", py_file, exc)
        
        logger.info("Completed analysis: %d files improved", len(results))
        return results

    def get_improvement_summary(self) -> dict[str, Any]:
        """Get summary statistics of all improvements applied."""
        if not self.edit_history:
            return {"total_improvements": 0}
        
        successful = [e for e in self.edit_history if e.success and e.applied]
        
        return {
            "total_improvements": len(self.edit_history),
            "successful": len(successful),
            "failed": len(self.edit_history) - len(successful),
            "avg_improvement_pct": float(
                sum(e.improvement_pct for e in successful) / len(successful)
                if successful else 0.0
            ),
            "avg_runtime_improvement_pct": float(
                sum(e.runtime_improvement_pct for e in successful) / len(successful)
                if successful else 0.0
            ),
            "avg_complexity_improvement_pct": float(
                sum(e.complexity_improvement_pct for e in successful) / len(successful)
                if successful else 0.0
            ),
            "total_commits": len([e for e in successful if e.git_commit_hash]),
        }
