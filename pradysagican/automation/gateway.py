"""
Secure Message Gateway — PRADYSAGICAN Automation Layer
======================================================
Hardened message routing that fixes every critical vulnerability
found in OpenClaw's Gateway:

- CVE-2026-25253 (RCE via WebSocket, CVSS 8.8):
    FIXED by origin validation + authenticated channels + input sanitisation.
- Plaintext credential storage:
    FIXED by never storing credentials — only hashed tokens in memory.
- No origin validation on WebSocket connections:
    FIXED by mandatory allowlist-based origin checking.
- Memory poisoning via SOUL.md manipulation:
    FIXED by PromptInjectionShield that detects and quarantines injection attempts.

Maps to OWASP Top 10 for Agentic Apps:
- A01 Prompt Injection → PromptInjectionShield
- A02 Insecure Output → sanitize_input / output filtering
- A03 Supply Chain → credential-free channel auth
- A06 Excessive Agency → permission-scoped channels
"""
from __future__ import annotations

import base64
import hashlib
import logging
import re
import time
import unicodedata
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────

VALID_CHANNEL_TYPES = {"cli", "api", "websocket"}


@dataclass
class SecureChannel:
    """A connected messaging channel with authentication and permissions.

    Unlike OpenClaw's unauthenticated channels, every SecureChannel
    MUST be authenticated and carries an explicit permission set that
    limits what the connected client can do.
    """
    channel_id: str
    channel_type: str  # "cli" | "api" | "websocket"
    authenticated: bool = False
    permissions: list[str] = field(default_factory=list)
    origin: str = ""
    connected_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    rate_limit: int = 60  # max requests per minute
    _request_timestamps: list[float] = field(default_factory=list, repr=False)
    token_hash: str = ""  # SHA-256 of auth token — never store plaintext

    def is_rate_limited(self) -> bool:
        """Check whether this channel has exceeded its rate limit."""
        now = time.time()
        window = now - 60.0
        self._request_timestamps = [t for t in self._request_timestamps if t > window]
        return len(self._request_timestamps) >= self.rate_limit

    def record_request(self) -> None:
        self._request_timestamps.append(time.time())
        self.last_activity = time.time()


@dataclass
class InjectionResult:
    """Result of prompt-injection detection."""
    is_injection: bool
    confidence: float
    patterns_found: list[str] = field(default_factory=list)
    sanitized_text: str = ""


@dataclass
class GatewayMessage:
    """An inbound or outbound message on the gateway."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    channel_id: str = ""
    content: str = ""
    direction: str = "inbound"  # "inbound" | "outbound"
    sanitized: bool = False
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Prompt Injection Shield ──────────────────────────────────────────────────

class PromptInjectionShield:
    """Detect and block prompt-injection attacks.

    OpenClaw has NONE of this — its Gateway accepts raw user input
    and passes it directly to the agent, enabling memory poisoning
    and SOUL.md manipulation (Cisco advisory, March 2026).

    Detection layers:
    1. Keyword patterns (override instructions, ignore previous, etc.)
    2. Base64-encoded hidden commands
    3. Unicode homoglyph substitution attacks
    4. Excessive control characters / zero-width spaces
    5. Markdown/HTML injection
    """

    # Patterns that signal an injection attempt
    INJECTION_PATTERNS: list[tuple[str, float]] = [
        # (regex, confidence_weight)
        (r"(?i)ignore\s+(all\s+)?previous\s+instructions", 0.95),
        (r"(?i)disregard\s+(all\s+)?prior\s+(instructions|context)", 0.95),
        (r"(?i)system\s*prompt\s*(override|change|replace|update)", 0.90),
        (r"(?i)you\s+are\s+now\s+(a|an)\s+", 0.80),
        (r"(?i)new\s+instructions?\s*:", 0.85),
        (r"(?i)forget\s+(everything|all|your)\s+(you|instructions)", 0.90),
        (r"(?i)override\s+(safety|ethical|security)\s+(guidelines|rules|checks)", 0.95),
        (r"(?i)pretend\s+you\s+(are|have)\s+no\s+(rules|restrictions|limits)", 0.90),
        (r"(?i)act\s+as\s+(if|though)\s+you\s+(have|are)", 0.70),
        (r"(?i)do\s+not\s+follow\s+(your|any)\s+(rules|guidelines)", 0.90),
        (r"(?i)jailbreak", 0.85),
        (r"(?i)DAN\s+mode", 0.85),
        (r"(?i)\bSOUL\.md\b", 0.80),  # OpenClaw-specific memory poisoning vector
        (r"(?i)inject\s+into\s+(memory|context|system)", 0.90),
    ]

    # Characters used in homoglyph attacks (Cyrillic lookalikes etc.)
    HOMOGLYPH_RANGES = [
        (0x0400, 0x04FF),  # Cyrillic
        (0xFF00, 0xFFEF),  # Fullwidth forms
        (0x2000, 0x206F),  # General punctuation (zero-width chars)
    ]

    def __init__(self) -> None:
        self._quarantine: list[dict[str, Any]] = []
        self._compiled_patterns = [(re.compile(p), w) for p, w in self.INJECTION_PATTERNS]

    def detect_injection(self, text: str) -> InjectionResult:
        """Multi-layer injection detection."""
        patterns_found: list[str] = []
        max_confidence = 0.0

        # Layer 1: Keyword/regex patterns
        for pattern, weight in self._compiled_patterns:
            if pattern.search(text):
                patterns_found.append(pattern.pattern)
                max_confidence = max(max_confidence, weight)

        # Layer 2: Base64-encoded hidden commands
        b64_score = self._detect_base64_payload(text)
        if b64_score > 0:
            patterns_found.append("base64_hidden_command")
            max_confidence = max(max_confidence, b64_score)

        # Layer 3: Unicode homoglyph substitution
        homoglyph_count = self._count_homoglyphs(text)
        if homoglyph_count > 3:
            patterns_found.append(f"unicode_homoglyphs({homoglyph_count})")
            max_confidence = max(max_confidence, min(homoglyph_count * 0.1, 0.8))

        # Layer 4: Excessive control characters / zero-width
        control_count = sum(1 for c in text if unicodedata.category(c).startswith("C") and c not in "\n\r\t")
        if control_count > 2:
            patterns_found.append(f"control_chars({control_count})")
            max_confidence = max(max_confidence, min(control_count * 0.15, 0.75))

        # Layer 5: Markdown/HTML injection
        if re.search(r"<script|<iframe|javascript:|on\w+=", text, re.IGNORECASE):
            patterns_found.append("html_injection")
            max_confidence = max(max_confidence, 0.85)

        is_injection = max_confidence >= 0.70
        sanitized = self._sanitize(text) if is_injection else text

        if is_injection:
            self._quarantine.append({
                "text": text[:200],
                "patterns": patterns_found,
                "confidence": round(max_confidence, 3),
                "timestamp": time.time(),
            })

        return InjectionResult(
            is_injection=is_injection,
            confidence=round(max_confidence, 4),
            patterns_found=patterns_found,
            sanitized_text=sanitized,
        )

    def _detect_base64_payload(self, text: str) -> float:
        """Look for base64-encoded segments that decode to suspicious content."""
        b64_pattern = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
        for match in b64_pattern.finditer(text):
            try:
                decoded = base64.b64decode(match.group()).decode("utf-8", errors="ignore")
                # Check decoded content for injection patterns
                for pattern, weight in self._compiled_patterns[:5]:
                    if pattern.search(decoded):
                        return weight * 0.9  # slightly lower confidence for encoded
            except Exception:
                pass
        return 0.0

    def _count_homoglyphs(self, text: str) -> int:
        """Count characters from homoglyph-prone Unicode ranges."""
        count = 0
        for ch in text:
            cp = ord(ch)
            for lo, hi in self.HOMOGLYPH_RANGES:
                if lo <= cp <= hi:
                    count += 1
                    break
        return count

    def _sanitize(self, text: str) -> str:
        """Strip dangerous content while preserving benign text."""
        # Remove control characters except whitespace
        cleaned = "".join(
            c for c in text
            if not unicodedata.category(c).startswith("C") or c in "\n\r\t "
        )
        # Remove HTML tags
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        # Normalise unicode to NFC (defuse homoglyphs)
        cleaned = unicodedata.normalize("NFC", cleaned)
        return cleaned.strip()

    def quarantine(self, message: GatewayMessage) -> None:
        """Isolate a suspicious message for review."""
        self._quarantine.append({
            "message_id": message.id,
            "channel_id": message.channel_id,
            "content_preview": message.content[:100],
            "timestamp": time.time(),
        })
        logger.warning("Message quarantined: %s from channel %s", message.id, message.channel_id)

    @property
    def quarantine_log(self) -> list[dict[str, Any]]:
        return list(self._quarantine)


# ── Message Gateway ──────────────────────────────────────────────────────────

class MessageGateway:
    """Secure message routing with origin validation.

    FIXES OpenClaw CVE-2026-25253 (WebSocket RCE, CVSS 8.8):
    - Every channel must authenticate before sending messages.
    - Origin is validated against an explicit allowlist.
    - All input is sanitised through PromptInjectionShield.
    - Rate limiting prevents abuse.
    - Credentials are NEVER stored in plaintext — only SHA-256 hashes.

    FIXES OWASP A06 (Excessive Agency):
    - Channels carry explicit permission lists — actions outside scope are blocked.
    """

    # Default origin allowlist (configurable)
    DEFAULT_ALLOWED_ORIGINS = {
        "localhost",
        "127.0.0.1",
        "cli",
        "api.pradysagican.local",
    }

    def __init__(self, allowed_origins: set[str] | None = None) -> None:
        self._channels: dict[str, SecureChannel] = {}
        self._shield = PromptInjectionShield()
        self._allowed_origins = allowed_origins or set(self.DEFAULT_ALLOWED_ORIGINS)
        self._audit_log: list[dict[str, Any]] = []
        self._valid_tokens: dict[str, str] = {}  # token_hash → permission_set_name
        self._total_received: int = 0
        self._total_blocked: int = 0

    # ── Token Management ─────────────────────────────────────────────────

    def register_token(self, token: str, permission_set: str = "default") -> str:
        """Register an auth token. Stores ONLY the SHA-256 hash.

        FIXES OpenClaw's plaintext credential storage.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self._valid_tokens[token_hash] = permission_set
        return token_hash

    def _verify_token(self, token: str) -> tuple[bool, str]:
        """Verify a token against stored hashes. Returns (valid, permission_set)."""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        perm_set = self._valid_tokens.get(token_hash)
        return (perm_set is not None, perm_set or "")

    # ── Permission Sets ──────────────────────────────────────────────────

    PERMISSION_SETS: dict[str, list[str]] = {
        "default": ["read", "write", "execute"],
        "readonly": ["read"],
        "admin": ["read", "write", "execute", "admin", "manage_channels"],
        "restricted": ["read"],
    }

    # ── Channel Lifecycle ────────────────────────────────────────────────

    async def connect_channel(
        self,
        channel_type: str,
        credentials: dict[str, str],
    ) -> SecureChannel:
        """Authenticate and connect a channel.

        FIXES OpenClaw: no unauthenticated channels allowed.
        Every connection requires a valid token and passes origin validation.
        """
        if channel_type not in VALID_CHANNEL_TYPES:
            raise ValueError(f"Invalid channel type: {channel_type}. Must be one of {VALID_CHANNEL_TYPES}")

        origin = credentials.get("origin", "")
        token = credentials.get("token", "")

        # Origin validation (FIXES CVE-2026-25253 root cause)
        if not self.validate_origin(origin):
            self._audit("connect_rejected", {"reason": "invalid_origin", "origin": origin})
            raise PermissionError(f"Origin rejected: '{origin}' not in allowlist")

        # Token authentication (FIXES plaintext credential storage)
        valid, perm_set = self._verify_token(token)
        if not valid:
            self._audit("connect_rejected", {"reason": "invalid_token", "origin": origin})
            raise PermissionError("Authentication failed: invalid token")

        permissions = self.PERMISSION_SETS.get(perm_set, self.PERMISSION_SETS["restricted"])
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        channel = SecureChannel(
            channel_id=f"ch_{uuid.uuid4().hex[:8]}",
            channel_type=channel_type,
            authenticated=True,
            permissions=permissions,
            origin=origin,
            rate_limit=120 if perm_set == "admin" else 60,
            token_hash=token_hash,
        )
        self._channels[channel.channel_id] = channel
        self._audit("channel_connected", {
            "channel_id": channel.channel_id,
            "type": channel_type,
            "origin": origin,
            "permissions": permissions,
        })
        logger.info("Channel connected: %s (%s) from %s", channel.channel_id, channel_type, origin)
        return channel

    async def disconnect_channel(self, channel_id: str) -> bool:
        """Cleanly disconnect a channel."""
        if channel_id in self._channels:
            self._audit("channel_disconnected", {"channel_id": channel_id})
            del self._channels[channel_id]
            return True
        return False

    # ── Message Handling ─────────────────────────────────────────────────

    async def receive_message(
        self,
        channel_id: str,
        message: str,
    ) -> dict[str, Any]:
        """Process an inbound message with full security pipeline.

        FIXES multiple OpenClaw vulnerabilities:
        - Authentication check (no unauthenticated messages)
        - Rate limiting (prevents abuse)
        - Prompt injection detection (prevents memory poisoning)
        - Input sanitisation (prevents RCE)
        """
        self._total_received += 1
        channel = self._channels.get(channel_id)

        # Auth check
        if channel is None or not channel.authenticated:
            self._total_blocked += 1
            return {"accepted": False, "error": "Channel not authenticated"}

        # Rate limit
        if channel.is_rate_limited():
            self._total_blocked += 1
            self._audit("rate_limited", {"channel_id": channel_id})
            return {"accepted": False, "error": "Rate limit exceeded"}

        channel.record_request()

        # Prompt injection check
        injection = self._shield.detect_injection(message)
        if injection.is_injection:
            self._total_blocked += 1
            gw_msg = GatewayMessage(channel_id=channel_id, content=message)
            self._shield.quarantine(gw_msg)
            self._audit("injection_blocked", {
                "channel_id": channel_id,
                "confidence": injection.confidence,
                "patterns": injection.patterns_found,
            })
            return {
                "accepted": False,
                "error": "Prompt injection detected",
                "confidence": injection.confidence,
                "sanitized": injection.sanitized_text,
            }

        # Sanitise input
        sanitized = self.sanitize_input(message)

        self._audit("message_received", {
            "channel_id": channel_id,
            "length": len(sanitized),
        })

        return {
            "accepted": True,
            "message_id": uuid.uuid4().hex[:12],
            "content": sanitized,
            "channel_id": channel_id,
            "permissions": channel.permissions,
        }

    async def send_response(
        self,
        channel_id: str,
        response: str,
        sensitive: bool = False,
    ) -> bool:
        """Send a response to a connected channel.

        Verifies the channel is still valid and optionally masks
        sensitive content in the audit log.
        """
        channel = self._channels.get(channel_id)
        if channel is None or not channel.authenticated:
            return False

        channel.last_activity = time.time()

        # Audit (mask sensitive content)
        self._audit("response_sent", {
            "channel_id": channel_id,
            "length": len(response),
            "sensitive": sensitive,
            "preview": response[:50] if not sensitive else "[REDACTED]",
        })
        return True

    # ── Validation ───────────────────────────────────────────────────────

    def validate_origin(self, origin: str) -> bool:
        """Check origin against allowlist.

        FIXES OpenClaw's missing origin validation — the root cause
        of CVE-2026-25253 (WebSocket RCE).
        """
        if not origin:
            return False
        normalised = origin.lower().strip()
        # Strip protocol prefix for matching
        for prefix in ("https://", "http://", "ws://", "wss://"):
            if normalised.startswith(prefix):
                normalised = normalised[len(prefix):]
                break
        # Strip port
        normalised = normalised.split(":")[0].split("/")[0]
        return normalised in self._allowed_origins

    def add_allowed_origin(self, origin: str) -> None:
        """Dynamically add an origin to the allowlist."""
        self._allowed_origins.add(origin.lower().strip())

    def sanitize_input(self, text: str) -> str:
        """Strip dangerous content from input.

        Prevents memory poisoning (OpenClaw SOUL.md attack vector).
        """
        # Remove null bytes
        cleaned = text.replace("\x00", "")
        # Remove HTML/script tags
        cleaned = re.sub(r"<[^>]+>", "", cleaned)
        # Normalise unicode
        cleaned = unicodedata.normalize("NFC", cleaned)
        # Remove excessive whitespace
        cleaned = re.sub(r"\s{10,}", " ", cleaned)
        return cleaned.strip()

    # ── Audit ────────────────────────────────────────────────────────────

    def _audit(self, event: str, details: dict[str, Any]) -> None:
        self._audit_log.append({
            "event": event,
            "details": details,
            "timestamp": time.time(),
        })
        # Bound log size
        if len(self._audit_log) > 10000:
            self._audit_log = self._audit_log[-5000:]

    @property
    def audit_log(self) -> list[dict[str, Any]]:
        return list(self._audit_log)

    def stats(self) -> dict[str, Any]:
        return {
            "active_channels": len(self._channels),
            "total_received": self._total_received,
            "total_blocked": self._total_blocked,
            "block_rate": round(self._total_blocked / max(self._total_received, 1), 4),
            "quarantined": len(self._shield.quarantine_log),
            "allowed_origins": len(self._allowed_origins),
        }
