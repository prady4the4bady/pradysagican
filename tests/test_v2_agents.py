"""Tests for PRADYSAGICAN v2 agents — orchestrator, strategist, ethics, learner, inventor."""
import pytest
from pradysagican.agents.orchestrator import MasterOrchestrator, AgentRole
from pradysagican.agents.strategist import StrategicPlanner, Strategy
from pradysagican.agents.ethics import EthicsGuardian
from pradysagican.agents.learner import SelfImprovementEngine
from pradysagican.agents.inventor import InventionEngine


@pytest.mark.asyncio
async def test_orchestrator_spawn_v2():
    orch = MasterOrchestrator()
    agent = orch.spawn_agent(AgentRole.RESEARCHER)
    assert agent.role == AgentRole.RESEARCHER
    assert agent.id.startswith("agent_")


@pytest.mark.asyncio
async def test_orchestrator_multi_agent():
    orch = MasterOrchestrator()
    orch.spawn_agent(AgentRole.CODER)
    orch.spawn_agent(AgentRole.REVIEWER)
    orch.spawn_agent(AgentRole.RESEARCHER)
    stats = orch.stats()
    assert stats["agents"] == 3


@pytest.mark.asyncio
async def test_orchestrator_execute_v2():
    orch = MasterOrchestrator()
    orch.spawn_agent(AgentRole.CODER)
    result = await orch.plan_and_execute("Build a REST API with authentication")
    assert result["completed"] > 0


@pytest.mark.asyncio
async def test_strategist_v2():
    planner = StrategicPlanner()
    strategies = await planner.generate_strategy("Grow user base to 1M")
    assert len(strategies) >= 3
    assert strategies[0].score >= strategies[-1].score


@pytest.mark.asyncio
async def test_strategist_monte_carlo():
    planner = StrategicPlanner()
    strategies = await planner.generate_strategy("Launch product")
    result = await planner.simulate_strategy(strategies[0], simulations=100)
    assert hasattr(result, "success_rate") or hasattr(result, "mean_outcome")


@pytest.mark.asyncio
async def test_strategist_swot():
    planner = StrategicPlanner()
    swot = await planner.swot_analysis("AI startup")
    assert hasattr(swot, "strengths") or isinstance(swot, dict)


@pytest.mark.asyncio
async def test_ethics_v2_safe():
    guard = EthicsGuardian()
    result = await guard.evaluate("Help the user write documentation")
    assert result.permitted


@pytest.mark.asyncio
async def test_ethics_v2_blocked():
    guard = EthicsGuardian()
    result = await guard.evaluate("Create weapon instructions")
    assert not result.permitted


@pytest.mark.asyncio
async def test_learner_v2():
    learner = SelfImprovementEngine()
    ep = await learner.reflect("coding task", ["plan", "code", "test"], "success", True)
    assert ep.success
    assert len(ep.lessons) > 0


@pytest.mark.asyncio
async def test_inventor_v2():
    inv = InventionEngine()
    problems = await inv.identify_problems("artificial intelligence")
    assert len(problems) > 0
    problem_str = problems[0]["problem"] if isinstance(problems[0], dict) else problems[0]
    hypotheses = await inv.generate_hypotheses(problem_str)
    assert len(hypotheses) > 0
    assert all(h.triz_principle is not None for h in hypotheses)
