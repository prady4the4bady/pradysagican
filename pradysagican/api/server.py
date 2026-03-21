"""
PRADYSAGICAN API Server
========================
Production-grade FastAPI server exposing all capabilities.
"""
from __future__ import annotations
import logging, time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from pradysagican import __version__
from pradysagican.config import load_config, SystemMode
from pradysagican.core.consciousness import ConsciousnessEngine
from pradysagican.core.reasoning import ReasoningEngine
from pradysagican.core.memory import MemorySystem, MemoryTier
from pradysagican.core.world_model import WorldModel
from pradysagican.agents.orchestrator import MasterOrchestrator, AgentRole
from pradysagican.agents.ethics import EthicsGuardian
from pradysagican.safety.dual_mode import DualModeController
from pradysagican.safety.guardrails import SafetyGuardrails
from pradysagican.capabilities.empathy import EmpathyEngine
from pradysagican.capabilities.intuition import IntuitionEngine
from pradysagican.capabilities.curiosity import CuriosityEngine
from pradysagican.providers.llm import UniversalLLMProvider

logger = logging.getLogger(__name__)

# ── Global Instances ──────────────────────────────────────────────────────────

config = load_config()
consciousness = ConsciousnessEngine()
reasoning = ReasoningEngine()
memory = MemorySystem()
world_model = WorldModel()
orchestrator = MasterOrchestrator()
ethics = EthicsGuardian()
dual_mode = DualModeController()
guardrails = SafetyGuardrails()
empathy = EmpathyEngine()
intuition = IntuitionEngine()
curiosity = CuriosityEngine()
llm = UniversalLLMProvider()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    logger.info("PRADYSAGICAN v%s starting — mode: %s", __version__, config.mode)
    # Spawn default agents
    for role in [AgentRole.RESEARCHER, AgentRole.CODER, AgentRole.ANALYST, AgentRole.WRITER]:
        orchestrator.spawn_agent(role)
    yield
    logger.info("PRADYSAGICAN shutting down")

app = FastAPI(title="PRADYSAGICAN", version=__version__, lifespan=lifespan,
              description="World\'s First Super General Agentic Intelligence")

# ── Request Models ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    mode: str = "auto"
    user_id: str = "anonymous"

class ReasonRequest(BaseModel):
    problem: str
    method: str = "auto"

class MemoryStoreRequest(BaseModel):
    content: str
    tier: str = "episodic"
    importance: float = 0.5

class GoalRequest(BaseModel):
    goal: str

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"system": "PRADYSAGICAN", "version": __version__, "mode": dual_mode.mode.value, "status": "operational"}

@app.get("/health")
async def health():
    return {"status": "healthy", "consciousness_level": consciousness.state.awareness.name, "memory": memory.stats(), "world_model": world_model.stats(), "agents": orchestrator.stats(), "llm": llm.stats()}

@app.post("/chat")
async def chat(req: ChatRequest):
    """Main chat endpoint with full pipeline."""
    # 1. Input validation
    validation = await guardrails.validate_input(req.message, req.user_id)
    if not validation["valid"]:
        raise HTTPException(400, validation.get("error", "Invalid input"))
    # 2. Content filter
    filtered = await dual_mode.filter_content(validation["sanitized"])
    if filtered.get("blocked"):
        raise HTTPException(403, filtered.get("reason", "Content blocked"))
    # 3. Emotion recognition
    emotion = await empathy.recognize_emotions(filtered["content"])
    # 4. Update consciousness
    await consciousness.update_self_model(cognitive_load=0.5, goals=[req.message[:50]])
    # 5. Reasoning
    trace = await reasoning.reason(filtered["content"], mode=req.mode)
    # 6. Store in memory
    await memory.store(filtered["content"], importance=0.6)
    # 7. Ethics check on response
    ethics_check = await ethics.evaluate(trace.conclusion)
    # 8. Output validation
    output_check = await guardrails.validate_output(trace.conclusion)

    return {
        "response": trace.conclusion,
        "reasoning_method": trace.method,
        "confidence": trace.confidence,
        "emotion_detected": emotion.primary,
        "consciousness_level": consciousness.state.awareness.name,
        "ethical_check": ethics_check.permitted,
    }

@app.post("/reason")
async def reason(req: ReasonRequest):
    trace = await reasoning.reason(req.problem, mode=req.method)
    return {"method": trace.method, "steps": trace.steps, "conclusion": trace.conclusion, "confidence": trace.confidence, "nodes_explored": trace.nodes_explored, "duration_ms": trace.duration_ms}

@app.post("/memory/store")
async def store_memory(req: MemoryStoreRequest):
    tier = MemoryTier(req.tier) if req.tier in [t.value for t in MemoryTier] else MemoryTier.EPISODIC
    entry = await memory.store(req.content, tier=tier, importance=req.importance)
    return {"stored": True, "id": entry.id, "tier": entry.tier.value}

@app.get("/memory/recall")
async def recall_memory(query: str, top_k: int = 5):
    results = await memory.recall(query, top_k=top_k)
    return {"results": [{"id": r.id, "content": r.content[:200], "importance": r.importance} for r in results]}

@app.post("/orchestrate")
async def orchestrate(req: GoalRequest):
    result = await orchestrator.plan_and_execute(req.goal)
    return result

@app.get("/introspect")
async def introspect():
    report = await consciousness.introspect()
    return {"awareness": report.state_after.awareness.name, "confidence": report.state_after.confidence, "cognitive_load": report.state_after.cognitive_load, "notes": report.metacognitive_notes, "recommendations": report.recommendations}

@app.get("/stats")
async def stats():
    return {"consciousness": consciousness.state.awareness.name, "memory": memory.stats(), "world_model": world_model.stats(), "agents": orchestrator.stats(), "mode": dual_mode.mode.value}

def main():
    import uvicorn
    uvicorn.run("pradysagican.api.server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
