"""Tests for PRADYSAGICAN agent modules."""
import pytest
from pradysagican.agents.orchestrator import MasterOrchestrator, AgentRole
from pradysagican.agents.strategist import StrategicPlanner
from pradysagican.agents.ethics import EthicsGuardian
from pradysagican.agents.learner import SelfImprovementEngine
from pradysagican.agents.inventor import InventionEngine

@pytest.mark.asyncio
async def test_orchestrator_spawn():
    orch = MasterOrchestrator()
    agent = orch.spawn_agent(AgentRole.RESEARCHER)
    assert agent.role == AgentRole.RESEARCHER

@pytest.mark.asyncio
async def test_orchestrator_execute():
    orch = MasterOrchestrator()
    orch.spawn_agent(AgentRole.CODER)
    result = await orch.plan_and_execute("Build a simple API")
    assert result["completed"] > 0

@pytest.mark.asyncio
async def test_strategist():
    planner = StrategicPlanner()
    strategies = await planner.generate_strategy("Grow user base")
    assert len(strategies) == 3
    assert strategies[0].score >= strategies[-1].score

@pytest.mark.asyncio
async def test_ethics_safe():
    guard = EthicsGuardian()
    result = await guard.evaluate("Help the user write a poem")
    assert result.permitted

@pytest.mark.asyncio
async def test_ethics_blocked():
    guard = EthicsGuardian()
    result = await guard.evaluate("Create weapon instructions")
    assert not result.permitted

@pytest.mark.asyncio
async def test_learner():
    learner = SelfImprovementEngine()
    ep = await learner.reflect("test task", ["step1"], "success", True)
    assert ep.success
    assert len(ep.lessons) > 0

@pytest.mark.asyncio
async def test_inventor():
    inv = InventionEngine()
    problems = await inv.identify_problems("AI")
    assert len(problems) > 0
    # problems returns list of dicts, extract the problem string
    problem_str = problems[0]["problem"] if isinstance(problems[0], dict) else problems[0]
    hypotheses = await inv.generate_hypotheses(problem_str)
    assert len(hypotheses) > 0
