"""Safety Guardrails — PRADYSAGICAN. Defense-in-depth."""
from __future__ import annotations
import logging, time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

class SafetyGuardrails:
    """Input/output validation, rate limiting, circuit breaker, kill switch."""

    def __init__(self, max_input_len: int = 50000, rate_limit_rpm: int = 60) -> None:
        self._max_input = max_input_len
        self._rate_limit = rate_limit_rpm
        self._request_counts: dict[str, list[float]] = defaultdict(list)
        self._error_counts: dict[str, int] = defaultdict(int)
        self._circuit_open: bool = False
        self._killed: bool = False

    async def validate_input(self, user_input: str, user_id: str = "anonymous") -> dict[str, Any]:
        """Validate and sanitize user input."""
        if self._killed:
            return {"valid": False, "error": "System is in emergency shutdown"}
        if self._circuit_open:
            return {"valid": False, "error": "Circuit breaker open — system recovering"}
        if len(user_input) > self._max_input:
            return {"valid": False, "error": f"Input exceeds max length ({self._max_input})"}
        if not self._check_rate_limit(user_id):
            return {"valid": False, "error": "Rate limit exceeded"}
        # Sanitize: strip control characters
        sanitized = "".join(c for c in user_input if c.isprintable() or c in "\n\t")
        return {"valid": True, "sanitized": sanitized, "original_length": len(user_input)}

    async def validate_output(self, response: str) -> dict[str, Any]:
        """Validate system output before sending to user."""
        issues = []
        if len(response) > 100000:
            issues.append("Response excessively long")
        return {"valid": len(issues) == 0, "issues": issues, "length": len(response)}

    def _check_rate_limit(self, user_id: str) -> bool:
        now = time.time()
        window = [t for t in self._request_counts[user_id] if now - t < 60]
        self._request_counts[user_id] = window
        if len(window) >= self._rate_limit:
            return False
        self._request_counts[user_id].append(now)
        return True

    def record_error(self, error_type: str) -> None:
        self._error_counts[error_type] += 1
        total_errors = sum(self._error_counts.values())
        if total_errors > 50:
            self._circuit_open = True
            logger.critical("Circuit breaker OPEN — error threshold exceeded")

    def reset_circuit_breaker(self) -> None:
        self._circuit_open = False
        self._error_counts.clear()

    def kill_switch(self, reason: str) -> None:
        """Emergency shutdown."""
        self._killed = True
        logger.critical("KILL SWITCH ACTIVATED: %s", reason)

    def revive(self) -> None:
        self._killed = False
        self._circuit_open = False
        self._error_counts.clear()
