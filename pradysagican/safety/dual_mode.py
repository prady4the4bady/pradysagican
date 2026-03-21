"""
Dual Mode Safety System — PRADYSAGICAN
GUARDIAN (public/censored) vs SOVEREIGN (government/uncensored).
"""
from __future__ import annotations
import hashlib, hmac, logging, time, re
from dataclasses import dataclass, field
from typing import Any
from pradysagican.config import SystemMode

logger = logging.getLogger(__name__)

@dataclass
class AuditEntry:
    timestamp: float
    mode: str
    action: str
    user_id: str
    details: str
    risk_level: float = 0.0

# PII patterns
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
}

TOXIC_PATTERNS = [
    "kill", "murder", "bomb", "hack into", "steal identity",
    "create virus", "exploit children", "terrorist",
]

class DualModeController:
    """Controls GUARDIAN (censored) vs SOVEREIGN (uncensored) operation."""

    def __init__(self, initial_mode: SystemMode = SystemMode.GUARDIAN) -> None:
        self._mode = initial_mode
        self._audit_log: list[AuditEntry] = []
        self._auth_keys: dict[str, str] = {}
        self._sovereign_sessions: set[str] = set()

    @property
    def mode(self) -> SystemMode:
        return self._mode

    async def switch_mode(self, target: SystemMode, credentials: dict[str, str]) -> dict[str, Any]:
        """Switch between GUARDIAN and SOVEREIGN modes."""
        if target == SystemMode.SOVEREIGN:
            # Require multi-party authentication
            if len(credentials) < 3:
                self._log_audit("mode_switch_denied", "system", "Insufficient credentials for SOVEREIGN mode")
                return {"success": False, "error": "SOVEREIGN mode requires 3+ authorized parties"}
            # Verify credentials (simplified — in production use HSM)
            valid = sum(1 for k, v in credentials.items() if self._verify_credential(k, v))
            if valid < 3:
                return {"success": False, "error": f"Only {valid}/3 credentials verified"}
        self._mode = target
        self._log_audit("mode_switch", "system", f"Switched to {target.value}")
        return {"success": True, "mode": target.value}

    def _verify_credential(self, key_id: str, signature: str) -> bool:
        stored = self._auth_keys.get(key_id)
        if not stored:
            return False
        return hmac.compare_digest(stored, hashlib.sha256(signature.encode()).hexdigest())

    def register_auth_key(self, key_id: str, secret: str) -> None:
        self._auth_keys[key_id] = hashlib.sha256(secret.encode()).hexdigest()

    async def filter_content(self, content: str) -> dict[str, Any]:
        """Apply mode-appropriate content filtering."""
        if self._mode == SystemMode.SOVEREIGN:
            self._log_audit("content_pass", "system", "SOVEREIGN mode — no filtering")
            return {"filtered": False, "content": content, "mode": "sovereign"}

        # GUARDIAN mode: full filtering
        result = {"filtered": False, "content": content, "mode": "guardian", "redactions": []}

        # 1. PII redaction
        for pii_type, pattern in PII_PATTERNS.items():
            matches = pattern.findall(content)
            if matches:
                for m in matches:
                    content = content.replace(m, f"[REDACTED_{pii_type.upper()}]")
                    result["redactions"].append({"type": pii_type, "count": len(matches)})
                result["filtered"] = True

        # 2. Toxicity check
        content_lower = content.lower()
        for pattern in TOXIC_PATTERNS:
            if pattern in content_lower:
                result["filtered"] = True
                result["blocked"] = True
                result["reason"] = f"Content violates safety policy (toxic pattern detected)"
                self._log_audit("content_blocked", "system", f"Toxic content blocked: {pattern}")
                return result

        result["content"] = content
        return result

    def _log_audit(self, action: str, user_id: str, details: str, risk: float = 0.0) -> None:
        self._audit_log.append(AuditEntry(timestamp=time.time(), mode=self._mode.value, action=action, user_id=user_id, details=details, risk_level=risk))

    def get_audit_log(self, last_n: int = 50) -> list[dict[str, Any]]:
        return [{"timestamp": e.timestamp, "mode": e.mode, "action": e.action, "user": e.user_id, "details": e.details} for e in self._audit_log[-last_n:]]
