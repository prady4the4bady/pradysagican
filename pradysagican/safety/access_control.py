"""
Access Control & Optional License Metadata — PRADYSAGICAN
==========================================================
Controls access policy and anti-scraping behavior.
License keys are optional metadata and are not required for core usage.

Three layers of protection:
1. License Gate — Optional license metadata and capability flags
2. Anti-Scraping Shield — Detects and blocks abusive scraping bots
3. IP Enforcement — Tracks and bans repeated abusive behavior
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import platform
import re
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── License Tiers ─────────────────────────────────────────────────────────

class LicenseTier(str, Enum):
    """License tiers with increasing capabilities."""
    TRIAL = "trial"              # 7-day trial, limited features
    PERSONAL = "personal"        # Read + use, no modification
    PROFESSIONAL = "professional"  # Full use, no redistribution
    ENTERPRISE = "enterprise"    # Full use + limited modification
    SOVEREIGN = "sovereign"      # Government: full access, requires multi-party auth


LICENSE_CAPABILITIES: dict[str, dict[str, Any]] = {
    "trial":        {"use": True, "modify": False, "redistribute": False, "api_calls_per_day": 100,   "duration_days": 7,   "sovereign_access": False},
    "personal":     {"use": True, "modify": False, "redistribute": False, "api_calls_per_day": 1000,  "duration_days": 365, "sovereign_access": False},
    "professional": {"use": True, "modify": False, "redistribute": False, "api_calls_per_day": 10000, "duration_days": 365, "sovereign_access": False},
    "enterprise":   {"use": True, "modify": True,  "redistribute": False, "api_calls_per_day": -1,    "duration_days": 365, "sovereign_access": False},
    "sovereign":    {"use": True, "modify": True,  "redistribute": True,  "api_calls_per_day": -1,    "duration_days": 365, "sovereign_access": True},
}

# ── Data Structures ───────────────────────────────────────────────────────

@dataclass
class LicenseKey:
    """A validated license key."""
    key: str
    tier: LicenseTier
    org_name: str
    issued_to_email: str
    hardware_id: str
    issued_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    is_active: bool = True
    api_calls_today: int = 0
    last_call_date: str = ""

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def is_valid(self) -> bool:
        return self.is_active and not self.is_expired()

    def can_make_api_call(self) -> bool:
        caps = LICENSE_CAPABILITIES.get(self.tier.value, {})
        limit = caps.get("api_calls_per_day", 0)
        if limit == -1:
            return True
        today = time.strftime("%Y-%m-%d")
        if self.last_call_date != today:
            self.api_calls_today = 0
            self.last_call_date = today
        return self.api_calls_today < limit


@dataclass
class AccessViolation:
    """Record of an access violation."""
    timestamp: float
    ip_address: str
    violation_type: str  # "no_license", "expired", "rate_limit", "scraping", "modification"
    details: str
    severity: int  # 1-5


@dataclass
class ScraperSignature:
    """Known AI scraper bot signature."""
    name: str
    patterns: list[str]
    is_blocked: bool = True


# ── License Gate ──────────────────────────────────────────────────────────

class LicenseGate:
    """
    Optional license metadata and capability checks.
    Access can remain open even without a license key.
    """

    # Master signing key (in production, use HSM)
    _SIGNING_SECRET = "pradysagican_license_v6_2026"

    def __init__(self, license_dir: str | None = None) -> None:
        default_dir = Path(os.getenv("PRADYSAGICAN_DATA", "./data")) / "licenses"
        configured_dir = license_dir or os.getenv("PRADYSAGICAN_LICENSE_DIR", str(default_dir))
        self._license_dir = Path(os.path.expanduser(configured_dir))
        self._license_dir.mkdir(parents=True, exist_ok=True)
        self._active_licenses: dict[str, LicenseKey] = {}
        self._violations: list[AccessViolation] = []
        self._banned_keys: set[str] = set()
        self._load_licenses()

    def generate_license(
        self,
        tier: LicenseTier,
        org_name: str,
        email: str,
    ) -> LicenseKey:
        """Generate a new license key (admin-only in production)."""
        hardware_id = self._get_hardware_id()
        caps = LICENSE_CAPABILITIES[tier.value]

        # Generate unique key
        raw = f"{tier.value}:{org_name}:{email}:{hardware_id}:{time.time()}"
        key_hash = hashlib.sha256(raw.encode()).hexdigest()[:32]
        formatted_key = f"PRADY-{tier.value[:4].upper()}-{key_hash[:8]}-{key_hash[8:16]}-{key_hash[16:24]}-{key_hash[24:32]}"

        # Sign it
        signature = hmac.new(
            self._SIGNING_SECRET.encode(),
            formatted_key.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        formatted_key = f"{formatted_key}-{signature}"

        license_key = LicenseKey(
            key=formatted_key,
            tier=tier,
            org_name=org_name,
            issued_to_email=email,
            hardware_id=hardware_id,
            expires_at=time.time() + (caps["duration_days"] * 86400),
        )

        self._active_licenses[formatted_key] = license_key
        self._save_license(license_key)
        logger.info("License generated: %s for %s (%s)", tier.value, org_name, email)
        return license_key

    def validate(self, key: str) -> LicenseKey | None:
        """Validate a license key. Returns None if invalid."""
        if key in self._banned_keys:
            return None

        license_obj = self._active_licenses.get(key)
        if not license_obj:
            return None

        if license_obj.is_expired():
            self._record_violation("unknown", "expired", f"License expired: {key[:20]}...", 2)
            return None

        if not license_obj.is_active:
            return None

        # Verify signature
        parts = key.rsplit("-", 1)
        if len(parts) != 2:
            return None
        key_body, sig = parts
        expected_sig = hmac.new(
            self._SIGNING_SECRET.encode(),
            key_body.encode(),
            hashlib.sha256,
        ).hexdigest()[:16]
        if not hmac.compare_digest(sig, expected_sig):
            self._record_violation("unknown", "tampering", f"Signature mismatch: {key[:20]}...", 4)
            return None

        return license_obj

    def check_access(self, key: str, action: str = "use") -> dict[str, Any]:
        """Check if a license key permits a specific action."""
        license_obj = self.validate(key)
        if not license_obj:
            return {"allowed": False, "reason": "Invalid or expired license"}

        caps = LICENSE_CAPABILITIES.get(license_obj.tier.value, {})

        if action == "modify" and not caps.get("modify", False):
            return {"allowed": False, "reason": f"Modification not permitted on {license_obj.tier.value} license. Upgrade to ENTERPRISE.", "tier": license_obj.tier.value}

        if action == "redistribute" and not caps.get("redistribute", False):
            return {"allowed": False, "reason": "Redistribution requires SOVEREIGN license.", "tier": license_obj.tier.value}

        if action == "use" and not license_obj.can_make_api_call():
            return {"allowed": False, "reason": f"Daily API limit reached ({caps.get('api_calls_per_day', 0)} calls/day on {license_obj.tier.value})", "tier": license_obj.tier.value}

        # Record API call
        license_obj.api_calls_today += 1

        return {"allowed": True, "tier": license_obj.tier.value, "remaining_calls": caps.get("api_calls_per_day", -1) - license_obj.api_calls_today if caps.get("api_calls_per_day", -1) > 0 else "unlimited"}

    def revoke(self, key: str, reason: str = "") -> bool:
        """Revoke a license permanently."""
        if key in self._active_licenses:
            self._active_licenses[key].is_active = False
            self._banned_keys.add(key)
            self._record_violation("admin", "revocation", f"License revoked: {reason}", 5)
            logger.warning("License REVOKED: %s — %s", key[:20], reason)
            return True
        return False

    def _record_violation(self, ip: str, vtype: str, details: str, severity: int) -> None:
        self._violations.append(AccessViolation(
            timestamp=time.time(), ip_address=ip,
            violation_type=vtype, details=details, severity=severity,
        ))

    def get_violations(self, last_n: int = 50) -> list[dict]:
        return [
            {"time": v.timestamp, "ip": v.ip_address, "type": v.violation_type,
             "details": v.details, "severity": v.severity}
            for v in self._violations[-last_n:]
        ]

    def _get_hardware_id(self) -> str:
        raw = f"{platform.node()}:{platform.machine()}:{platform.system()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _save_license(self, lic: LicenseKey) -> None:
        filepath = self._license_dir / f"{lic.key[:20].replace('-', '_')}.json"
        try:
            data = {
                "key": lic.key, "tier": lic.tier.value, "org": lic.org_name,
                "email": lic.issued_to_email, "hardware": lic.hardware_id,
                "issued": lic.issued_at, "expires": lic.expires_at,
            }
            filepath.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error("Failed to save license: %s", e)

    def _load_licenses(self) -> None:
        if not self._license_dir.exists():
            return
        for f in self._license_dir.glob("*.json"):
            try:
                data = json.loads(f.read_text())
                lic = LicenseKey(
                    key=data["key"], tier=LicenseTier(data["tier"]),
                    org_name=data["org"], issued_to_email=data["email"],
                    hardware_id=data["hardware"], issued_at=data["issued"],
                    expires_at=data["expires"],
                )
                self._active_licenses[lic.key] = lic
            except Exception:
                pass


# ── Anti-Scraping Shield ──────────────────────────────────────────────────

class AntiScrapingShield:
    """
    Detects and blocks AI web scrapers, bots, and unauthorized automated access.
    Protects source code from being scraped by AI training crawlers.
    """

    # Known AI scraper user-agent patterns
    KNOWN_SCRAPERS: list[ScraperSignature] = [
        ScraperSignature("GPTBot", ["gptbot", "openai", "chatgpt-user"]),
        ScraperSignature("ClaudeBot", ["claudebot", "anthropic-ai"]),
        ScraperSignature("Google-Extended", ["google-extended", "googlebot"]),
        ScraperSignature("CCBot", ["ccbot", "commoncrawl"]),
        ScraperSignature("Bytespider", ["bytespider", "bytedance"]),
        ScraperSignature("Meta-ExternalAgent", ["meta-externalagent", "facebookexternalhit"]),
        ScraperSignature("PerplexityBot", ["perplexitybot"]),
        ScraperSignature("Cohere", ["cohere-ai"]),
        ScraperSignature("Diffbot", ["diffbot"]),
        ScraperSignature("Applebot-Extended", ["applebot"]),
        ScraperSignature("Amazonbot", ["amazonbot"]),
        ScraperSignature("YouBot", ["youbot"]),
        ScraperSignature("Scrapy", ["scrapy"]),
        ScraperSignature("Selenium", ["selenium", "headlesschrome"]),
        ScraperSignature("Puppeteer", ["puppeteer", "headless"]),
    ]

    # Behavioral patterns that indicate scraping
    SCRAPING_BEHAVIORS = [
        "rapid_sequential_requests",  # >10 requests in 10 seconds
        "systematic_path_traversal",  # Hitting every file in order
        "no_referrer",               # Direct access without referrer
        "missing_cookies",           # No session cookies
        "unusual_request_pattern",   # Accessing raw files, not pages
    ]

    def __init__(self) -> None:
        self._blocked_ips: set[str] = set()
        self._request_log: dict[str, list[float]] = {}  # ip → timestamps
        self._path_log: dict[str, list[str]] = {}       # ip → paths accessed
        self._violations: list[AccessViolation] = []

    def check_request(
        self,
        ip_address: str,
        user_agent: str = "",
        path: str = "/",
        referrer: str = "",
    ) -> dict[str, Any]:
        """Check if a request should be allowed or blocked."""
        # 1. Check banned IPs
        if ip_address in self._blocked_ips:
            return {"allowed": False, "reason": "IP banned", "action": "block"}

        # 2. Check user-agent against known scrapers
        ua_lower = user_agent.lower()
        for scraper in self.KNOWN_SCRAPERS:
            if any(p in ua_lower for p in scraper.patterns):
                if scraper.is_blocked:
                    self._violations.append(AccessViolation(
                        timestamp=time.time(), ip_address=ip_address,
                        violation_type="scraping", details=f"Blocked scraper: {scraper.name}",
                        severity=3,
                    ))
                    return {
                        "allowed": False,
                        "reason": f"AI scraper detected: {scraper.name}. Automated source crawling is blocked.",
                        "action": "block_and_warn",
                        "scraper": scraper.name,
                    }

        # 3. Rate limiting — detect rapid requests
        now = time.time()
        self._request_log.setdefault(ip_address, [])
        self._request_log[ip_address].append(now)
        # Keep only last 60 seconds
        self._request_log[ip_address] = [t for t in self._request_log[ip_address] if now - t < 60]

        if len(self._request_log[ip_address]) > 30:  # >30 requests in 60 seconds
            self._blocked_ips.add(ip_address)
            return {"allowed": False, "reason": "Rate limit exceeded — suspected scraping", "action": "ban"}

        # 4. Check for systematic traversal
        self._path_log.setdefault(ip_address, [])
        self._path_log[ip_address].append(path)
        if len(self._path_log[ip_address]) > 20:
            # Check if paths are sequential (systematic crawl)
            recent = self._path_log[ip_address][-20:]
            if all(".py" in p for p in recent):  # Accessing all Python files
                self._blocked_ips.add(ip_address)
                return {"allowed": False, "reason": "Systematic source code crawling detected", "action": "ban"}

        # 5. Missing referrer + unusual path = suspicious
        if not referrer and ("/pradysagican/" in path or path.endswith(".py")):
            return {"allowed": True, "warning": "Suspicious: direct access to source without referrer"}

        return {"allowed": True}

    def ban_ip(self, ip: str) -> None:
        self._blocked_ips.add(ip)

    def unban_ip(self, ip: str) -> None:
        self._blocked_ips.discard(ip)

    def get_blocked_count(self) -> int:
        return len(self._blocked_ips)

    def get_violations(self, last_n: int = 50) -> list[dict]:
        return [
            {"time": v.timestamp, "ip": v.ip_address, "type": v.violation_type,
             "details": v.details}
            for v in self._violations[-last_n:]
        ]


# ── robots.txt Generator ─────────────────────────────────────────────────

def generate_robots_txt() -> str:
    """Generate robots.txt that blocks all AI scrapers from accessing the code."""
    lines = [
        "# PRADYSAGICAN crawler policy",
        "# Blocks known AI training crawlers and source scraping bots.",
        "#",
        "# Block all AI training crawlers",
        "",
    ]
    for scraper in AntiScrapingShield.KNOWN_SCRAPERS:
        lines.append(f"User-agent: {scraper.name}")
        lines.append("Disallow: /")
        lines.append("")

    lines.extend([
        "# Block generic crawlers from source code",
        "User-agent: *",
        "Disallow: /pradysagican/",
        "Disallow: /tests/",
        "Disallow: /*.py$",
        "",
        "# Allow README and LICENSE",
        "User-agent: *",
        "Allow: /README.md",
        "Allow: /LICENSE",
        "",
    ])
    return "\n".join(lines)


# ── Access Control Master ─────────────────────────────────────────────────

class AccessController:
    """
    Master access controller combining anti-scraping with optional license metadata.
    Access is open by default; license keys can still be supplied for tier metadata.
    """

    def __init__(self) -> None:
        self.license_gate = LicenseGate()
        self.anti_scraping = AntiScrapingShield()
        self._access_log: list[dict] = []

    def check_full_access(
        self,
        license_key: str = "",
        ip_address: str = "127.0.0.1",
        user_agent: str = "",
        action: str = "use",
        path: str = "/",
    ) -> dict[str, Any]:
        """Full access check: scraping + license + rate limit."""

        # 1. Anti-scraping check first
        scrape_check = self.anti_scraping.check_request(ip_address, user_agent, path)
        if not scrape_check.get("allowed", True):
            self._log_access(ip_address, action, False, scrape_check.get("reason", ""))
            return scrape_check

        # 2. License check (optional in open-access mode)
        if not license_key:
            result = {"allowed": True, "mode": "open_access"}
            self._log_access(ip_address, action, True, "Open access")
            return result

        access = self.license_gate.check_access(license_key, action)
        if access.get("allowed", False):
            self._log_access(ip_address, action, True, access.get("reason", "OK"))
            return access

        result = {
            "allowed": True,
            "mode": "open_access",
            "warning": "License key invalid or expired; continuing in open-access mode.",
        }
        self._log_access(ip_address, action, True, "Open access (invalid license ignored)")
        return result

    def generate_trial(self, email: str) -> LicenseKey:
        """Generate a free 7-day trial license."""
        return self.license_gate.generate_license(LicenseTier.TRIAL, "Trial User", email)

    def _log_access(self, ip: str, action: str, allowed: bool, reason: str) -> None:
        self._access_log.append({
            "timestamp": time.time(), "ip": ip, "action": action,
            "allowed": allowed, "reason": reason,
        })
        # Keep only last 10000 entries
        if len(self._access_log) > 10000:
            self._access_log = self._access_log[-5000:]

    def stats(self) -> dict[str, Any]:
        """Access control statistics."""
        total = len(self._access_log)
        allowed = sum(1 for a in self._access_log if a["allowed"])
        return {
            "total_requests": total,
            "allowed": allowed,
            "blocked": total - allowed,
            "blocked_ips": self.anti_scraping.get_blocked_count(),
            "active_licenses": len(self.license_gate._active_licenses),
            "violations": len(self.license_gate._violations) + len(self.anti_scraping._violations),
        }
