"""
Access Policy Enforcement - PRADYSAGICAN
========================================
Open-access policy primitives for session tokens, integrity checks,
and administrative lock/ban controls.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ACCESS_INFO_URL = "https://github.com/prady4the4bady/pradysagican"


class AccessState(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"
    BANNED = "banned"


@dataclass
class SessionToken:
    token_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    user_id: str = ""
    token_hash: str = ""
    generated_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    verified: bool = False

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


@dataclass
class AccessProfile:
    user_id: str
    email: str
    role: str = "default"
    started_at: float = field(default_factory=time.time)
    state: AccessState = AccessState.ACTIVE
    tokens_generated: int = 0
    violations: int = 0
    is_banned: bool = False
    ban_reason: str = ""


class SessionTokenManager:
    """TOTP-like token manager that rotates every 60 seconds."""

    def __init__(self, secret: str = "pradysagican_access_token_secret_v1") -> None:
        self._secret = secret.encode()

    def generate(self, user_id: str) -> SessionToken:
        window = int(time.time()) // 60
        raw = f"{user_id}:{window}".encode()
        token_hash = hmac.new(self._secret, raw, hashlib.sha256).hexdigest()
        now = time.time()
        return SessionToken(
            user_id=user_id,
            token_hash=token_hash,
            generated_at=now,
            expires_at=now + 60,
            verified=True,
        )

    def verify(self, user_id: str, token_hash: str) -> bool:
        for offset in (0, -1):
            window = int(time.time()) // 60 + offset
            raw = f"{user_id}:{window}".encode()
            expected = hmac.new(self._secret, raw, hashlib.sha256).hexdigest()
            if hmac.compare_digest(expected, token_hash):
                return True
        return False


class FileIntegrityMonitor:
    """Detects local tampering with source files."""

    def __init__(self, install_dir: str = ".") -> None:
        self._dir = Path(install_dir)
        self._manifest: dict[str, str] = {}
        self._compute_manifest()

    def _compute_manifest(self) -> None:
        for file_path in self._dir.rglob("*.py"):
            if ".git" in str(file_path):
                continue
            try:
                digest = hashlib.sha256(file_path.read_bytes()).hexdigest()[:16]
                self._manifest[str(file_path)] = digest
            except OSError:
                continue

    def check_integrity(self) -> dict[str, Any]:
        modified: list[str] = []
        deleted: list[str] = []
        for path, old_hash in self._manifest.items():
            fp = Path(path)
            if not fp.exists():
                deleted.append(path)
                continue
            try:
                new_hash = hashlib.sha256(fp.read_bytes()).hexdigest()[:16]
                if new_hash != old_hash:
                    modified.append(path)
            except OSError:
                continue
        return {
            "intact": len(modified) == 0 and len(deleted) == 0,
            "modified": modified,
            "deleted": deleted,
        }


class AccessPolicyEnforcer:
    """Open-access policy manager with optional user profiles."""

    def __init__(self) -> None:
        self._token_mgr = SessionTokenManager()
        self._integrity = FileIntegrityMonitor()
        self._profiles: dict[str, AccessProfile] = {}
        self._violations: list[dict[str, Any]] = []
        self._locked_users: set[str] = set()
        self._banned_users: set[str] = set()

    async def check_access(self, user_id: str) -> dict[str, Any]:
        if user_id in self._banned_users:
            return {
                "allowed": False,
                "status": AccessState.BANNED.value,
                "message": "Account permanently banned.",
                "action": "block",
            }

        if user_id in self._locked_users:
            return {
                "allowed": False,
                "status": AccessState.LOCKED.value,
                "message": "Access locked pending policy review.",
                "action": "contact_admin",
            }

        profile = self._profiles.get(user_id)
        if not profile:
            return {
                "allowed": True,
                "status": "open_access",
                "message": "Open access mode: no access profile required.",
            }

        token = self._token_mgr.generate(user_id)
        profile.tokens_generated += 1

        integrity = self._integrity.check_integrity()
        if not integrity["intact"]:
            profile.violations += 1
            self._violations.append(
                {
                    "user": user_id,
                    "time": time.time(),
                    "type": "tampering",
                    "files": integrity["modified"],
                }
            )
            logger.warning(
                "File tampering detected for %s (violation %d)",
                user_id,
                profile.violations,
            )
            if profile.violations >= 3:
                await self.ban_user(user_id, "Repeated file tampering", permanent=True)
                return {
                    "allowed": False,
                    "status": AccessState.BANNED.value,
                    "message": "Banned: repeated tampering detected.",
                }
            return {
                "allowed": True,
                "status": "warning",
                "message": f"WARNING: File tampering detected ({profile.violations}/3 strikes)",
                "token": token.token_hash,
            }

        return {
            "allowed": True,
            "status": profile.state.value,
            "role": profile.role,
            "token": token.token_hash,
            "expires_in": 60,
        }

    async def lock_access(self, user_id: str, reason: str) -> dict[str, Any]:
        self._locked_users.add(user_id)
        logger.warning("Access LOCKED for %s: %s", user_id, reason)
        return {"locked": True, "reason": reason, "unlock": "Contact administrator to unlock."}

    async def ban_user(self, user_id: str, reason: str, permanent: bool = False) -> dict[str, Any]:
        self._banned_users.add(user_id)
        profile = self._profiles.get(user_id)
        if profile:
            profile.is_banned = True
            profile.ban_reason = reason
            profile.state = AccessState.BANNED
        self._violations.append(
            {"user": user_id, "time": time.time(), "type": "ban", "reason": reason, "permanent": permanent}
        )
        if permanent:
            await self.schedule_uninstall(user_id)
        return {"banned": True, "permanent": permanent, "reason": reason}

    async def schedule_uninstall(self, user_id: str, delay_hours: int = 24) -> dict[str, Any]:
        logger.critical("AUTO-UNINSTALL scheduled for %s in %dh", user_id, delay_hours)
        return {"uninstall_scheduled": True, "delay_hours": delay_hours, "user": user_id}

    async def handle_offline(self, user_id: str) -> dict[str, Any]:
        return {
            "allowed": True,
            "offline_mode": True,
            "message": f"Offline mode enabled for {user_id}.",
        }

    def create_access_profile(self, email: str, role: str = "default") -> AccessProfile:
        user_id = hashlib.sha256(email.encode()).hexdigest()[:16]
        profile = AccessProfile(user_id=user_id, email=email, role=role)
        self._profiles[user_id] = profile
        return profile

    def activate_profile(self, user_id: str, role: str = "default") -> AccessProfile:
        profile = self._profiles.get(user_id)
        if not profile:
            profile = AccessProfile(user_id=user_id, email="", role=role)
        profile.role = role
        profile.state = AccessState.ACTIVE
        profile.is_banned = False
        profile.ban_reason = ""
        self._profiles[user_id] = profile
        self._locked_users.discard(user_id)
        self._banned_users.discard(user_id)
        return profile

    def get_access_info_url(self) -> str:
        return ACCESS_INFO_URL

    def stats(self) -> dict[str, Any]:
        active = sum(1 for p in self._profiles.values() if p.state == AccessState.ACTIVE)
        return {
            "active": active,
            "provisioned": len(self._profiles),
            "banned": len(self._banned_users),
            "locked": len(self._locked_users),
            "violations": len(self._violations),
            "access_info_url": ACCESS_INFO_URL,
        }
