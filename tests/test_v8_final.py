"""Tests for PRADYSAGICAN final — Access Policy, Task Classifier, CLI."""
import pytest
from pradysagican.safety.access_policy import (
    ACCESS_INFO_URL,
    AccessPolicyEnforcer,
    AccessState,
    FileIntegrityMonitor,
    SessionTokenManager,
)
from pradysagican.core.task_classifier import (
    TaskClassifier, TaskCategory, TaskComplexity, AutonomousResearchEngine,
)


# ── Token Generator ──────────────────────────────────────────────────────

def test_token_generation():
    gen = SessionTokenManager()
    token = gen.generate("user_123")
    assert token.token_hash != ""
    assert not token.is_expired()


def test_token_verification():
    gen = SessionTokenManager()
    token = gen.generate("user_abc")
    assert gen.verify("user_abc", token.token_hash)
    assert not gen.verify("user_abc", "fake_token_hash")


# ── File Integrity ────────────────────────────────────────────────────────

def test_file_integrity():
    monitor = FileIntegrityMonitor()
    result = monitor.check_integrity()
    assert "intact" in result


# ── Access Policy Enforcer ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_access_profile():
    enforcer = AccessPolicyEnforcer()
    profile = enforcer.create_access_profile("test@example.com", role="analyst")
    assert profile.role == "analyst"
    assert profile.state == AccessState.ACTIVE
    result = await enforcer.check_access(profile.user_id)
    assert result["allowed"]


@pytest.mark.asyncio
async def test_no_profile_open_access():
    enforcer = AccessPolicyEnforcer()
    result = await enforcer.check_access("nonexistent_user")
    assert result["allowed"]
    assert result["status"] == "open_access"


@pytest.mark.asyncio
async def test_activate_profile():
    enforcer = AccessPolicyEnforcer()
    profile = enforcer.create_access_profile("test@ops.com", role="observer")
    await enforcer.lock_access(profile.user_id, "maintenance")
    enforcer.activate_profile(profile.user_id, role="operator")
    result = await enforcer.check_access(profile.user_id)
    assert result["allowed"]
    assert result["status"] == "active"
    assert result["role"] == "operator"


@pytest.mark.asyncio
async def test_ban_user():
    enforcer = AccessPolicyEnforcer()
    profile = enforcer.create_access_profile("bad@user.com")
    await enforcer.ban_user(profile.user_id, "Tampering", permanent=True)
    result = await enforcer.check_access(profile.user_id)
    assert not result["allowed"]
    assert result["status"] == "banned"


def test_access_info_url():
    enforcer = AccessPolicyEnforcer()
    url = enforcer.get_access_info_url()
    assert url == ACCESS_INFO_URL


def test_access_stats():
    enforcer = AccessPolicyEnforcer()
    enforcer.create_access_profile("a@b.com")
    stats = enforcer.stats()
    assert stats["provisioned"] >= 1
    assert "access_info_url" in stats


# ── Task Classifier ───────────────────────────────────────────────────────

def test_classify_coding_task():
    c = TaskClassifier()
    task = c.classify("Write a Python function to sort a list")
    assert task.category == TaskCategory.CODING
    assert "nexus" in task.required_subsystems or "auto_tool_builder" in task.required_subsystems


def test_classify_research_task():
    c = TaskClassifier()
    task = c.classify("Research the latest papers on quantum computing and create a hypothesis")
    assert task.category in (TaskCategory.RESEARCH, TaskCategory.INVENTION)
    assert task.complexity in (TaskComplexity.MODERATE, TaskComplexity.COMPLEX, TaskComplexity.RESEARCH_GRADE)


def test_classify_creative_task():
    c = TaskClassifier()
    task = c.classify("Imagine a new way to design cities using AI")
    assert task.category == TaskCategory.CREATIVE


def test_classify_prediction():
    c = TaskClassifier()
    task = c.classify("Predict what will happen to Bitcoin price in 2027")
    assert task.category == TaskCategory.PREDICTION


def test_classify_automation():
    c = TaskClassifier()
    task = c.classify("Automate my email workflow to schedule recurring reports")
    assert task.category == TaskCategory.AUTOMATION
    assert task.autonomous_capable


def test_route_task():
    c = TaskClassifier()
    task = c.classify("Solve this complex engineering problem with multiple constraints")
    route = c.route(task)
    assert "subsystems" in route
    assert "pipeline" in route


def test_suggest_tools():
    c = TaskClassifier()
    task = c.classify("Analyze this dataset and find patterns")
    tools = c.suggest_tools(task)
    assert isinstance(tools, list)
    assert len(tools) > 0


# ── Autonomous Research Engine ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_discover_problems():
    engine = AutonomousResearchEngine()
    problems = await engine.discover_problems("artificial intelligence")
    assert len(problems) >= 3


@pytest.mark.asyncio
async def test_generate_hypothesis():
    engine = AutonomousResearchEngine()
    hyp = await engine.generate_hypothesis("Scalability challenge in AI training")
    assert "hypothesis" in hyp
    assert hyp["confidence"] > 0


@pytest.mark.asyncio
async def test_research_cycle():
    engine = AutonomousResearchEngine()
    result = await engine.research_cycle("machine learning")
    assert result["problems_found"] >= 3
    assert result["hypotheses_generated"] >= 1
