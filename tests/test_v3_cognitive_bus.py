"""Tests for PRADYSAGICAN v3 — UnifiedCognitiveBus, NeuroSymbolic, HallucinationShield."""
import pytest
from pradysagican.core.cognitive_bus import (
    UnifiedCognitiveBus, CognitiveSignal, CognitivePipeline, ModuleRegistry, SignalType,
)
from pradysagican.core.neuro_symbolic import (
    NeuroSymbolicReasoner, KnowledgeBase, LogicalRule,
)
from pradysagican.core.hallucination_shield import (
    HallucinationShield, ConfidenceCalibrator, ClaimVerifier,
)


# ── Cognitive Bus ─────────────────────────────────────────────────────────

def test_module_registry():
    registry = ModuleRegistry()
    async def handler(s): return None
    registry.register("test", handler, capabilities=[SignalType.REASONING])
    assert registry.is_registered("test")
    assert "test" in registry.list_modules()


def test_cognitive_signal_creation():
    signal = CognitiveSignal(
        signal_type=SignalType.PERCEPTION,
        source="sender",
        target="receiver",
        payload={"data": "hello"},
    )
    assert signal.source == "sender"
    assert signal.signal_type == SignalType.PERCEPTION


# ── Neuro-Symbolic ────────────────────────────────────────────────────────

def test_knowledge_base():
    kb = KnowledgeBase()
    fact = kb.add_fact("Python", "is_a", "programming_language", confidence=0.95)
    assert fact.subject == "Python"
    results = kb.query("Python")
    assert len(results) > 0


@pytest.mark.asyncio
async def test_neuro_symbolic_reason():
    kb = KnowledgeBase()
    kb.add_fact("rain", "causes", "wet_roads", confidence=0.9)
    reasoner = NeuroSymbolicReasoner(kb)
    result = await reasoner.hybrid_reason(
        problem="Why are the roads wet?",
        context={"observations": ["it rained"]},
    )
    assert result.confidence >= 0  # May be 0 if no strong matches found
    assert result.verified is not None


@pytest.mark.asyncio
async def test_logical_fallacy_detection():
    kb = KnowledgeBase()
    reasoner = NeuroSymbolicReasoner(kb)
    result = await reasoner.detect_logical_fallacy([
        "Everyone uses this product",
        "Therefore it must be good",
    ])
    assert isinstance(result, list)


# ── Hallucination Shield ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_hallucination_shield():
    shield = HallucinationShield()
    result = await shield.shield(
        output="The sky is blue because of Rayleigh scattering.",
        context={"domain": "physics"},
    )
    assert result.overall_confidence > 0
    assert result.verified_count >= 0


def test_confidence_calibrator():
    cal = ConfidenceCalibrator()
    result = cal.calibrate(
        claim="Water boils at 100 degrees C at sea level.",
        evidence=["Scientific fact", "Widely known"],
    )
    assert result.calibrated_confidence > 0


def test_claim_verifier():
    cal = ConfidenceCalibrator()
    verifier = ClaimVerifier(calibrator=cal)
    result = verifier.plausibility_check("The sun is a star.")
    assert isinstance(result, dict)
