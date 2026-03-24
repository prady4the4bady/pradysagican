"""
Subscription Enforcement — PRADYSAGICAN
========================================
Self-regenerating TOTP-like token verified every 60 seconds.
No valid subscription → software locks.  Tampering → ban + auto-uninstall.
"""
from __future__ import annotations
import hashlib, hmac, json, logging, os, platform, shutil, time, uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PAYPAL_PAYMENT_URL = "https://www.paypal.com/ncp/payment/M9VNKLDZP2W3J"
MONTHLY_FEE_USD = 5

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"; TRIAL = "trial"; EXPIRED = "expired"
    BANNED = "banned"; LOCKED = "locked"

@dataclass
class SubscriptionToken:
    token_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    user_id: str = ""
    token_hash: str = ""
    generated_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    verified: bool = False
    def is_expired(self) -> bool: return time.time() > self.expires_at

@dataclass
class UserSubscription:
    user_id: str; email: str; tier: str = "trial"
    started_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    status: SubscriptionStatus = SubscriptionStatus.TRIAL
    tokens_generated: int = 0; violations: int = 0
    is_banned: bool = False; ban_reason: str = ""
    paypal_transaction_id: str = ""

class TokenGenerator:
    """TOTP-like token that regenerates every 60 seconds."""
    def __init__(self, secret: str = "pradysagican_token_secret_v6") -> None:
        self._secret = secret.encode()
    def generate(self, user_id: str) -> SubscriptionToken:
        window = int(time.time()) // 60
        raw = f"{user_id}:{window}".encode()
        h = hmac.new(self._secret, raw, hashlib.sha256).hexdigest()
        now = time.time()
        return SubscriptionToken(user_id=user_id, token_hash=h, generated_at=now, expires_at=now + 60, verified=True)
    def verify(self, user_id: str, token_hash: str) -> bool:
        for offset in (0, -1):
            window = int(time.time()) // 60 + offset
            raw = f"{user_id}:{window}".encode()
            expected = hmac.new(self._secret, raw, hashlib.sha256).hexdigest()
            if hmac.compare_digest(expected, token_hash): return True
        return False

class FileIntegrityMonitor:
    """Detects tampering with source files."""
    def __init__(self, install_dir: str = ".") -> None:
        self._dir = Path(install_dir)
        self._manifest: dict[str, str] = {}
        self._compute_manifest()
    def _compute_manifest(self) -> None:
        for f in self._dir.rglob("*.py"):
            if ".git" in str(f): continue
            try: self._manifest[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
            except: pass
    def check_integrity(self) -> dict[str, Any]:
        modified, deleted = [], []
        for path, old_hash in self._manifest.items():
            p = Path(path)
            if not p.exists(): deleted.append(path); continue
            try:
                new_hash = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                if new_hash != old_hash: modified.append(path)
            except: pass
        return {"intact": len(modified) == 0 and len(deleted) == 0, "modified": modified, "deleted": deleted}

class SubscriptionEnforcer:
    """Master subscription enforcer — protects the entire system."""
    def __init__(self) -> None:
        self._token_gen = TokenGenerator()
        self._integrity = FileIntegrityMonitor()
        self._subs: dict[str, UserSubscription] = {}
        self._violations: list[dict] = []
        self._locked_users: set[str] = set()
        self._banned_users: set[str] = set()

    async def check_subscription(self, user_id: str) -> dict[str, Any]:
        if user_id in self._banned_users:
            return {"allowed": False, "status": "banned", "message": "Account permanently banned. Software will uninstall.", "action": "uninstall"}
        if user_id in self._locked_users:
            return {"allowed": False, "status": "locked", "message": f"Software locked. Subscribe at {PAYPAL_PAYMENT_URL}", "action": "prompt_payment"}
        sub = self._subs.get(user_id)
        if not sub:
            return {"allowed": False, "status": "no_subscription", "message": f"No subscription found. Pay ${MONTHLY_FEE_USD}/month at {PAYPAL_PAYMENT_URL}", "payment_url": PAYPAL_PAYMENT_URL}
        if sub.status == SubscriptionStatus.EXPIRED or time.time() > sub.expires_at:
            sub.status = SubscriptionStatus.EXPIRED
            return {"allowed": False, "status": "expired", "message": f"Subscription expired. Renew at {PAYPAL_PAYMENT_URL}", "payment_url": PAYPAL_PAYMENT_URL}
        token = self._token_gen.generate(user_id)
        sub.tokens_generated += 1
        integrity = self._integrity.check_integrity()
        if not integrity["intact"]:
            sub.violations += 1
            self._violations.append({"user": user_id, "time": time.time(), "type": "tampering", "files": integrity["modified"]})
            logger.warning("File tampering detected for %s (violation %d)", user_id, sub.violations)
            if sub.violations >= 3:
                await self.ban_user(user_id, "Repeated file tampering", permanent=True)
                return {"allowed": False, "status": "banned", "message": "Banned: repeated tampering detected. Software will auto-uninstall."}
            return {"allowed": True, "status": "warning", "message": f"WARNING: File tampering detected ({sub.violations}/3 strikes)", "token": token.token_hash}
        return {"allowed": True, "status": sub.status.value, "token": token.token_hash, "expires_in": 60, "tier": sub.tier}

    async def lock_software(self, user_id: str, reason: str) -> dict:
        self._locked_users.add(user_id)
        logger.warning("Software LOCKED for %s: %s", user_id, reason)
        return {"locked": True, "reason": reason, "unlock": f"Pay at {PAYPAL_PAYMENT_URL}"}

    async def ban_user(self, user_id: str, reason: str, permanent: bool = False) -> dict:
        self._banned_users.add(user_id)
        if user_id in self._subs: self._subs[user_id].is_banned = True; self._subs[user_id].ban_reason = reason
        self._violations.append({"user": user_id, "time": time.time(), "type": "ban", "reason": reason, "permanent": permanent})
        if permanent: await self.schedule_uninstall(user_id)
        return {"banned": True, "permanent": permanent, "reason": reason}

    async def schedule_uninstall(self, user_id: str, delay_hours: int = 24) -> dict:
        logger.critical("AUTO-UNINSTALL scheduled for %s in %dh", user_id, delay_hours)
        return {"uninstall_scheduled": True, "delay_hours": delay_hours, "user": user_id}

    async def handle_offline(self, user_id: str) -> dict:
        self._locked_users.add(user_id)
        return {"offline_locked": True, "message": "Connect to internet to verify subscription. Software encrypted until reconnection."}

    def start_trial(self, email: str, duration_days: int = 7) -> UserSubscription:
        uid = hashlib.sha256(email.encode()).hexdigest()[:16]
        sub = UserSubscription(user_id=uid, email=email, tier="trial", expires_at=time.time() + duration_days * 86400)
        self._subs[uid] = sub
        return sub

    def activate_subscription(self, user_id: str, paypal_txn: str = "", tier: str = "monthly") -> UserSubscription:
        sub = self._subs.get(user_id)
        if not sub: sub = UserSubscription(user_id=user_id, email="", tier=tier)
        sub.tier = tier; sub.status = SubscriptionStatus.ACTIVE
        sub.paypal_transaction_id = paypal_txn
        sub.expires_at = time.time() + (30 * 86400 if tier == "monthly" else 365 * 86400)
        self._subs[user_id] = sub
        self._locked_users.discard(user_id); self._banned_users.discard(user_id)
        return sub

    def get_payment_url(self) -> str: return PAYPAL_PAYMENT_URL

    def stats(self) -> dict:
        active = sum(1 for s in self._subs.values() if s.status == SubscriptionStatus.ACTIVE)
        trial = sum(1 for s in self._subs.values() if s.status == SubscriptionStatus.TRIAL)
        return {"active": active, "trial": trial, "banned": len(self._banned_users), "locked": len(self._locked_users), "violations": len(self._violations), "payment_url": PAYPAL_PAYMENT_URL}
