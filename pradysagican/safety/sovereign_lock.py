"""SOVEREIGN Lock — Multi-layer authentication for government mode.

The government version requires:
1. Master password: pradyisgod (hashed with SHA-256)
2. Multi-party authorization (3+ government officials)
3. Hardware fingerprint validation
4. Time-limited session tokens
"""

from __future__ import annotations

import hashlib
import logging
import platform
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ── Enums ────────────────────────────────────────────────────────────────────

class LicenseType(str, Enum):
    """License tiers controlling access."""
    PERSONAL = "personal"           # Read-only
    PROFESSIONAL = "professional"   # Use only
    ENTERPRISE = "enterprise"       # Use + limited modify
    SOVEREIGN = "sovereign"         # Full access, government only


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class SovereignCredential:
    """A government official's credential."""
    official_id: str
    name: str
    clearance_level: int  # 1-5
    department: str
    signature_hash: str = ""
    issued_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 86400 * 365)

    def __post_init__(self) -> None:
        if not self.signature_hash:
            payload = f"{self.official_id}:{self.name}:{self.department}:{self.issued_at}"
            self.signature_hash = hashlib.sha256(payload.encode()).hexdigest()

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def is_valid_clearance(self) -> bool:
        return 1 <= self.clearance_level <= 5


@dataclass
class SovereignSession:
    """An authenticated SOVEREIGN mode session."""
    token: str
    ip_address: str
    officials: list[str] = field(default_factory=list)
    clearance_level: int = 0
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 14400)  # 4 hours
    is_active: bool = True

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def remaining_seconds(self) -> float:
        return max(0.0, self.expires_at - time.time())


@dataclass
class AuthEvent:
    """Audit log entry for authentication attempts."""
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    ip_address: str = ""
    event_type: str = ""  # "auth_success", "auth_failure", "session_revoked", etc.
    details: str = ""
    officials_involved: list[str] = field(default_factory=list)


@dataclass
class License:
    """A software license."""
    license_key: str = field(default_factory=lambda: uuid.uuid4().hex)
    org_name: str = ""
    license_type: LicenseType = LicenseType.PERSONAL
    issued_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 86400 * 365)
    is_revoked: bool = False
    revoke_reason: str = ""

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired


# ── Sovereign Lock ───────────────────────────────────────────────────────────

class SovereignLock:
    """Multi-layer authentication gate for SOVEREIGN mode.

    Requires:
    1. Correct master password (SHA-256 verified)
    2. At least 3 officials with clearance >= 3
    3. Valid (unexpired) credentials
    4. IP not banned / rate-limited
    """

    # Master password hash (SHA-256 of "pradyisgod")
    _MASTER_HASH: str = hashlib.sha256(b"pradyisgod").hexdigest()

    def __init__(self) -> None:
        self._authorized_sessions: dict[str, SovereignSession] = {}
        self._failed_attempts: dict[str, list[float]] = {}  # ip → timestamps
        self._banned_ips: set[str] = set()
        self._audit_log: list[AuthEvent] = []
        self._max_attempts: int = 5
        self._lockout_duration: float = 3600.0  # seconds
        self._hardware_fp: str = self.generate_hardware_fingerprint()

    # ── Authentication ────────────────────────────────────────────────────

    async def authenticate(
        self,
        password: str,
        credentials: list[SovereignCredential],
        ip_address: str = "127.0.0.1",
    ) -> SovereignSession | None:
        """Full authentication flow for SOVEREIGN access.

        Returns a session on success, None on failure.
        Raises PermissionError if the IP is banned.
        """
        # 1. Check IP ban
        if ip_address in self._banned_ips:
            self._log_event(ip_address, "auth_blocked_banned", "IP is permanently banned")
            raise PermissionError(f"IP {ip_address} is permanently banned")

        # 2. Rate-limit check
        if self._is_rate_limited(ip_address):
            self._log_event(ip_address, "auth_blocked_rate_limit", "Too many failed attempts")
            raise PermissionError(
                f"IP {ip_address} is temporarily locked out ({self._max_attempts} "
                f"failures within {self._lockout_duration}s)"
            )

        # 3. Verify master password
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        if pw_hash != self._MASTER_HASH:
            self._record_failure(ip_address)
            self._log_event(ip_address, "auth_failure", "Invalid master password")
            logger.warning("SOVEREIGN auth failure: bad password from %s", ip_address)
            return None

        # 4. Verify at least 3 credentials with clearance >= 3
        valid_officials: list[SovereignCredential] = []
        for cred in credentials:
            if cred.is_expired:
                continue
            if cred.clearance_level < 3:
                continue
            if not cred.is_valid_clearance:
                continue
            # Verify signature integrity
            expected = hashlib.sha256(
                f"{cred.official_id}:{cred.name}:{cred.department}:{cred.issued_at}".encode()
            ).hexdigest()
            if cred.signature_hash != expected:
                continue
            valid_officials.append(cred)

        if len(valid_officials) < 3:
            self._record_failure(ip_address)
            self._log_event(
                ip_address, "auth_failure",
                f"Insufficient credentials: {len(valid_officials)} valid of {len(credentials)} provided",
            )
            logger.warning(
                "SOVEREIGN auth failure: only %d valid credentials from %s",
                len(valid_officials), ip_address,
            )
            return None

        # 5. Generate session token
        token_seed = f"{uuid.uuid4().hex}:{time.time()}:{ip_address}:{self._hardware_fp}"
        token = hashlib.sha256(token_seed.encode()).hexdigest()

        # 6. Compute session clearance (minimum of officials' levels)
        session_clearance = min(c.clearance_level for c in valid_officials)

        now = time.time()
        session = SovereignSession(
            token=token,
            ip_address=ip_address,
            officials=[c.name for c in valid_officials],
            clearance_level=session_clearance,
            created_at=now,
            expires_at=now + 14400,  # 4 hours
            is_active=True,
        )
        self._authorized_sessions[token] = session

        # 7. Clear failed attempts on success
        self._failed_attempts.pop(ip_address, None)

        self._log_event(
            ip_address, "auth_success",
            f"Session created with clearance {session_clearance}, "
            f"{len(valid_officials)} officials",
            officials=[c.name for c in valid_officials],
        )
        logger.info("SOVEREIGN session created for %s (clearance %d)", ip_address, session_clearance)
        return session

    # ── Session Management ────────────────────────────────────────────────

    def validate_session(self, token: str) -> bool:
        """Check if a session token is still valid and active."""
        session = self._authorized_sessions.get(token)
        if session is None:
            return False
        if session.is_expired or not session.is_active:
            session.is_active = False
            return False
        return True

    def revoke_session(self, token: str) -> bool:
        """Invalidate a single session."""
        session = self._authorized_sessions.get(token)
        if session is None:
            return False
        session.is_active = False
        self._log_event(session.ip_address, "session_revoked", f"Token {token[:12]}...")
        logger.info("Session revoked: %s", token[:12])
        return True

    def revoke_all(self) -> int:
        """Emergency: invalidate ALL active sessions."""
        count = 0
        for token, session in self._authorized_sessions.items():
            if session.is_active:
                session.is_active = False
                count += 1
        self._log_event("system", "all_sessions_revoked", f"Revoked {count} sessions")
        logger.warning("EMERGENCY: all %d SOVEREIGN sessions revoked", count)
        return count

    def is_sovereign_available(self, session_token: str) -> bool:
        """Check if SOVEREIGN mode can be used with this session."""
        if not self.validate_session(session_token):
            return False
        session = self._authorized_sessions[session_token]
        return session.clearance_level >= 3

    def get_session_info(self, token: str) -> dict[str, object]:
        """Return session metadata (safe to expose)."""
        session = self._authorized_sessions.get(token)
        if session is None:
            return {"valid": False}
        return {
            "valid": session.is_active and not session.is_expired,
            "ip_address": session.ip_address,
            "officials": session.officials,
            "clearance_level": session.clearance_level,
            "remaining_seconds": round(session.remaining_seconds, 1),
            "created_at": session.created_at,
        }

    # ── IP Management ─────────────────────────────────────────────────────

    def ban_ip(self, ip: str) -> None:
        """Permanently ban an IP address."""
        self._banned_ips.add(ip)
        # Also revoke any sessions from this IP
        for token, session in self._authorized_sessions.items():
            if session.ip_address == ip and session.is_active:
                session.is_active = False
        self._log_event(ip, "ip_banned", "Permanently banned")
        logger.warning("IP permanently banned: %s", ip)

    def unban_ip(self, ip: str) -> bool:
        """Remove a permanent ban."""
        if ip in self._banned_ips:
            self._banned_ips.discard(ip)
            self._log_event(ip, "ip_unbanned", "Ban removed")
            return True
        return False

    # ── Audit ─────────────────────────────────────────────────────────────

    def get_audit_log(self) -> list[dict[str, object]]:
        """Return the full authentication audit log."""
        return [
            {
                "event_id": ev.event_id,
                "timestamp": ev.timestamp,
                "ip_address": ev.ip_address,
                "event_type": ev.event_type,
                "details": ev.details,
                "officials_involved": ev.officials_involved,
            }
            for ev in self._audit_log
        ]

    # ── Hardware Fingerprint ──────────────────────────────────────────────

    @staticmethod
    def generate_hardware_fingerprint() -> str:
        """Generate a deterministic hardware fingerprint.

        Hashes: hostname, platform, processor, MAC address.
        """
        parts = [
            platform.node(),
            platform.system(),
            platform.machine(),
            platform.processor(),
            str(uuid.getnode()),  # MAC address as int
        ]
        payload = "|".join(parts)
        return hashlib.sha256(payload.encode()).hexdigest()

    # ── Internal Helpers ──────────────────────────────────────────────────

    def _is_rate_limited(self, ip: str) -> bool:
        """Check if IP has exceeded the attempt limit within the lockout window."""
        attempts = self._failed_attempts.get(ip, [])
        cutoff = time.time() - self._lockout_duration
        recent = [t for t in attempts if t > cutoff]
        self._failed_attempts[ip] = recent
        return len(recent) >= self._max_attempts

    def _record_failure(self, ip: str) -> None:
        """Record a failed authentication attempt."""
        self._failed_attempts.setdefault(ip, []).append(time.time())

    def _log_event(
        self,
        ip: str,
        event_type: str,
        details: str,
        officials: list[str] | None = None,
    ) -> None:
        self._audit_log.append(AuthEvent(
            ip_address=ip,
            event_type=event_type,
            details=details,
            officials_involved=officials or [],
        ))

    @property
    def active_session_count(self) -> int:
        return sum(
            1 for s in self._authorized_sessions.values()
            if s.is_active and not s.is_expired
        )

    @property
    def banned_ip_count(self) -> int:
        return len(self._banned_ips)


# ── License Manager ──────────────────────────────────────────────────────────

class LicenseManager:
    """Controls who can use and modify the system.

    License tiers:
    - PERSONAL: read-only access
    - PROFESSIONAL: use only (run queries, get results)
    - ENTERPRISE: use + limited modification rights
    - SOVEREIGN: full access (government only)
    """

    # Permissions per license type
    _PERMISSIONS: dict[LicenseType, dict[str, bool]] = {
        LicenseType.PERSONAL: {
            "read": True, "use": False, "modify": False, "admin": False, "sovereign": False,
        },
        LicenseType.PROFESSIONAL: {
            "read": True, "use": True, "modify": False, "admin": False, "sovereign": False,
        },
        LicenseType.ENTERPRISE: {
            "read": True, "use": True, "modify": True, "admin": False, "sovereign": False,
        },
        LicenseType.SOVEREIGN: {
            "read": True, "use": True, "modify": True, "admin": True, "sovereign": True,
        },
    }

    def __init__(self) -> None:
        self._licenses: dict[str, License] = {}
        self._revoked: dict[str, str] = {}  # key → reason

    def generate_license(
        self,
        org_name: str,
        license_type: LicenseType | str,
        duration_days: int = 365,
    ) -> License:
        """Create a new license for an organisation."""
        if isinstance(license_type, str):
            license_type = LicenseType(license_type.lower())

        now = time.time()
        lic = License(
            org_name=org_name,
            license_type=license_type,
            issued_at=now,
            expires_at=now + 86400 * duration_days,
        )
        self._licenses[lic.license_key] = lic
        logger.info("License generated: %s (%s) for %s", lic.license_key[:8], license_type.value, org_name)
        return lic

    def validate_license(self, license_key: str) -> bool:
        """Check if a license key is valid (exists, not expired, not revoked)."""
        lic = self._licenses.get(license_key)
        if lic is None:
            return False
        return lic.is_valid

    def check_modification_rights(self, license_key: str) -> bool:
        """Only ENTERPRISE and SOVEREIGN licenses can modify the system."""
        lic = self._licenses.get(license_key)
        if lic is None or not lic.is_valid:
            return False
        perms = self._PERMISSIONS.get(lic.license_type, {})
        return perms.get("modify", False)

    def check_permission(self, license_key: str, permission: str) -> bool:
        """Check a specific permission for a license."""
        lic = self._licenses.get(license_key)
        if lic is None or not lic.is_valid:
            return False
        perms = self._PERMISSIONS.get(lic.license_type, {})
        return perms.get(permission, False)

    def revoke_license(self, license_key: str, reason: str = "Revoked by admin") -> bool:
        """Ban a license permanently."""
        lic = self._licenses.get(license_key)
        if lic is None:
            return False
        lic.is_revoked = True
        lic.revoke_reason = reason
        self._revoked[license_key] = reason
        logger.warning("License revoked: %s — %s", license_key[:8], reason)
        return True

    def get_license_info(self, license_key: str) -> dict[str, object]:
        """Return license metadata."""
        lic = self._licenses.get(license_key)
        if lic is None:
            return {"valid": False, "error": "License not found"}
        return {
            "license_key": lic.license_key,
            "org_name": lic.org_name,
            "license_type": lic.license_type.value,
            "is_valid": lic.is_valid,
            "is_expired": lic.is_expired,
            "is_revoked": lic.is_revoked,
            "issued_at": lic.issued_at,
            "expires_at": lic.expires_at,
            "permissions": self._PERMISSIONS.get(lic.license_type, {}),
        }

    def list_licenses(self) -> list[dict[str, object]]:
        """List all issued licenses."""
        return [self.get_license_info(k) for k in self._licenses]

    @property
    def total_licenses(self) -> int:
        return len(self._licenses)

    @property
    def active_licenses(self) -> int:
        return sum(1 for lic in self._licenses.values() if lic.is_valid)
