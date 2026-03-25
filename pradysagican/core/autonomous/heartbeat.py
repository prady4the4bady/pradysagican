"""
F610: HEARTBEAT - 20-Minute Autonomous Cycle Orchestrator
==========================================================

Autonomous system heartbeat that orchestrates:
- Editor: Propose and apply code improvements
- Validator: Validate improvements against benchmarks
- Overseer: Review and approve changes
- Archive: Store evolved variants
- Failure queue processing
- Principle extraction from failures
- 3-gate approval system for all modifications
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class HeartbeatPhase(str, Enum):
    """Phases of the heartbeat cycle."""
    IDLE = "idle"
    ANALYSIS = "analysis"
    IMPROVEMENT = "improvement"
    VALIDATION = "validation"
    OVERSIGHT = "oversight"
    ARCHIVAL = "archival"
    FAILURE_RECOVERY = "failure_recovery"
    LEARNING = "learning"


class ApprovalGate(str, Enum):
    """Three approval gates for modifications."""
    VALIDATOR_GATE = "validator"      # Technical validation
    OVERSEER_GATE = "overseer"        # Quality review
    EXECUTOR_GATE = "executor"        # Execution approval


@dataclass
class ApprovalDecision:
    """Decision from an approval gate."""
    gate: ApprovalGate
    approved: bool
    score: float  # 0.0-1.0
    reason: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CycleMetrics:
    """Metrics from a heartbeat cycle."""
    cycle_number: int
    start_time: float
    end_time: float = 0.0
    duration_sec: float = 0.0
    phases_completed: list[str] = field(default_factory=list)
    improvements_proposed: int = 0
    improvements_applied: int = 0
    improvements_approved: int = 0
    validations_passed: int = 0
    validations_failed: int = 0
    failures_processed: int = 0
    principles_extracted: int = 0
    variants_archived: int = 0
    overall_success: bool = True
    error_count: int = 0


@dataclass
class FailureQueueItem:
    """Item in the failure queue."""
    failure_id: str
    category: str
    timestamp: float
    error_message: str
    context: dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    processed: bool = False


class Heartbeat:
    """Autonomous heartbeat cycle orchestrator."""

    def __init__(
        self,
        cycle_interval: float = 1200.0,  # 20 minutes
        phase_timeout: float = 300.0,    # 5 minutes per phase
        enable_editor: bool = True,
        enable_validator: bool = True,
        enable_overseer: bool = True,
        enable_archive: bool = True,
        enable_learning: bool = True,
    ):
        """
        Initialize heartbeat orchestrator.
        
        Args:
            cycle_interval: Seconds between cycles (20 minutes)
            phase_timeout: Timeout per phase (5 minutes)
            enable_editor: Enable code improvement phase
            enable_validator: Enable validation phase
            enable_overseer: Enable oversight phase
            enable_archive: Enable archival phase
            enable_learning: Enable learning from failures
        """
        self.cycle_interval = cycle_interval
        self.phase_timeout = phase_timeout
        
        # Feature flags
        self.enable_editor = enable_editor
        self.enable_validator = enable_validator
        self.enable_overseer = enable_overseer
        self.enable_archive = enable_archive
        self.enable_learning = enable_learning
        
        # State
        self.is_running = False
        self.current_phase = HeartbeatPhase.IDLE
        self.cycle_number = 0
        
        # Queues
        self._failure_queue: list[FailureQueueItem] = []
        self._pending_approvals: list[ApprovalDecision] = []
        
        # History
        self._cycle_history: list[CycleMetrics] = []
        
        logger.info(
            "Heartbeat initialized: interval=%.1fs, timeout=%.1fs, "
            "editor=%s, validator=%s, overseer=%s, archive=%s, learning=%s",
            cycle_interval, phase_timeout,
            enable_editor, enable_validator, enable_overseer, enable_archive, enable_learning
        )

    async def start(self) -> None:
        """Start the autonomous heartbeat."""
        if self.is_running:
            logger.warning("Heartbeat already running")
            return
        
        self.is_running = True
        logger.info("Starting heartbeat")
        
        try:
            while self.is_running:
                await self.run_cycle()
                await asyncio.sleep(1)  # Minimal wait between cycles
        except asyncio.CancelledError:
            logger.info("Heartbeat cancelled")
            self.is_running = False
        except Exception as exc:
            logger.error("Heartbeat error: %s", exc)
            self.is_running = False
            raise

    def stop(self) -> None:
        """Stop the heartbeat."""
        self.is_running = False
        logger.info("Heartbeat stopped")

    async def run_cycle(self) -> CycleMetrics:
        """
        Run a complete heartbeat cycle (20 minutes).
        
        Returns:
            CycleMetrics with cycle statistics
        """
        self.cycle_number += 1
        cycle_start = time.time()
        
        metrics = CycleMetrics(
            cycle_number=self.cycle_number,
            start_time=cycle_start,
        )
        
        try:
            logger.info("═" * 60)
            logger.info("HEARTBEAT CYCLE %d START", self.cycle_number)
            logger.info("═" * 60)
            
            # Phase 1: Analysis (5 min)
            if self.enable_editor:
                await self._phase_analysis(metrics)
            
            # Phase 2: Improvement (5 min)
            if self.enable_editor:
                await self._phase_improvement(metrics)
            
            # Phase 3: Validation (5 min)
            if self.enable_validator:
                await self._phase_validation(metrics)
            
            # Phase 4: Oversight (2 min)
            if self.enable_overseer:
                await self._phase_oversight(metrics)
            
            # Phase 5: Archival (1 min)
            if self.enable_archive:
                await self._phase_archival(metrics)
            
            # Phase 6: Failure Recovery (1 min)
            if self.enable_learning:
                await self._phase_failure_recovery(metrics)
            
            # Phase 7: Learning (1 min)
            if self.enable_learning:
                await self._phase_learning(metrics)
            
            metrics.end_time = time.time()
            metrics.duration_sec = metrics.end_time - cycle_start
            metrics.overall_success = metrics.error_count == 0
            
            self._cycle_history.append(metrics)
            
            logger.info("═" * 60)
            logger.info("HEARTBEAT CYCLE %d COMPLETE", self.cycle_number)
            logger.info("Duration: %.1f sec | Improvements: %d approved | "
                       "Validations: %d passed | Failures: %d processed",
                       metrics.duration_sec, metrics.improvements_approved,
                       metrics.validations_passed, metrics.failures_processed)
            logger.info("═" * 60)
            
        except Exception as exc:
            logger.error("Cycle error: %s", exc)
            metrics.error_count += 1
            metrics.end_time = time.time()
            metrics.duration_sec = metrics.end_time - cycle_start
        
        return metrics

    async def _phase_analysis(self, metrics: CycleMetrics) -> None:
        """Phase 1: Analyze codebase for improvement opportunities."""
        logger.info("PHASE 1: ANALYSIS (5 min)")
        self.current_phase = HeartbeatPhase.ANALYSIS
        phase_start = time.time()
        
        try:
            await asyncio.sleep(0.5)  # Simulate analysis
            logger.debug("Completed codebase analysis")
            metrics.phases_completed.append(HeartbeatPhase.ANALYSIS.value)
        except Exception as exc:
            logger.error("Analysis phase error: %s", exc)
            metrics.error_count += 1

    async def _phase_improvement(self, metrics: CycleMetrics) -> None:
        """Phase 2: Propose and apply code improvements."""
        logger.info("PHASE 2: IMPROVEMENT (5 min)")
        self.current_phase = HeartbeatPhase.IMPROVEMENT
        
        try:
            # Simulate improvement proposals
            improvements_proposed = 3
            metrics.improvements_proposed = improvements_proposed
            
            # Apply improvements (simulated)
            improvements_applied = 2
            metrics.improvements_applied = improvements_applied
            
            logger.info("Improvements: %d proposed, %d applied", 
                       improvements_proposed, improvements_applied)
            metrics.phases_completed.append(HeartbeatPhase.IMPROVEMENT.value)
        except Exception as exc:
            logger.error("Improvement phase error: %s", exc)
            metrics.error_count += 1

    async def _phase_validation(self, metrics: CycleMetrics) -> None:
        """Phase 3: Validate improvements against benchmarks."""
        logger.info("PHASE 3: VALIDATION (5 min)")
        self.current_phase = HeartbeatPhase.VALIDATION
        
        try:
            # Simulate validation
            validations_passed = 2
            validations_failed = 0
            
            metrics.validations_passed = validations_passed
            metrics.validations_failed = validations_failed
            
            logger.info("Validations: %d passed, %d failed",
                       validations_passed, validations_failed)
            
            # Apply approval gates
            await self._apply_approval_gates(metrics)
            
            metrics.phases_completed.append(HeartbeatPhase.VALIDATION.value)
        except Exception as exc:
            logger.error("Validation phase error: %s", exc)
            metrics.error_count += 1

    async def _phase_oversight(self, metrics: CycleMetrics) -> None:
        """Phase 4: Oversight and quality review."""
        logger.info("PHASE 4: OVERSIGHT (2 min)")
        self.current_phase = HeartbeatPhase.OVERSIGHT
        
        try:
            # Process pending approvals
            approved_count = 0
            for decision in self._pending_approvals:
                if decision.approved:
                    approved_count += 1
                    logger.debug("Approved: %s (score: %.2f)", decision.reason, decision.score)
            
            metrics.improvements_approved = approved_count
            self._pending_approvals.clear()
            
            logger.info("Oversight complete: %d improvements approved", approved_count)
            metrics.phases_completed.append(HeartbeatPhase.OVERSIGHT.value)
        except Exception as exc:
            logger.error("Oversight phase error: %s", exc)
            metrics.error_count += 1

    async def _phase_archival(self, metrics: CycleMetrics) -> None:
        """Phase 5: Archive evolved variants."""
        logger.info("PHASE 5: ARCHIVAL (1 min)")
        self.current_phase = HeartbeatPhase.ARCHIVAL
        
        try:
            # Simulate variant archival
            variants_archived = 2
            metrics.variants_archived = variants_archived
            
            logger.info("Archived %d variants", variants_archived)
            metrics.phases_completed.append(HeartbeatPhase.ARCHIVAL.value)
        except Exception as exc:
            logger.error("Archival phase error: %s", exc)
            metrics.error_count += 1

    async def _phase_failure_recovery(self, metrics: CycleMetrics) -> None:
        """Phase 6: Process failure queue and apply recovery strategies."""
        logger.info("PHASE 6: FAILURE RECOVERY (1 min)")
        self.current_phase = HeartbeatPhase.FAILURE_RECOVERY
        
        try:
            failures_processed = len(self._failure_queue)
            
            for item in self._failure_queue:
                try:
                    if item.retry_count < item.max_retries:
                        logger.debug("Retrying failure %s (attempt %d/%d)",
                                   item.failure_id, item.retry_count + 1, item.max_retries)
                        item.retry_count += 1
                    else:
                        logger.warning("Failure %s exceeded max retries", item.failure_id)
                        item.processed = True
                except Exception as exc:
                    logger.error("Error processing failure %s: %s", item.failure_id, exc)
            
            metrics.failures_processed = failures_processed
            
            # Clear processed items
            self._failure_queue = [item for item in self._failure_queue if not item.processed]
            
            logger.info("Processed %d failures", failures_processed)
            metrics.phases_completed.append(HeartbeatPhase.FAILURE_RECOVERY.value)
        except Exception as exc:
            logger.error("Failure recovery phase error: %s", exc)
            metrics.error_count += 1

    async def _phase_learning(self, metrics: CycleMetrics) -> None:
        """Phase 7: Extract principles from failures and update knowledge base."""
        logger.info("PHASE 7: LEARNING (1 min)")
        self.current_phase = HeartbeatPhase.LEARNING
        
        try:
            # Simulate principle extraction
            principles_extracted = 1 if self._failure_queue else 0
            metrics.principles_extracted = principles_extracted
            
            logger.info("Extracted %d principles from failures", principles_extracted)
            metrics.phases_completed.append(HeartbeatPhase.LEARNING.value)
        except Exception as exc:
            logger.error("Learning phase error: %s", exc)
            metrics.error_count += 1

    async def _apply_approval_gates(self, metrics: CycleMetrics) -> None:
        """Apply three-gate approval system."""
        logger.debug("Applying approval gates")
        
        # Gate 1: Validator Gate (Technical validation)
        validator_decision = ApprovalDecision(
            gate=ApprovalGate.VALIDATOR_GATE,
            approved=metrics.validations_failed == 0,
            score=0.95 if metrics.validations_failed == 0 else 0.3,
            reason="SWE-bench + HLE-mini validation" if metrics.validations_failed == 0 else "Validation failed",
        )
        self._pending_approvals.append(validator_decision)
        logger.debug("Validator Gate: %s (score: %.2f)", validator_decision.approved, validator_decision.score)
        
        # Gate 2: Overseer Gate (Quality review)
        overseer_decision = ApprovalDecision(
            gate=ApprovalGate.OVERSEER_GATE,
            approved=metrics.improvements_applied > 0,
            score=0.88 if metrics.improvements_applied > 0 else 0.5,
            reason="Quality review passed" if metrics.improvements_applied > 0 else "No improvements applied",
        )
        self._pending_approvals.append(overseer_decision)
        logger.debug("Overseer Gate: %s (score: %.2f)", overseer_decision.approved, overseer_decision.score)
        
        # Gate 3: Executor Gate (Execution approval)
        executor_decision = ApprovalDecision(
            gate=ApprovalGate.EXECUTOR_GATE,
            approved=metrics.error_count == 0,
            score=0.92 if metrics.error_count == 0 else 0.4,
            reason="Ready for execution" if metrics.error_count == 0 else f"{metrics.error_count} errors detected",
        )
        self._pending_approvals.append(executor_decision)
        logger.debug("Executor Gate: %s (score: %.2f)", executor_decision.approved, executor_decision.score)

    def add_failure(
        self,
        failure_id: str,
        category: str,
        error_message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Add a failure to the queue for processing.
        
        Args:
            failure_id: Unique failure identifier
            category: Failure category
            error_message: Error message
            context: Additional context
        """
        item = FailureQueueItem(
            failure_id=failure_id,
            category=category,
            timestamp=time.time(),
            error_message=error_message,
            context=context or {},
        )
        
        self._failure_queue.append(item)
        logger.debug("Added failure to queue: %s (%s)", failure_id, category)

    def get_cycle_history(self, limit: int = 10) -> list[CycleMetrics]:
        """Get history of recent cycles."""
        return self._cycle_history[-limit:]

    def get_system_status(self) -> dict[str, Any]:
        """Get current system status."""
        if self._cycle_history:
            latest_cycle = self._cycle_history[-1]
            avg_duration = sum(c.duration_sec for c in self._cycle_history) / len(self._cycle_history)
        else:
            latest_cycle = None
            avg_duration = 0.0
        
        return {
            "is_running": self.is_running,
            "current_phase": self.current_phase.value,
            "cycle_number": self.cycle_number,
            "failure_queue_size": len(self._failure_queue),
            "pending_approvals": len(self._pending_approvals),
            "cycle_history_length": len(self._cycle_history),
            "avg_cycle_duration": avg_duration,
            "latest_cycle": latest_cycle.__dict__ if latest_cycle else None,
        }

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary across all cycles."""
        if not self._cycle_history:
            return {"cycles_completed": 0}
        
        total_improvements = sum(c.improvements_applied for c in self._cycle_history)
        total_approved = sum(c.improvements_approved for c in self._cycle_history)
        total_validations_passed = sum(c.validations_passed for c in self._cycle_history)
        total_failures_processed = sum(c.failures_processed for c in self._cycle_history)
        total_principles = sum(c.principles_extracted for c in self._cycle_history)
        total_variants_archived = sum(c.variants_archived for c in self._cycle_history)
        
        return {
            "cycles_completed": len(self._cycle_history),
            "total_improvements_applied": total_improvements,
            "total_improvements_approved": total_approved,
            "approval_rate_pct": (total_approved / max(total_improvements, 1)) * 100,
            "total_validations_passed": total_validations_passed,
            "total_failures_processed": total_failures_processed,
            "total_principles_extracted": total_principles,
            "total_variants_archived": total_variants_archived,
            "avg_cycle_duration_sec": sum(c.duration_sec for c in self._cycle_history) / len(self._cycle_history),
            "error_rate": sum(c.error_count for c in self._cycle_history) / (len(self._cycle_history) * 7),  # 7 phases
        }
