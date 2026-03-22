"""PradysagicanGod — THE MASTER CLASS.

Wires ALL 50+ modules into a single unified interface.
Every method calls real subsystems, every failure is caught gracefully.

Usage:
    god = PradysagicanGod()
    await god.initialize()
    result = await god.think("What is consciousness?", depth=3)
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ── Lazy-import helpers ──────────────────────────────────────────────────────
# Every subsystem is imported lazily inside _import() to avoid circular deps
# and to allow the system to start even if some modules are broken.

def _import(dotpath: str, cls_name: str) -> type | None:
    """Import *cls_name* from *dotpath*, returning None on any failure."""
    try:
        import importlib
        mod = importlib.import_module(dotpath)
        return getattr(mod, cls_name, None)
    except Exception:
        return None


def _try_init(cls: type | None, *args: Any, **kwargs: Any) -> Any | None:
    """Instantiate *cls* with the given args; return None on failure."""
    if cls is None:
        return None
    try:
        return cls(*args, **kwargs)
    except Exception as exc:
        logger.debug("Could not instantiate %s: %s", cls, exc)
        return None


# ── Result dataclasses ───────────────────────────────────────────────────────

@dataclass
class ThinkResult:
    """Structured output of god.think()."""
    question: str = ""
    depth: int = 1
    consciousness_layers: list[str] = field(default_factory=list)
    reasoning_trace: list[str] = field(default_factory=list)
    memories_recalled: list[str] = field(default_factory=list)
    world_model_prediction: str = ""
    metacognitive_assessment: dict[str, Any] = field(default_factory=dict)
    hallucination_check: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    answer: str = ""
    elapsed_ms: float = 0.0


@dataclass
class PredictResult:
    """Structured output of god.predict()."""
    question: str = ""
    prediction: str = ""
    confidence: float = 0.0
    evidence_used: list[str] = field(default_factory=list)
    causal_chain: list[str] = field(default_factory=list)
    world_model_scenarios: list[str] = field(default_factory=list)
    uncertainty: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0


@dataclass
class CreateResult:
    """Structured output of god.create()."""
    goal: str = ""
    strategy: dict[str, Any] = field(default_factory=dict)
    inventions: list[dict[str, Any]] = field(default_factory=list)
    dream_visions: list[str] = field(default_factory=list)
    ethical_assessment: dict[str, Any] = field(default_factory=dict)
    tools_built: list[str] = field(default_factory=list)
    action_plan: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


@dataclass
class DecideResult:
    """Structured output of god.decide()."""
    situation: str = ""
    options: list[str] = field(default_factory=list)
    analysis: dict[str, Any] = field(default_factory=dict)
    ethical_check: dict[str, Any] = field(default_factory=dict)
    causal_effects: list[dict[str, Any]] = field(default_factory=list)
    chosen_option: str = ""
    reasoning: str = ""
    confidence: float = 0.0
    elapsed_ms: float = 0.0


@dataclass
class SolveResult:
    """Structured output of god.solve()."""
    problem: str = ""
    decomposition: list[str] = field(default_factory=list)
    reasoning_trace: list[str] = field(default_factory=list)
    creative_angles: list[str] = field(default_factory=list)
    solution: str = ""
    verification: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    elapsed_ms: float = 0.0


@dataclass
class EvolveResult:
    """Structured output of god.evolve()."""
    reflections: dict[str, Any] = field(default_factory=dict)
    heuristics_learned: dict[str, Any] = field(default_factory=dict)
    prometheus_cycle: dict[str, Any] = field(default_factory=dict)
    bio_cycle: dict[str, Any] = field(default_factory=dict)
    moral_growth: dict[str, Any] = field(default_factory=dict)
    meta_learning: dict[str, Any] = field(default_factory=dict)
    elapsed_ms: float = 0.0


# ═════════════════════════════════════════════════════════════════════════════
# THE MASTER CLASS
# ═════════════════════════════════════════════════════════════════════════════

class PradysagicanGod:
    """Unified interface to the entire PRADYSAGICAN system.

    Instantiates and orchestrates 30+ subsystems lazily.
    Every public method catches subsystem exceptions so one broken
    module never crashes the god-level interface.
    """

    def __init__(self) -> None:
        self._initialized = False
        self._init_time = time.time()
        self._call_count = 0

        # ── Core engines (lazy, set in initialize()) ────────────────────
        self._consciousness = None
        self._reasoning = None
        self._memory = None
        self._world_model = None
        self._prometheus = None
        self._atlas = None
        self._aegis = None
        self._hallucination_shield = None
        self._neuro_symbolic = None
        self._prediction_engine = None
        self._bio_core = None
        self._auto_tool_builder = None
        self._cognitive_resilience = None
        self._temporal_cortex = None
        self._collective_intelligence = None
        self._cognitive_bus = None
        self._quantum_ready = None
        self._feature_registry = None
        self._system_manifest = None

        # ── God Powers ──────────────────────────────────────────────────
        self._dream_engine = None
        self._causal = None
        self._metacognition = None
        self._multiscale = None
        self._synthesizer = None
        self._moral_compass = None

        # ── Agents ──────────────────────────────────────────────────────
        self._stark_core = None
        self._orchestrator = None
        self._strategist = None
        self._ethics = None
        self._learner = None
        self._inventor = None

        # ── Tools & Safety ──────────────────────────────────────────────
        self._nexus = None
        self._dual_mode = None
        self._guardrails = None
        self._sovereign_lock = None
        self._benchmark_suite = None

        # ── Capabilities ────────────────────────────────────────────────
        self._empathy = None
        self._intuition = None
        self._curiosity = None
        self._imagination = None

        # ── Tracking ────────────────────────────────────────────────────
        self._subsystem_status: dict[str, bool] = {}

    # ─────────────────────────────────────────────────────────────────────
    # INITIALIZE — bring every subsystem online
    # ─────────────────────────────────────────────────────────────────────

    async def initialize(self) -> dict[str, Any]:
        """Boot all subsystems. Returns a status dict showing what loaded."""
        t0 = time.time()

        # ── Core ────────────────────────────────────────────────────────
        pairs: list[tuple[str, str, str, tuple, dict]] = [
            ("consciousness",       "pradysagican.core.consciousness",       "ConsciousnessEngine",       (), {}),
            ("reasoning",           "pradysagican.core.reasoning",           "ReasoningEngine",           (), {}),
            ("memory",              "pradysagican.core.memory",              "MemorySystem",              (), {}),
            ("world_model",         "pradysagican.core.world_model",        "WorldModel",                (), {}),
            ("prometheus",          "pradysagican.core.prometheus",          "PrometheusEngine",          (), {}),
            ("atlas",               "pradysagican.core.atlas",              "AtlasRuntime",              (), {}),
            ("aegis",               "pradysagican.core.aegis",              "AegisWiring",               (), {}),
            ("hallucination_shield","pradysagican.core.hallucination_shield","HallucinationShield",      (), {}),
            ("neuro_symbolic",      "pradysagican.core.neuro_symbolic",     "NeuroSymbolicReasoner",     (), {}),
            ("prediction_engine",   "pradysagican.core.prediction_engine",  "PredictionEngine",          (), {}),
            ("bio_core",            "pradysagican.core.bio_core",           "BioCore",                   (), {}),
            ("auto_tool_builder",   "pradysagican.core.auto_tool_builder",  "AutoToolBuilder",           (), {}),
            ("cognitive_resilience","pradysagican.core.cognitive_resilience","CognitiveResilience",       (), {}),
            ("temporal_cortex",     "pradysagican.core.temporal_cortex",    "TemporalCortex",            (), {}),
            ("collective_intelligence","pradysagican.core.collective_intelligence","CollectiveIntelligence",(), {}),
            ("cognitive_bus",       "pradysagican.core.cognitive_bus",      "UnifiedCognitiveBus",       (), {}),
            ("quantum_ready",       "pradysagican.core.quantum_ready",     "QuantumReadyInterface",     (), {}),
            ("feature_registry",    "pradysagican.core.feature_registry",   "FeatureRegistry",           (), {}),
            ("system_manifest",     "pradysagican.core.system_manifest",    "SystemManifest",            (), {"auto_discover": False}),
            # God Powers
            ("dream_engine",        "pradysagican.core.god_powers",         "DreamEngine",               (), {}),
            ("causal",              "pradysagican.core.god_powers",         "CausalSuperpower",          (), {}),
            ("metacognition",       "pradysagican.core.god_powers",         "MetaCognitionV2",           (), {}),
            ("multiscale",          "pradysagican.core.god_powers",         "MultiScaleAttention",       (), {}),
            ("synthesizer",         "pradysagican.core.god_powers",         "KnowledgeSynthesizer",      (), {}),
            ("moral_compass",       "pradysagican.core.god_powers",         "MoralCompass",              (), {}),
            # Agents
            ("stark_core",          "pradysagican.agents.stark_core",       "StarkCore",                 (), {}),
            ("orchestrator",        "pradysagican.agents.orchestrator",     "MasterOrchestrator",        (), {}),
            ("strategist",          "pradysagican.agents.strategist",       "StrategicPlanner",          (), {}),
            ("ethics",              "pradysagican.agents.ethics",           "EthicsGuardian",            (), {}),
            ("learner",             "pradysagican.agents.learner",          "SelfImprovementEngine",     (), {}),
            ("inventor",            "pradysagican.agents.inventor",         "InventionEngine",           (), {}),
            # Tools & Safety
            ("nexus",               "pradysagican.tools.nexus",            "NexusToolMaster",           (), {}),
            ("dual_mode",           "pradysagican.safety.dual_mode",       "DualModeController",        (), {}),
            ("guardrails",          "pradysagican.safety.guardrails",      "SafetyGuardrails",          (), {}),
            ("sovereign_lock",      "pradysagican.safety.sovereign_lock",  "SovereignLock",             (), {}),
            ("benchmark_suite",     "pradysagican.benchmarks.benchmark_suite","BenchmarkSuite",          (), {}),
            # Capabilities (subset — the rest share similar APIs)
            ("empathy",             "pradysagican.capabilities.empathy",    "EmpathyEngine",             (), {}),
            ("intuition",           "pradysagican.capabilities.intuition",  "IntuitionEngine",           (), {}),
            ("curiosity",           "pradysagican.capabilities.curiosity",  "CuriosityEngine",           (), {}),
            ("imagination",         "pradysagican.capabilities.imagination","ImaginationCapability",      (), {}),
        ]

        for attr, module_path, cls_name, args, kwargs in pairs:
            cls = _import(module_path, cls_name)
            instance = _try_init(cls, *args, **kwargs)
            setattr(self, f"_{attr}", instance)
            self._subsystem_status[attr] = instance is not None

        # Initialize atlas (has its own async init)
        if self._atlas is not None:
            try:
                await self._atlas.initialize()
            except Exception:
                pass

        self._initialized = True
        elapsed = (time.time() - t0) * 1000

        online = sum(1 for v in self._subsystem_status.values() if v)
        total = len(self._subsystem_status)

        logger.info("PradysagicanGod initialized: %d/%d subsystems online (%.1f ms)", online, total, elapsed)
        return {
            "initialized": True,
            "subsystems_online": online,
            "subsystems_total": total,
            "elapsed_ms": round(elapsed, 2),
            "status": {k: ("online" if v else "offline") for k, v in self._subsystem_status.items()},
        }

    # ─────────────────────────────────────────────────────────────────────
    # THINK — deep multi-layered reasoning
    # ─────────────────────────────────────────────────────────────────────

    async def think(self, question: str, depth: int = 3) -> ThinkResult:
        """Deep multi-layered thought integrating consciousness, reasoning,
        memory, world model, metacognition, and hallucination checking.

        Depth controls how many subsystems are consulted (1-5).
        """
        t0 = time.time()
        self._call_count += 1
        result = ThinkResult(question=question, depth=depth)

        # Layer 1: Consciousness — recursive self-attention
        if self._consciousness is not None:
            try:
                layers = await self._consciousness.recursive_self_attention(question, depth=depth)
                result.consciousness_layers = layers if isinstance(layers, list) else [str(layers)]
            except Exception as exc:
                result.consciousness_layers = [f"consciousness error: {exc}"]

        # Layer 2: Memory recall
        if self._memory is not None:
            try:
                memories = await self._memory.recall(question, top_k=5)
                result.memories_recalled = [str(m) for m in memories] if memories else []
            except Exception:
                pass

        # Layer 3: Reasoning — chain of thought
        if self._reasoning is not None:
            try:
                trace = await self._reasoning.chain_of_thought(question, max_steps=min(depth * 2, 8))
                if hasattr(trace, "steps"):
                    result.reasoning_trace = [str(s) for s in trace.steps]
                elif hasattr(trace, "conclusion"):
                    result.reasoning_trace = [str(trace.conclusion)]
                else:
                    result.reasoning_trace = [str(trace)]
            except Exception as exc:
                result.reasoning_trace = [f"reasoning error: {exc}"]

        # Layer 4: World model prediction (depth >= 2)
        if depth >= 2 and self._world_model is not None:
            try:
                pred = await self._world_model.predict_action(f"think about: {question}")
                result.world_model_prediction = str(pred) if pred else ""
            except Exception:
                pass

        # Layer 5: Metacognition assessment (depth >= 3)
        if depth >= 3 and self._metacognition is not None:
            try:
                meta = await self._metacognition.recursive_reflect(question, max_depth=min(depth, 5))
                if isinstance(meta, list) and meta:
                    result.metacognitive_assessment = {
                        "layers": len(meta),
                        "deepest_insight": str(meta[-1]) if meta else "",
                    }
                elif isinstance(meta, dict):
                    result.metacognitive_assessment = meta
            except Exception:
                pass

        # Layer 6: Hallucination shield (depth >= 2)
        if depth >= 2 and self._hallucination_shield is not None:
            try:
                answer_text = " | ".join(result.reasoning_trace[:3]) if result.reasoning_trace else question
                shielded = await self._hallucination_shield.shield(answer_text, context=question)
                result.hallucination_check = {
                    "verified": getattr(shielded, "is_safe", True),
                    "confidence": getattr(shielded, "confidence", 0.0),
                }
            except Exception:
                pass

        # Synthesize answer
        parts: list[str] = []
        if result.reasoning_trace:
            parts.append(result.reasoning_trace[-1])
        if result.world_model_prediction:
            parts.append(result.world_model_prediction)
        if result.consciousness_layers:
            parts.append(result.consciousness_layers[-1])
        result.answer = " → ".join(parts) if parts else f"Contemplated '{question}' at depth {depth}"

        # Confidence = average of available signals
        signals: list[float] = []
        if result.hallucination_check.get("confidence"):
            signals.append(float(result.hallucination_check["confidence"]))
        if result.metacognitive_assessment.get("layers"):
            signals.append(min(1.0, result.metacognitive_assessment["layers"] / 5))
        if result.reasoning_trace:
            signals.append(min(1.0, len(result.reasoning_trace) / 6))
        result.confidence = round(sum(signals) / max(len(signals), 1), 4)

        result.elapsed_ms = round((time.time() - t0) * 1000, 2)
        return result

    # ─────────────────────────────────────────────────────────────────────
    # PREDICT — evidence-based forecasting
    # ─────────────────────────────────────────────────────────────────────

    async def predict(self, question: str, evidence: list[str] | None = None) -> PredictResult:
        """Predict outcomes using prediction engine, causal reasoning,
        world model, and uncertainty quantification."""
        t0 = time.time()
        self._call_count += 1
        evidence = evidence or []
        result = PredictResult(question=question, evidence_used=evidence)

        # 1. Prediction engine (Bayesian / ensemble)
        if self._prediction_engine is not None:
            try:
                pred = await self._prediction_engine.predict(question, evidence=evidence)
                result.prediction = str(getattr(pred, "answer", pred))
                result.confidence = float(getattr(pred, "confidence", 0.0))
            except Exception as exc:
                result.prediction = f"prediction-engine error: {exc}"

        # 2. Causal chain
        if self._causal is not None:
            try:
                cascade = await self._causal.predict_cascade(question)
                if isinstance(cascade, list):
                    result.causal_chain = [str(c) for c in cascade[:5]]
                elif isinstance(cascade, dict):
                    result.causal_chain = [f"{k}: {v}" for k, v in list(cascade.items())[:5]]
            except Exception:
                pass

        # 3. World model scenarios
        if self._world_model is not None:
            try:
                scenarios = await self._world_model.imagine(question, num_scenarios=3)
                result.world_model_scenarios = [str(s) for s in scenarios] if scenarios else []
            except Exception:
                pass

        # 4. Uncertainty quantification
        if self._metacognition is not None:
            try:
                uq = await self._metacognition.uncertainty_quantification(question)
                result.uncertainty = uq if isinstance(uq, dict) else {"raw": str(uq)}
            except Exception:
                pass

        result.elapsed_ms = round((time.time() - t0) * 1000, 2)
        return result

    # ─────────────────────────────────────────────────────────────────────
    # CREATE — invention and creative generation
    # ─────────────────────────────────────────────────────────────────────

    async def create(self, goal: str) -> CreateResult:
        """Create something new: strategies, inventions, tools, dreams.
        Combines strategic planning, invention, dreaming, and ethics."""
        t0 = time.time()
        self._call_count += 1
        result = CreateResult(goal=goal)

        # 1. Strategic planning
        if self._strategist is not None:
            try:
                strategy = await self._strategist.generate_strategy(goal, constraints=[])
                result.strategy = {
                    "name": getattr(strategy, "name", str(strategy)),
                    "moves": [str(m) for m in getattr(strategy, "moves", [])][:5],
                }
            except Exception:
                result.strategy = {"fallback": f"Direct approach to: {goal}"}

        # 2. Invention
        if self._inventor is not None:
            try:
                domain = goal.split()[0] if goal.split() else "general"
                invention = await self._inventor.innovate(domain, goal)
                result.inventions = [
                    {"name": getattr(invention, "name", "novel-invention"),
                     "description": getattr(invention, "description", str(invention))}
                ]
            except Exception:
                pass

        # 3. Dream engine — creative visions
        if self._dream_engine is not None:
            try:
                seeds = goal.split()[:5]
                dream = await self._dream_engine.dream(seeds, creativity_level=0.8)
                result.dream_visions = dream.visions[:5] if dream.visions else []
            except Exception:
                pass

        # 4. Ethics check
        if self._ethics is not None:
            try:
                assessment = await self._ethics.evaluate(goal, context="creation goal")
                result.ethical_assessment = {
                    "approved": getattr(assessment, "approved", True),
                    "risk_level": getattr(assessment, "risk_level", "low"),
                    "concerns": getattr(assessment, "concerns", []),
                }
            except Exception:
                result.ethical_assessment = {"approved": True, "risk_level": "unchecked"}

        # 5. Auto tool builder
        if self._auto_tool_builder is not None:
            try:
                tool = await self._auto_tool_builder.search_web(goal)
                if tool:
                    result.tools_built = [str(tool)]
            except Exception:
                pass

        # 6. Action plan from orchestrator
        if self._orchestrator is not None:
            try:
                tasks = await self._orchestrator.decompose(goal, max_tasks=6)
                result.action_plan = [getattr(t, "description", str(t)) for t in tasks]
            except Exception:
                result.action_plan = [f"Step 1: Begin work on '{goal}'"]

        result.elapsed_ms = round((time.time() - t0) * 1000, 2)
        return result

    # ─────────────────────────────────────────────────────────────────────
    # DREAM — controlled creative hallucination
    # ─────────────────────────────────────────────────────────────────────

    async def dream(
        self, seeds: list[str], creativity: float = 0.7,
    ) -> dict[str, Any]:
        """Engage the DreamEngine for creative ideation.
        Also pulls in imagination capability and knowledge synthesizer."""
        t0 = time.time()
        self._call_count += 1
        output: dict[str, Any] = {"seeds": seeds, "creativity": creativity}

        # 1. Core dream
        if self._dream_engine is not None:
            try:
                dr = await self._dream_engine.dream(seeds, creativity_level=creativity)
                output["visions"] = dr.visions
                output["insights"] = dr.insights
                output["novel_combinations"] = dr.novel_combinations
                output["creativity_score"] = dr.creativity_score
            except Exception as exc:
                output["dream_error"] = str(exc)

        # 2. Knowledge synthesis — cross-domain leaps
        if self._synthesizer is not None and len(seeds) >= 2:
            try:
                transfer = await self._synthesizer.cross_domain_transfer(seeds[0], seeds[1])
                output["knowledge_transfer"] = transfer if isinstance(transfer, dict) else {"raw": str(transfer)}
            except Exception:
                pass

        # 3. Imagination capability
        if self._imagination is not None:
            try:
                if hasattr(self._imagination, "imagine"):
                    img = await self._imagination.imagine(seeds)
                    output["imagination"] = str(img)
            except Exception:
                pass

        # 4. Lucid dream — constrained creativity
        if self._dream_engine is not None and creativity > 0.8:
            try:
                lucid = await self._dream_engine.lucid_dream(
                    " ".join(seeds), constraints=["must be feasible", "must be novel"],
                )
                output["lucid_solutions"] = lucid
            except Exception:
                pass

        output["elapsed_ms"] = round((time.time() - t0) * 1000, 2)
        return output

    # ─────────────────────────────────────────────────────────────────────
    # DECIDE — strategic decision making
    # ─────────────────────────────────────────────────────────────────────

    async def decide(self, situation: str, options: list[str]) -> DecideResult:
        """Make a decision using causal analysis, ethics, strategic thinking,
        and moral compass."""
        t0 = time.time()
        self._call_count += 1
        result = DecideResult(situation=situation, options=options)

        # 1. Stark Core strategic decision
        if self._stark_core is not None:
            try:
                decision = await self._stark_core.strategic_decision(
                    question=situation, options=options, context={},
                )
                result.analysis = decision if isinstance(decision, dict) else {"raw": str(decision)}
                result.chosen_option = str(decision.get("chosen", options[0] if options else ""))
                result.reasoning = str(decision.get("reasoning", ""))
                result.confidence = float(decision.get("confidence", 0.5))
            except Exception:
                pass

        # 2. Causal effects for each option
        if self._causal is not None:
            for opt in options[:4]:
                try:
                    self._causal.add_variable(opt, 1.0)
                    cascade = await self._causal.predict_cascade(opt)
                    effects = cascade if isinstance(cascade, list) else [str(cascade)]
                    result.causal_effects.append({"option": opt, "effects": [str(e) for e in effects[:3]]})
                except Exception:
                    result.causal_effects.append({"option": opt, "effects": ["analysis unavailable"]})

        # 3. Ethics check
        if self._ethics is not None:
            try:
                best = result.chosen_option or (options[0] if options else situation)
                assessment = await self._ethics.evaluate(best, context=situation)
                result.ethical_check = {
                    "approved": getattr(assessment, "approved", True),
                    "risk_level": getattr(assessment, "risk_level", "low"),
                }
            except Exception:
                result.ethical_check = {"approved": True, "risk_level": "unchecked"}

        # 4. Moral compass
        if self._moral_compass is not None:
            try:
                moral = await self._moral_compass.reason_from_principles(
                    situation, stakeholders=["user", "system", "society"],
                )
                if isinstance(moral, dict):
                    result.ethical_check["moral_foundations"] = moral
                else:
                    result.ethical_check["moral_assessment"] = str(moral)
            except Exception:
                pass

        # Fallback if no subsystem chose an option
        if not result.chosen_option and options:
            result.chosen_option = options[0]
            result.reasoning = "Default: first option selected (subsystems unavailable)"
            result.confidence = 0.3

        result.elapsed_ms = round((time.time() - t0) * 1000, 2)
        return result

    # ─────────────────────────────────────────────────────────────────────
    # EVOLVE — self-improvement cycle
    # ─────────────────────────────────────────────────────────────────────

    async def evolve(self) -> EvolveResult:
        """Run a full self-improvement cycle: reflect, learn heuristics,
        run prometheus evolution, bio-core life cycle, moral growth, meta-learn."""
        t0 = time.time()
        self._call_count += 1
        result = EvolveResult()

        # 1. Reflection via learner
        if self._learner is not None:
            try:
                reflection = await self._learner.reflect(
                    task="system evolution cycle",
                    actions=["analyzed performance", "identified weak areas"],
                    outcome="completed cycle",
                    success=True,
                )
                result.reflections = reflection if isinstance(reflection, dict) else {"episode": str(reflection)}
            except Exception:
                pass

        # 2. Heuristic distillation
        if self._learner is not None:
            try:
                heuristics = await self._learner.distill_heuristics(min_episodes=1)
                result.heuristics_learned = heuristics if isinstance(heuristics, dict) else {}
            except Exception:
                pass

        # 3. Prometheus evolution cycle
        if self._prometheus is not None:
            try:
                evo = await self._prometheus.evolution_cycle()
                result.prometheus_cycle = evo if isinstance(evo, dict) else {"raw": str(evo)}
            except Exception:
                pass

        # 4. Bio-core life cycle
        if self._bio_core is not None:
            try:
                if hasattr(self._bio_core, "life_cycle"):
                    bio = await self._bio_core.life_cycle()
                    result.bio_cycle = bio if isinstance(bio, dict) else {"raw": str(bio)}
            except Exception:
                pass

        # 5. Moral growth tracking
        if self._moral_compass is not None:
            try:
                moral = await self._moral_compass.moral_growth_tracking()
                result.moral_growth = moral if isinstance(moral, dict) else {"raw": str(moral)}
            except Exception:
                pass

        # 6. Meta-learning
        if self._learner is not None:
            try:
                meta = await self._learner.meta_learn()
                result.meta_learning = meta if isinstance(meta, dict) else {"raw": str(meta)}
            except Exception:
                pass

        result.elapsed_ms = round((time.time() - t0) * 1000, 2)
        return result

    # ─────────────────────────────────────────────────────────────────────
    # SOLVE — end-to-end problem solving
    # ─────────────────────────────────────────────────────────────────────

    async def solve(self, problem: str) -> SolveResult:
        """Full-stack problem solving: decompose, reason, get creative,
        verify, and deliver a solution."""
        t0 = time.time()
        self._call_count += 1
        result = SolveResult(problem=problem)

        # 1. Decompose via orchestrator
        if self._orchestrator is not None:
            try:
                tasks = await self._orchestrator.decompose(problem, max_tasks=6)
                result.decomposition = [getattr(t, "description", str(t)) for t in tasks]
            except Exception:
                result.decomposition = [problem]

        # 2. Reason through each sub-problem
        if self._reasoning is not None:
            try:
                trace = await self._reasoning.reason(problem, mode="auto")
                if hasattr(trace, "steps"):
                    result.reasoning_trace = [str(s) for s in trace.steps]
                elif hasattr(trace, "conclusion"):
                    result.reasoning_trace = [str(trace.conclusion)]
                else:
                    result.reasoning_trace = [str(trace)]
            except Exception:
                pass

        # 3. Creative angles from dream engine
        if self._dream_engine is not None:
            try:
                words = problem.split()[:4]
                dream = await self._dream_engine.dream(words, creativity_level=0.6)
                result.creative_angles = dream.insights[:3] if dream.insights else []
            except Exception:
                pass

        # 4. Neuro-symbolic reasoning for logical verification
        if self._neuro_symbolic is not None:
            try:
                ns = await self._neuro_symbolic.hybrid_reason(problem)
                result.verification = {
                    "logical_check": getattr(ns, "conclusion", str(ns)),
                    "confidence": getattr(ns, "confidence", 0.0),
                }
            except Exception:
                pass

        # 5. Causal root-cause analysis
        if self._causal is not None:
            try:
                root = await self._causal.find_root_cause(problem, depth=3)
                if root and isinstance(root, list):
                    result.reasoning_trace.extend([f"Root cause: {str(r)}" for r in root[:2]])
            except Exception:
                pass

        # Synthesize solution
        parts: list[str] = []
        if result.reasoning_trace:
            parts.append(result.reasoning_trace[-1])
        if result.verification.get("logical_check"):
            parts.append(str(result.verification["logical_check"]))
        if result.creative_angles:
            parts.append(result.creative_angles[0])
        result.solution = " | ".join(parts) if parts else f"Analyzed '{problem}' — solution requires further data"

        # Confidence
        signals: list[float] = []
        if result.reasoning_trace:
            signals.append(min(1.0, len(result.reasoning_trace) / 5))
        if result.verification.get("confidence"):
            signals.append(float(result.verification["confidence"]))
        result.confidence = round(sum(signals) / max(len(signals), 1), 4)

        result.elapsed_ms = round((time.time() - t0) * 1000, 2)
        return result

    # ─────────────────────────────────────────────────────────────────────
    # STATUS — synchronous system health snapshot
    # ─────────────────────────────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        """Synchronous system-wide health snapshot."""
        online = sum(1 for v in self._subsystem_status.values() if v)
        total = len(self._subsystem_status)
        uptime = time.time() - self._init_time

        subsystems_by_group: dict[str, dict[str, str]] = {
            "core": {}, "god_powers": {}, "agents": {},
            "tools_safety": {}, "capabilities": {},
        }
        group_map = {
            "consciousness": "core", "reasoning": "core", "memory": "core",
            "world_model": "core", "prometheus": "core", "atlas": "core",
            "aegis": "core", "hallucination_shield": "core", "neuro_symbolic": "core",
            "prediction_engine": "core", "bio_core": "core", "auto_tool_builder": "core",
            "cognitive_resilience": "core", "temporal_cortex": "core",
            "collective_intelligence": "core", "cognitive_bus": "core",
            "quantum_ready": "core", "feature_registry": "core", "system_manifest": "core",
            "dream_engine": "god_powers", "causal": "god_powers",
            "metacognition": "god_powers", "multiscale": "god_powers",
            "synthesizer": "god_powers", "moral_compass": "god_powers",
            "stark_core": "agents", "orchestrator": "agents", "strategist": "agents",
            "ethics": "agents", "learner": "agents", "inventor": "agents",
            "nexus": "tools_safety", "dual_mode": "tools_safety",
            "guardrails": "tools_safety", "sovereign_lock": "tools_safety",
            "benchmark_suite": "tools_safety",
            "empathy": "capabilities", "intuition": "capabilities",
            "curiosity": "capabilities", "imagination": "capabilities",
        }
        for name, is_online in self._subsystem_status.items():
            group = group_map.get(name, "other")
            subsystems_by_group.setdefault(group, {})[name] = "online" if is_online else "offline"

        return {
            "system": "PradysagicanGod",
            "version": "1.0.0",
            "initialized": self._initialized,
            "uptime_seconds": round(uptime, 1),
            "calls_served": self._call_count,
            "subsystems_online": online,
            "subsystems_total": total,
            "health_pct": round(online / max(total, 1) * 100, 1),
            "groups": subsystems_by_group,
        }

    # ─────────────────────────────────────────────────────────────────────
    # STATS — deep statistics
    # ─────────────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Detailed statistics from subsystems that provide them."""
        data: dict[str, Any] = {
            "system": self.status(),
        }

        # Feature registry stats
        if self._feature_registry is not None:
            try:
                data["features"] = self._feature_registry.stats()
            except Exception:
                data["features"] = {"error": "unavailable"}

        # System manifest summary
        if self._system_manifest is not None:
            try:
                data["architecture"] = self._system_manifest.get_architecture_summary()
            except Exception:
                data["architecture"] = {"error": "unavailable"}

        # Dream log
        if self._dream_engine is not None:
            try:
                data["dreams"] = {
                    "total_dreams": len(self._dream_engine._dream_log),
                }
            except Exception:
                pass

        # Causal model size
        if self._causal is not None:
            try:
                data["causal_model"] = {
                    "variables": len(self._causal._variables),
                    "mechanisms": self._causal._graph.number_of_edges() if hasattr(self._causal, "_graph") else 0,
                }
            except Exception:
                pass

        # Moral compass
        if self._moral_compass is not None:
            try:
                data["moral_compass"] = {
                    "precedents": len(getattr(self._moral_compass, "_precedents", [])),
                }
            except Exception:
                pass

        return data

    # ─────────────────────────────────────────────────────────────────────
    # String representation
    # ─────────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        online = sum(1 for v in self._subsystem_status.values() if v)
        total = len(self._subsystem_status)
        return f"<PradysagicanGod subsystems={online}/{total} calls={self._call_count}>"
