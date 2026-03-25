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
from pradysagican.core.memory_middleware import MemoryMiddleware
from pradysagican.core.world_model import WorldModel
from pradysagican.agents.orchestrator import MasterOrchestrator, AgentRole
from pradysagican.agents.ethics import EthicsGuardian
from pradysagican.safety.dual_mode import DualModeController
from pradysagican.safety.guardrails import SafetyGuardrails
from pradysagican.capabilities.empathy import EmpathyEngine
from pradysagican.capabilities.intuition import IntuitionEngine
from pradysagican.capabilities.curiosity import CuriosityEngine
from pradysagican.providers import ProviderRouter, select_runtime
from pradysagican.providers.llm import UniversalLLMProvider
from pradysagican.tools.web_crawler import WebCrawlerTool
from pradysagican.upgrades import UpgradeManager
from pradysagican.omega import OmegaConsciousnessStack, MemoryCitadelAPI, HardwareAutoSelect
from pradysagican.godlayer import GodLayerKernel

logger = logging.getLogger(__name__)

# ── Global Instances ──────────────────────────────────────────────────────────

config = load_config()
consciousness = ConsciousnessEngine()
reasoning = ReasoningEngine()
memory = MemorySystem()
memory_middleware = MemoryMiddleware()
world_model = WorldModel()
orchestrator = MasterOrchestrator()
ethics = EthicsGuardian()
dual_mode = DualModeController()
guardrails = SafetyGuardrails()
empathy = EmpathyEngine()
intuition = IntuitionEngine()
curiosity = CuriosityEngine()
llm = UniversalLLMProvider()
router = ProviderRouter()
web_crawler = WebCrawlerTool()
upgrade_manager = UpgradeManager()
runtime_decision = select_runtime()
omega_stack = OmegaConsciousnessStack()
omega_memory = MemoryCitadelAPI()
omega_hardware = HardwareAutoSelect()
godlayer = GodLayerKernel()

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


class GodLayerSomniumRequest(BaseModel):
    events: list[str]
    awake_hours: float = 8.0
    local_hour: int = 3
    idle_minutes: int = 0


class GodLayerFutureRequest(BaseModel):
    current_scores: dict[str, float]
    daily_improvement: float = 0.1
    days: int = 30
    intent: str = "improve reliability while preserving safety"


class GodLayerImmuneRequest(BaseModel):
    anomaly_signature: str
    detector_signals: list[bool]
    complexity: float = 0.5
    impact: float = 0.5
    uncertainty: float = 0.5

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"system": "PRADYSAGICAN", "version": __version__, "mode": dual_mode.mode.value, "status": "operational"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "consciousness_level": consciousness.state.awareness.name,
        "memory": memory.stats(),
        "world_model": world_model.stats(),
        "agents": orchestrator.stats(),
        "llm": llm.stats(),
        "runtime": {"selected": runtime_decision.runtime, "reason": runtime_decision.reason},
        "upgrades": upgrade_manager.summary(),
    }

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
    memory_middleware.ingest_turn(session_id=req.user_id, role="user", content=filtered["content"])
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
    merged = memory_middleware.retrieve(session_id="api_recall", query=query, limit=top_k)
    return {
        "results": [{"id": r.id, "content": r.content[:200], "importance": r.importance} for r in results],
        "cross_session": merged,
    }

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
    return {
        "consciousness": consciousness.state.awareness.name,
        "memory": memory.stats(),
        "world_model": world_model.stats(),
        "agents": orchestrator.stats(),
        "mode": dual_mode.mode.value,
        "upgrades": upgrade_manager.as_dict(),
        "runtime": {"selected": runtime_decision.runtime, "reason": runtime_decision.reason},
        "omega": {"hardware_backend": omega_hardware.select().backend},
        "godlayer": {"total_tools": godlayer.inventory().get("total_tools", 0)},
    }


@app.get("/upgrades/status")
async def upgrades_status():
    return upgrade_manager.as_dict()


@app.get("/tools/research")
async def tools_research(url: str):
    if not config.upgrades.enable_crawl4ai and config.upgrades.rollout_stage == "off":
        raise HTTPException(403, "Web crawler upgrade is disabled by feature flags.")
    return await web_crawler.research_url(url)


@app.get("/omega/status")
async def omega_status():
    return {
        "enabled_flags": {
            "omega_stack": config.upgrades.enable_omega_stack,
            "omega_memory_citadel": config.upgrades.enable_omega_memory_citadel,
            "omega_safety_net": config.upgrades.enable_omega_safety_net,
            "omega_hardware": config.upgrades.enable_omega_hardware_control,
            "omega_bench_auto": config.upgrades.enable_omega_bench_auto,
        },
        "hardware": {"backend": omega_hardware.select().backend, "reason": omega_hardware.select().reason},
        "memory_tiers": 12,
    }


@app.post("/omega/consciousness/update")
async def omega_consciousness_update(self_model: str, phi: float = 0.5, ignition: float = 0.5, entropy: float = 0.5):
    if not config.upgrades.enable_omega_stack:
        raise HTTPException(403, "OMEGA consciousness stack is disabled.")
    return omega_stack.update(
        specialists=["reasoning", "memory", "planner"],
        surprises=["input_shift"],
        phi=phi,
        gw_ignition_rate=ignition,
        prediction_error_entropy=entropy,
        self_model=self_model,
    )


@app.get("/godlayer/status")
async def godlayer_status():
    return {
        "enabled_flags": {
            "godlayer": config.upgrades.enable_godlayer_inventions,
            "somnium": config.upgrades.enable_somnium_cycle,
            "drift": config.upgrades.enable_drift_pipeline,
            "topological": config.upgrades.enable_topological_intelligence,
            "immune": config.upgrades.enable_immune_self_healing,
            "future_self": config.upgrades.enable_future_self_model,
        },
        "status": godlayer.status(),
    }


@app.post("/godlayer/somnium/run")
async def godlayer_run_somnium(req: GodLayerSomniumRequest):
    if not config.upgrades.enable_godlayer_inventions:
        raise HTTPException(403, "God-layer inventions are disabled.")
    if not config.upgrades.enable_somnium_cycle:
        raise HTTPException(403, "Somnium cycle is disabled.")
    events = [{"event": event} for event in req.events]
    return godlayer.run_somnium_cycle(
        events=events,
        awake_hours=req.awake_hours,
        local_hour=req.local_hour,
        idle_minutes=req.idle_minutes,
    )


@app.post("/godlayer/future-self/project")
async def godlayer_project_future(req: GodLayerFutureRequest):
    if not config.upgrades.enable_godlayer_inventions:
        raise HTTPException(403, "God-layer inventions are disabled.")
    if not config.upgrades.enable_future_self_model:
        raise HTTPException(403, "Future-self simulator is disabled.")
    return godlayer.project_future(
        current_scores=req.current_scores,
        daily_improvement=req.daily_improvement,
        days=req.days,
        intent=req.intent,
    )


@app.post("/godlayer/immune/check")
async def godlayer_immune_check(req: GodLayerImmuneRequest):
    if not config.upgrades.enable_godlayer_inventions:
        raise HTTPException(403, "God-layer inventions are disabled.")
    if not config.upgrades.enable_immune_self_healing:
        raise HTTPException(403, "Self-healing immune layer is disabled.")
    return godlayer.run_immune_check(
        anomaly_signature=req.anomaly_signature,
        detector_signals=req.detector_signals,
        complexity=req.complexity,
        impact=req.impact,
        uncertainty=req.uncertainty,
    )

def main():
    import uvicorn
    uvicorn.run("pradysagican.api.server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
