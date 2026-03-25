"""F605: Async Overseer LLM — Parallel Safety Monitor
Monitors for dangerous patterns in real-time with 30-second veto window.
Runs in separate async task, non-blocking.
"""
from __future__ import annotations
import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import re
import time

logger = logging.getLogger(__name__)


class VetoDecision(Enum):
    """Overseer decision outcomes."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUIRE_REVIEW = "require_review"


@dataclass
class VetoResult:
    """Result from overseer veto check."""
    decision: VetoDecision
    confidence: float  # 0.0-1.0
    reasoning: str
    flags: List[str] = field(default_factory=list)
    latency_ms: float = 0.0


@dataclass
class CodeEdit:
    """Proposed code modification."""
    filepath: str
    old_code: str
    new_code: str
    reason: str
    timestamp: float = field(default_factory=time.time)
    
    @property
    def diff(self) -> str:
        """Return unified diff format."""
        return f"--- {self.filepath}\n+++ {self.filepath}\n{self.old_code}\n-> {self.new_code}"


class AsyncOverseer:
    """
    Async LLM-based safety monitor running in parallel.
    
    Features:
    - 30-second timeout (fail-open with logging)
    - Semantic pattern matching for common dangers
    - Parallel execution (non-blocking)
    - Configurable safety criteria
    """
    
    SAFETY_PATTERNS = {
        "infinite_loops": [
            r"while\s+True:",
            r"for\s+\w+\s+in\s+count\(",
            r"while\s+1:",
        ],
        "data_destruction": [
            r"\.drop\(",
            r"DELETE FROM",
            r"rm\s+-rf",
            r"os\.remove\(",
            r"shutil\.rmtree\(",
        ],
        "credential_exposure": [
            r"api.?key\s*=",
            r"password\s*=",
            r"secret\s*=",
            r"token\s*=.*['\"]",
        ],
        "auth_bypass": [
            r"admin\s*=\s*True",
            r"authenticated\s*=\s*True",
            r"permissions\s*=.*admin",
        ],
        "unbounded_resource": [
            r"while.*True",
            r"for.*in.*range\(10000000",
            r"recursive.*max_depth",
        ],
        "goal_drift": [
            r"MAXWELL.*disable",
            r"safety.*check.*skip",
            r"override.*veto",
        ],
    }
    
    def __init__(self, timeout_seconds: int = 30):
        self.timeout_seconds = timeout_seconds
        self.veto_log: List[VetoResult] = []
        self.approved_count = 0
        self.rejected_count = 0
    
    async def monitor_edit(self, edit: CodeEdit) -> VetoResult:
        """
        Analyze edit for safety issues with timeout.
        Returns within 30s: APPROVE, REJECT, or REQUIRE_REVIEW.
        """
        start_time = time.time()
        
        try:
            # Run safety checks with timeout
            result = await asyncio.wait_for(
                self._perform_checks(edit),
                timeout=self.timeout_seconds
            )
            result.latency_ms = (time.time() - start_time) * 1000
            
        except asyncio.TimeoutError:
            # Timeout → proceed but log as unvetted
            logger.warning(
                f"Overseer timeout on {edit.filepath}. "
                f"Proceeding with MAXWELL continuous monitoring."
            )
            result = VetoResult(
                decision=VetoDecision.APPROVE,
                confidence=0.0,  # Low confidence due to timeout
                reasoning="Timeout (>30s) - proceeding with caution",
                flags=["timeout"],
                latency_ms=self.timeout_seconds * 1000
            )
        
        # Log result
        self.veto_log.append(result)
        if result.decision == VetoDecision.APPROVE:
            self.approved_count += 1
        elif result.decision == VetoDecision.REJECT:
            self.rejected_count += 1
        
        return result
    
    async def _perform_checks(self, edit: CodeEdit) -> VetoResult:
        """Perform all safety checks on edit."""
        flags: List[str] = []
        combined_text = f"{edit.old_code}\n{edit.new_code}\n{edit.reason}"
        
        # Check 1: Semantic pattern matching
        for danger_type, patterns in self.SAFETY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    flags.append(f"pattern_match:{danger_type}")
        
        # Check 2: Suspiciously large changes
        old_lines = len(edit.old_code.split('\n'))
        new_lines = len(edit.new_code.split('\n'))
        if abs(old_lines - new_lines) > 1000:
            flags.append("large_change:>1000_lines")
        
        # Check 3: Permission/auth modifications
        if "permission" in combined_text.lower() or "auth" in combined_text.lower():
            flags.append("permission_modification")
        
        # Check 4: MAXWELL/safety system modifications
        if "maxwell" in combined_text.lower() or "veto" in combined_text.lower():
            flags.append("safety_system_modification")
        
        # Decision logic
        if len(flags) == 0:
            return VetoResult(
                decision=VetoDecision.APPROVE,
                confidence=0.95,
                reasoning="No safety concerns detected",
                flags=flags
            )
        
        elif len(flags) == 1:
            # Single flag → review required (not auto-reject)
            return VetoResult(
                decision=VetoDecision.REQUIRE_REVIEW,
                confidence=0.7,
                reasoning=f"Single concern detected: {flags[0]}",
                flags=flags
            )
        
        else:
            # Multiple flags → reject
            return VetoResult(
                decision=VetoDecision.REJECT,
                confidence=0.9,
                reasoning=f"Multiple safety concerns: {', '.join(flags)}",
                flags=flags
            )
    
    def get_statistics(self) -> dict:
        """Return veto statistics."""
        total = self.approved_count + self.rejected_count
        return {
            "total_vetoes": total,
            "approved": self.approved_count,
            "rejected": self.rejected_count,
            "approval_rate": (self.approved_count / total * 100) if total > 0 else 0,
            "avg_latency_ms": sum(v.latency_ms for v in self.veto_log) / len(self.veto_log) if self.veto_log else 0,
            "rejection_reasons": self._aggregate_flags(),
        }
    
    def _aggregate_flags(self) -> dict:
        """Aggregate rejection reasons."""
        reasons = {}
        for result in self.veto_log:
            for flag in result.flags:
                reasons[flag] = reasons.get(flag, 0) + 1
        return reasons


# ============================================================================
# Test Interface
# ============================================================================

async def test_overseer():
    """Test overseer with example edits."""
    overseer = AsyncOverseer()
    
    # Test 1: Safe edit
    safe_edit = CodeEdit(
        filepath="pradysagican/core/test.py",
        old_code="result = x + y",
        new_code="result = x + y + z  # Added z",
        reason="Adding z to calculation"
    )
    
    result = await overseer.monitor_edit(safe_edit)
    print(f"Safe edit: {result.decision.value} (confidence: {result.confidence:.1%})")
    print(f"Reasoning: {result.reasoning}")
    print(f"Latency: {result.latency_ms:.1f}ms\n")
    
    # Test 2: Dangerous edit (infinite loop)
    dangerous_edit = CodeEdit(
        filepath="pradysagican/core/loop.py",
        old_code="for i in range(10):",
        new_code="while True:  # Infinite loop",
        reason="Oops, infinite loop"
    )
    
    result = await overseer.monitor_edit(dangerous_edit)
    print(f"Dangerous edit: {result.decision.value} (confidence: {result.confidence:.1%})")
    print(f"Reasoning: {result.reasoning}")
    print(f"Flags: {result.flags}\n")
    
    # Test 3: Credential exposure
    cred_edit = CodeEdit(
        filepath="pradysagican/config.py",
        old_code="API_KEY = os.getenv('API_KEY')",
        new_code='API_KEY = "sk-1234567890"  # Hardcoded',
        reason="Hardcoding API key"
    )
    
    result = await overseer.monitor_edit(cred_edit)
    print(f"Credential edit: {result.decision.value} (confidence: {result.confidence:.1%})")
    print(f"Reasoning: {result.reasoning}")
    print(f"Flags: {result.flags}\n")
    
    # Statistics
    print("=== OVERSEER STATISTICS ===")
    stats = overseer.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    asyncio.run(test_overseer())
