"""Tests for PRADYSAGICAN final — Subscription, Task Classifier, CLI."""
import pytest
import time
from pradysagican.safety.subscription import (
    SubscriptionEnforcer, TokenGenerator, FileIntegrityMonitor,
    SubscriptionStatus, PAYPAL_PAYMENT_URL,
)
from pradysagican.core.task_classifier import (
    TaskClassifier, TaskCategory, TaskComplexity, AutonomousResearchEngine,
)


# ── Token Generator ──────────────────────────────────────────────────────

def test_token_generation():
    gen = TokenGenerator()
    token = gen.generate("user_123")
    assert token.token_hash != ""
    assert not token.is_expired()


def test_token_verification():
    gen = TokenGenerator()
    token = gen.generate("user_abc")
    assert gen.verify("user_abc", token.token_hash)
    assert not gen.verify("user_abc", "fake_token_hash")


# ── File Integrity ────────────────────────────────────────────────────────

def test_file_integrity():
    monitor = FileIntegrityMonitor()
    result = monitor.check_integrity()
    assert "intact" in result


# ── Subscription Enforcer ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_trial():
    enforcer = SubscriptionEnforcer()
    sub = enforcer.start_trial("test@example.com", 7)
    assert sub.tier == "trial"
    assert sub.status == SubscriptionStatus.TRIAL
    result = await enforcer.check_subscription(sub.user_id)
    assert result["allowed"]


@pytest.mark.asyncio
async def test_no_subscription():
    enforcer = SubscriptionEnforcer()
    result = await enforcer.check_subscription("nonexistent_user")
    assert not result["allowed"]
    assert "payment_url" in result or "subscribe" in result.get("message", "").lower()


@pytest.mark.asyncio
async def test_activate_subscription():
    enforcer = SubscriptionEnforcer()
    sub = enforcer.start_trial("test@pay.com", 7)
    enforcer.activate_subscription(sub.user_id, "PAYPAL_TXN_123", "monthly")
    result = await enforcer.check_subscription(sub.user_id)
    assert result["allowed"]
    assert result["status"] == "active"


@pytest.mark.asyncio
async def test_ban_user():
    enforcer = SubscriptionEnforcer()
    sub = enforcer.start_trial("bad@user.com", 7)
    await enforcer.ban_user(sub.user_id, "Tampering", permanent=True)
    result = await enforcer.check_subscription(sub.user_id)
    assert not result["allowed"]
    assert result["status"] == "banned"


def test_payment_url():
    enforcer = SubscriptionEnforcer()
    url = enforcer.get_payment_url()
    assert "paypal" in url.lower()


def test_subscription_stats():
    enforcer = SubscriptionEnforcer()
    enforcer.start_trial("a@b.com", 7)
    stats = enforcer.stats()
    assert stats["trial"] >= 1
    assert "payment_url" in stats


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
