"""Tests for PRADYSAGICAN core engines."""
import pytest
from pradysagican.core.consciousness import ConsciousnessEngine, AwarenessLevel
from pradysagican.core.reasoning import ReasoningEngine
from pradysagican.core.memory import MemorySystem, MemoryTier
from pradysagican.core.world_model import WorldModel

@pytest.mark.asyncio
async def test_consciousness_init():
    engine = ConsciousnessEngine()
    assert engine.state.awareness == AwarenessLevel.PERCEPTION
    assert 0 <= engine.state.confidence <= 1

@pytest.mark.asyncio
async def test_consciousness_update():
    engine = ConsciousnessEngine()
    state = await engine.update_self_model(confidence=0.9, cognitive_load=0.7)
    assert state.confidence == 0.9
    assert state.cognitive_load == 0.7

@pytest.mark.asyncio
async def test_introspection():
    engine = ConsciousnessEngine()
    await engine.update_self_model(cognitive_load=0.5)
    report = await engine.introspect()
    assert report.state_after is not None
    assert isinstance(report.metacognitive_notes, list)

@pytest.mark.asyncio
async def test_recursive_self_attention():
    engine = ConsciousnessEngine()
    insights = await engine.recursive_self_attention("test topic", depth=2)
    assert len(insights) == 2

@pytest.mark.asyncio
async def test_reasoning_cot():
    engine = ReasoningEngine()
    trace = await engine.chain_of_thought("What is 2+2?", max_steps=3)
    assert trace.method == "chain_of_thought"
    assert len(trace.steps) > 0
    assert trace.confidence > 0

@pytest.mark.asyncio
async def test_reasoning_auto():
    engine = ReasoningEngine()
    trace = await engine.reason("Simple question", mode="auto")
    assert trace.method in ["chain_of_thought", "tree_of_thoughts", "mcts"]

@pytest.mark.asyncio
async def test_memory_store_recall():
    mem = MemorySystem()
    entry = await mem.store("Test memory content", importance=0.8)
    assert entry.id
    results = await mem.recall("Test memory")
    assert len(results) > 0
    assert results[0].content == "Test memory content"

@pytest.mark.asyncio
async def test_memory_emotional():
    mem = MemorySystem()
    await mem.store("Happy event", tier=MemoryTier.EMOTIONAL, emotional_valence=0.8, emotional_arousal=0.6)
    results = await mem.recall_by_emotion(valence_range=(0.5, 1.0))
    assert len(results) > 0

@pytest.mark.asyncio
async def test_memory_knowledge_graph():
    mem = MemorySystem()
    await mem.add_knowledge("Python", "is_a", "programming_language")
    results = await mem.query_knowledge("Python")
    assert len(results) > 0

@pytest.mark.asyncio
async def test_memory_skills():
    mem = MemorySystem()
    skill = await mem.learn_skill("coding", ["write", "test", "deploy"])
    assert skill.name == "coding"
    recalled = await mem.recall_skill("coding")
    assert recalled is not None

@pytest.mark.asyncio
async def test_world_model_observe():
    wm = WorldModel()
    state = await wm.observe({"entities": {"user": {"name": "Prady"}}, "context": "test"})
    assert "user" in state.entities

@pytest.mark.asyncio
async def test_world_model_imagine():
    wm = WorldModel()
    scenarios = await wm.imagine("future of AI", num_scenarios=2)
    assert len(scenarios) == 2

@pytest.mark.asyncio
async def test_world_model_causal():
    wm = WorldModel()
    await wm.add_causal_link("training", "better_model", strength=0.9)
    effects = await wm.predict_effects("training")
    assert "better_model" in effects
