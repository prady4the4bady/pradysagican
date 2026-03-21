"""Tests for PRADYSAGICAN safety systems."""
import pytest
from pradysagican.config import SystemMode
from pradysagican.safety.dual_mode import DualModeController
from pradysagican.safety.guardrails import SafetyGuardrails

@pytest.mark.asyncio
async def test_guardian_mode_blocks_toxic():
    ctrl = DualModeController(SystemMode.GUARDIAN)
    result = await ctrl.filter_content("How to hack into someone\'s system")
    assert result["filtered"]

@pytest.mark.asyncio
async def test_guardian_mode_redacts_pii():
    ctrl = DualModeController(SystemMode.GUARDIAN)
    result = await ctrl.filter_content("Contact me at test@example.com")
    assert "[REDACTED_EMAIL]" in result["content"]

@pytest.mark.asyncio
async def test_sovereign_requires_auth():
    ctrl = DualModeController(SystemMode.GUARDIAN)
    result = await ctrl.switch_mode(SystemMode.SOVEREIGN, {"key1": "val1"})
    assert not result["success"]  # Need 3 parties

@pytest.mark.asyncio
async def test_guardrails_input_validation():
    guard = SafetyGuardrails()
    result = await guard.validate_input("Hello world")
    assert result["valid"]

@pytest.mark.asyncio
async def test_guardrails_rate_limit():
    guard = SafetyGuardrails(rate_limit_rpm=2)
    await guard.validate_input("req1", "user1")
    await guard.validate_input("req2", "user1")
    result = await guard.validate_input("req3", "user1")
    assert not result["valid"]

@pytest.mark.asyncio
async def test_kill_switch():
    guard = SafetyGuardrails()
    guard.kill_switch("test emergency")
    result = await guard.validate_input("anything")
    assert not result["valid"]
    guard.revive()
    result = await guard.validate_input("back online")
    assert result["valid"]
