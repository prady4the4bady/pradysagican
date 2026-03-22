"""Tests for PRADYSAGICAN Tony Stark Intelligence — stark_core."""
import pytest
from pradysagican.agents.stark_core import (
    StarkMindset, DecisionJournal, OperatorDashboard,
    StrategicPlanner, RapidExperimenter,
)


def test_stark_mindset_init():
    mind = StarkMindset()
    assert 0 <= mind.strategic_thinking <= 1
    pillar = mind.dominant_pillar()
    assert isinstance(pillar, str)


@pytest.mark.asyncio
async def test_decision_journal():
    journal = DecisionJournal()
    entry = await journal.record(
        decision="Use GCP for infrastructure",
        reasoning="Best price-performance ratio",
        confidence=0.85,
        alternatives=["AWS", "On-prem"],
    )
    assert entry.decision == "Use GCP for infrastructure"
    assert len(journal.entries) == 1


@pytest.mark.asyncio
async def test_operator_dashboard():
    dash = OperatorDashboard()
    await dash.record_metric("task_success", 1.0)
    await dash.record_metric("task_success", 0.0)
    summary = await dash.summary("task_success")
    assert isinstance(summary, dict)


@pytest.mark.asyncio
async def test_strategic_planner():
    planner = StrategicPlanner()
    moves = await planner.plan_ahead("Build a production API", horizon=5)
    assert isinstance(moves, list)
    assert len(moves) > 0


@pytest.mark.asyncio
async def test_rapid_experimenter():
    exp = RapidExperimenter()
    experiment = await exp.create_experiment(
        name="speed_test",
        hypothesis="Method A is faster",
        variants=["A", "B"],
    )
    assert experiment.name == "speed_test"
    await exp.add_observation("speed_test", "A", 100.0)
    await exp.add_observation("speed_test", "B", 80.0)
    result = await exp.analyze("speed_test")
    assert isinstance(result, dict)
