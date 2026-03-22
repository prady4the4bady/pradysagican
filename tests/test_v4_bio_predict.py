"""Tests for PRADYSAGICAN v4 — BioCore, PredictionEngine, AutoToolBuilder."""
import pytest
from pradysagican.core.bio_core import BioCore, Homeostasis, SelfRepair, Metabolism, EvolutionaryAdaptation
from pradysagican.core.prediction_engine import PredictionEngine, BayesianPredictor, EnsemblePredictor
from pradysagican.core.auto_tool_builder import AutoToolBuilder, WebConnector


# ── BioCore ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_homeostasis():
    h = Homeostasis()
    vitals = h.vital_signs()
    assert "energy" in vitals
    assert "health" in vitals
    await h.regulate()
    assert h.vital_signs()["health"] > 0


@pytest.mark.asyncio
async def test_self_repair():
    repair = SelfRepair()
    diagnosis = await repair.diagnose()
    assert isinstance(diagnosis, (list, dict))


@pytest.mark.asyncio
async def test_metabolism():
    meta = Metabolism()
    raw = await meta.ingest("test information about AI systems and machine learning")
    assert raw is not None
    processed = await meta.digest("test information about AI systems and machine learning")
    assert processed is not None


@pytest.mark.asyncio
async def test_bio_core_lifecycle():
    bio = BioCore()
    await bio.life_cycle()
    assert bio.is_alive()
    status = bio.status()
    assert isinstance(status, dict)


# ── Prediction Engine ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bayesian_predictor():
    bp = BayesianPredictor()
    posterior = bp.update_prior(prior=0.5, evidence=0.8, likelihood=0.9)
    assert 0 < posterior < 1


@pytest.mark.asyncio
async def test_prediction_engine():
    engine = PredictionEngine()
    result = await engine.predict(
        question="Will the stock market rise tomorrow?",
        domain="economics",
        evidence=["Recent GDP growth", "Low unemployment"],
    )
    assert result.confidence > 0
    assert result.prediction is not None


@pytest.mark.asyncio
async def test_prediction_explain():
    engine = PredictionEngine()
    result = await engine.predict(
        question="Is Python faster than C?",
        domain="computer_science",
        evidence=["Compiled vs interpreted"],
    )
    explanation = await engine.explain_prediction(result)
    assert explanation is not None


# ── Auto Tool Builder ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_web_connector():
    wc = WebConnector()
    results = await wc.search_web("artificial intelligence")
    assert isinstance(results, (list, dict))


@pytest.mark.asyncio
async def test_auto_tool_builder():
    builder = AutoToolBuilder()
    need = await builder.identify_need("I need to calculate fibonacci numbers")
    assert need is not None
    blueprint = await builder.design_tool(need)
    assert blueprint.name is not None
    tool = await builder.build_tool(blueprint)
    assert tool is not None
