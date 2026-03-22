"""Tests for PRADYSAGICAN v3 — TemporalCortex, CognitiveResilience, QuantumReady, CollectiveIntelligence."""
import pytest
import time
from pradysagican.core.temporal_cortex import (
    TemporalCortex, TemporalEvent, TimePoint, TimeInterval,
)
from pradysagican.core.cognitive_resilience import (
    CognitiveResilience, ExecutionTrace,
)
from pradysagican.core.quantum_ready import (
    QuantumReadyInterface, QuantumBackend, QuantumConfig,
)
from pradysagican.core.collective_intelligence import (
    CollectiveIntelligence, PeerNode, ConsensusProtocol,
)


# ── Temporal Cortex ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_temporal_add_event():
    cortex = TemporalCortex()
    now = time.time()
    event = TemporalEvent(
        id="evt_1", name="Deploy API",
        interval=TimeInterval(
            start=TimePoint(timestamp=now, label="start"),
            end=TimePoint(timestamp=now + 3600, label="end"),
        ),
    )
    await cortex.add_event(event)
    events = await cortex.query_period(now - 1, now + 7200)
    assert len(events) >= 1


@pytest.mark.asyncio
async def test_temporal_conflicts():
    cortex = TemporalCortex()
    now = time.time()
    evt1 = TemporalEvent(
        id="e1", name="Meeting",
        interval=TimeInterval(
            start=TimePoint(timestamp=now, label="s"),
            end=TimePoint(timestamp=now + 3600, label="e"),
        ),
    )
    evt2 = TemporalEvent(
        id="e2", name="Another Meeting",
        interval=TimeInterval(
            start=TimePoint(timestamp=now + 1800, label="s"),
            end=TimePoint(timestamp=now + 5400, label="e"),
        ),
    )
    await cortex.add_event(evt1)
    conflicts = await cortex.detect_conflicts(evt2)
    assert len(conflicts) > 0


@pytest.mark.asyncio
async def test_deadline_pressure():
    cortex = TemporalCortex()
    now = time.time()
    urgent = TemporalEvent(
        id="urgent", name="Due Soon",
        interval=TimeInterval(
            start=TimePoint(timestamp=now, label="s"),
            end=TimePoint(timestamp=now + 60, label="e"),
        ),
    )
    await cortex.add_event(urgent)
    # Pass event ID string, not the event object
    pressure = await cortex.deadline_pressure("urgent")
    assert pressure is not None


# ── Cognitive Resilience ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resilient_execution_success():
    resilience = CognitiveResilience(max_retries=2)

    # Steps must accept state dict as argument
    async def step_ok(state=None):
        return {"value": 42}

    trace = await resilience.execute_resilient(
        steps=[step_ok, step_ok],
        names=["step_1", "step_2"],
    )
    assert trace.overall_success
    assert len(trace.steps) >= 2


@pytest.mark.asyncio
async def test_resilient_execution_with_failure():
    resilience = CognitiveResilience(max_retries=3)
    call_count = 0

    async def flaky_step(state=None):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Transient error")
        return {"recovered": True}

    trace = await resilience.execute_resilient(
        steps=[flaky_step],
        names=["flaky"],
    )
    assert trace.steps[0].retries >= 1


@pytest.mark.asyncio
async def test_reliability_calculation():
    resilience = CognitiveResilience()
    overall = resilience.compute_reliability(20, 0.95)
    assert 0.3 < overall < 0.4  # 0.95^20 ≈ 0.358

    required = resilience.calculate_required_reliability(20, 0.99)
    assert required > 0.999


# ── Quantum Ready ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_quantum_classical_optimize():
    qi = QuantumReadyInterface(QuantumConfig(backend=QuantumBackend.CLASSICAL))
    result = await qi.optimize(
        problem={"type": "minimize", "values": [5, 3, 8, 1, 4]},
        constraints={},
    )
    assert result.backend_used == QuantumBackend.CLASSICAL


@pytest.mark.asyncio
async def test_quantum_search():
    qi = QuantumReadyInterface(QuantumConfig(backend=QuantumBackend.CLASSICAL))
    result = await qi.search(database=list(range(1000)), query=42)
    assert result.result is not None


@pytest.mark.asyncio
async def test_quantum_advantage_estimate():
    qi = QuantumReadyInterface()
    advantage = await qi.estimate_quantum_advantage(problem_size=1_000_000)
    assert advantage is not None


# ── Collective Intelligence ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_peer():
    ci = CollectiveIntelligence()
    peer = PeerNode(
        node_id="node_1", address="localhost:8001",
        capabilities=["reasoning", "coding"], reputation=0.8,
    )
    await ci.register_peer(peer)
    assert "node_1" in ci._peers


@pytest.mark.asyncio
async def test_consensus_majority():
    ci = CollectiveIntelligence()
    proposals = [
        {"solution": "A", "confidence": 0.8},
        {"solution": "A", "confidence": 0.7},
        {"solution": "B", "confidence": 0.9},
    ]
    result = await ci.consensus(proposals, ConsensusProtocol.MAJORITY)
    assert result.consensus_achieved


@pytest.mark.asyncio
async def test_reputation_update():
    ci = CollectiveIntelligence()
    peer = PeerNode(
        node_id="node_2", address="localhost:8002",
        capabilities=["analysis"], reputation=0.5,
    )
    await ci.register_peer(peer)
    await ci.reputation_update("node_2", success=True)
    assert ci._peers["node_2"].reputation >= 0.5
