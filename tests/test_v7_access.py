"""Tests for PRADYSAGICAN v7 — Access Control, License Gate, Anti-Scraping."""
import pytest
from pradysagican.safety.access_control import (
    AccessController, LicenseGate, LicenseTier, AntiScrapingShield,
    generate_robots_txt,
)


# ── License Gate ──────────────────────────────────────────────────────────

def test_generate_license():
    gate = LicenseGate()
    lic = gate.generate_license(LicenseTier.PROFESSIONAL, "Test Corp", "test@test.com")
    assert lic.key.startswith("PRADY-PROF-")
    assert lic.is_valid()


def test_validate_license():
    gate = LicenseGate()
    lic = gate.generate_license(LicenseTier.PERSONAL, "User", "user@mail.com")
    result = gate.validate(lic.key)
    assert result is not None
    assert result.tier == LicenseTier.PERSONAL


def test_invalid_license():
    gate = LicenseGate()
    result = gate.validate("PRADY-FAKE-12345678-abcdefgh-00000000-11111111-deadbeef")
    assert result is None


def test_license_access_check():
    gate = LicenseGate()
    lic = gate.generate_license(LicenseTier.PERSONAL, "User", "u@m.com")
    result = gate.check_access(lic.key, "use")
    assert result["allowed"]
    # Personal can't modify
    result = gate.check_access(lic.key, "modify")
    assert not result["allowed"]


def test_enterprise_can_modify():
    gate = LicenseGate()
    lic = gate.generate_license(LicenseTier.ENTERPRISE, "BigCorp", "admin@big.com")
    result = gate.check_access(lic.key, "modify")
    assert result["allowed"]


def test_revoke_license():
    gate = LicenseGate()
    lic = gate.generate_license(LicenseTier.TRIAL, "Freeloader", "free@test.com")
    assert gate.validate(lic.key) is not None
    gate.revoke(lic.key, "Terms violation")
    assert gate.validate(lic.key) is None


# ── Anti-Scraping Shield ──────────────────────────────────────────────────

def test_block_gptbot():
    shield = AntiScrapingShield()
    result = shield.check_request("1.2.3.4", user_agent="Mozilla/5.0 (compatible; GPTBot/1.0)")
    assert not result["allowed"]
    assert "scraper" in result.get("reason", "").lower() or "GPTBot" in result.get("scraper", "")


def test_block_claudebot():
    shield = AntiScrapingShield()
    result = shield.check_request("5.6.7.8", user_agent="ClaudeBot/1.0")
    assert not result["allowed"]


def test_allow_normal_user():
    shield = AntiScrapingShield()
    result = shield.check_request(
        "10.0.0.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        path="/",
        referrer="https://github.com/prady4the4bady/pradysagican",
    )
    assert result["allowed"]


def test_rate_limit_scraper():
    shield = AntiScrapingShield()
    # Simulate rapid requests
    for i in range(35):
        shield.check_request("9.9.9.9", user_agent="CustomBot", path=f"/file_{i}.py")
    result = shield.check_request("9.9.9.9", user_agent="CustomBot")
    assert not result["allowed"]  # Should be banned after >30 requests


# ── Access Controller (Combined) ─────────────────────────────────────────

def test_no_license_allowed():
    ac = AccessController()
    result = ac.check_full_access(license_key="", ip_address="1.1.1.1")
    assert result["allowed"]
    assert result.get("mode") == "open_access"


def test_valid_license_allowed():
    ac = AccessController()
    lic = ac.generate_trial("test@example.com")
    result = ac.check_full_access(license_key=lic.key, ip_address="10.0.0.1")
    assert result["allowed"]


def test_stats():
    ac = AccessController()
    stats = ac.stats()
    assert "total_requests" in stats
    assert "blocked_ips" in stats


# ── Robots.txt ────────────────────────────────────────────────────────────

def test_robots_txt():
    txt = generate_robots_txt()
    assert "GPTBot" in txt
    assert "ClaudeBot" in txt
    assert "Disallow: /" in txt
    assert "crawler policy" in txt.lower()
