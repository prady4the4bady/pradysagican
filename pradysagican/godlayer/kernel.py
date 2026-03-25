"""Executable kernel for the God-layer invention stack."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pradysagican.godlayer.registry import INVENTED_TOOL_SPECS, TOTAL_INVENTED_TOOLS, inventory_summary
from pradysagican.godlayer.systems_bio import (
    AttestableIdentityChain,
    CapabilityTrajectoryPlanner,
    CognitiveFingerprintGenerator,
    CoherenceDrivenRetriever,
    DriftRetrievalPipeline,
    EmergentBehaviorDetector,
    EpisodicNarrativeBuilder,
    ImmuneSystemKernel,
    KnowledgeGapDetector,
    PersistentHomologyAnalyzer,
    RetrospectivenessOracle,
    SomaticMarkerEngine,
    SomniumCycle,
    SpringDamperMood,
    SwarmConsensusDebater,
    TopologicCognitiveFingerprint,
    FutureSelfSimulator,
    FutureMemoryGenerator,
    TemporalSelfModel,
)
from pradysagican.godlayer.systems_cognition import (
    BeliefSuperpositionEngine,
    CognitiveBiasDetector,
    DramaticTensionMeter,
    GoalAbstractionLift,
    GoalCoherenceVerifier,
    GoalConflictResolver,
    MetaCognitiveSwitcher,
    SevenLevelGoalHierarchy,
    TemporalDiscountingCalibrator,
    WavefunctionCollapseDecider,
)


@dataclass
class GodLayerKernel:
    """Central runtime for invented God-layer systems."""

    somnium: SomniumCycle = field(default_factory=SomniumCycle)
    drift: DriftRetrievalPipeline = field(default_factory=DriftRetrievalPipeline)
    narrative_builder: EpisodicNarrativeBuilder = field(default_factory=EpisodicNarrativeBuilder)
    coherence_retriever: CoherenceDrivenRetriever = field(default_factory=CoherenceDrivenRetriever)
    somatic: SomaticMarkerEngine = field(default_factory=SomaticMarkerEngine)
    mood: SpringDamperMood = field(default_factory=SpringDamperMood)
    topology: PersistentHomologyAnalyzer = field(default_factory=PersistentHomologyAnalyzer)
    gap_detector: KnowledgeGapDetector = field(default_factory=KnowledgeGapDetector)
    immune: ImmuneSystemKernel = field(default_factory=ImmuneSystemKernel)
    future_sim: FutureSelfSimulator = field(default_factory=FutureSelfSimulator)
    temporal_self: TemporalSelfModel = field(default_factory=TemporalSelfModel)
    future_memory: FutureMemoryGenerator = field(default_factory=FutureMemoryGenerator)
    trajectory: CapabilityTrajectoryPlanner = field(default_factory=CapabilityTrajectoryPlanner)
    retrospective: RetrospectivenessOracle = field(default_factory=RetrospectivenessOracle)
    cognitive_fp: CognitiveFingerprintGenerator = field(default_factory=CognitiveFingerprintGenerator)
    topo_fp: TopologicCognitiveFingerprint = field(default_factory=TopologicCognitiveFingerprint)
    identity_chain: AttestableIdentityChain = field(default_factory=AttestableIdentityChain)
    swarm_consensus: SwarmConsensusDebater = field(default_factory=SwarmConsensusDebater)
    emergent_detector: EmergentBehaviorDetector = field(default_factory=EmergentBehaviorDetector)
    superposition: BeliefSuperpositionEngine = field(default_factory=BeliefSuperpositionEngine)
    collapse: WavefunctionCollapseDecider = field(default_factory=WavefunctionCollapseDecider)
    bias_detector: CognitiveBiasDetector = field(default_factory=CognitiveBiasDetector)
    mode_switcher: MetaCognitiveSwitcher = field(default_factory=MetaCognitiveSwitcher)
    tension_meter: DramaticTensionMeter = field(default_factory=DramaticTensionMeter)
    goals: SevenLevelGoalHierarchy = field(default_factory=SevenLevelGoalHierarchy)
    coherence: GoalCoherenceVerifier = field(default_factory=GoalCoherenceVerifier)
    goal_lift: GoalAbstractionLift = field(default_factory=GoalAbstractionLift)
    goal_discount: TemporalDiscountingCalibrator = field(default_factory=TemporalDiscountingCalibrator)
    goal_conflicts: GoalConflictResolver = field(default_factory=GoalConflictResolver)

    def inventory(self) -> dict[str, Any]:
        summary = inventory_summary()
        summary["first_10_tools"] = [spec.tool_name for spec in INVENTED_TOOL_SPECS[:10]]
        return summary

    def status(self) -> dict[str, Any]:
        return {
            "inventory": self.inventory(),
            "self_model_latest": self.temporal_self.latest(),
            "identity_chain_length": len(self.identity_chain.chain()),
            "total_tools": TOTAL_INVENTED_TOOLS,
        }

    def run_somnium_cycle(
        self,
        events: list[dict[str, Any]],
        awake_hours: float,
        local_hour: int,
        idle_minutes: int = 0,
    ) -> dict[str, Any]:
        result = self.somnium.run(
            events=events,
            awake_hours=awake_hours,
            local_hour=local_hour,
            idle_minutes=idle_minutes,
        )
        self.temporal_self.update(
            {"somnium_phase": result["phase"], "semantic_rules": result["semantic_rules"], "sleep_risk": result["sleep_risk"]["risk"]}
        )
        return result

    def run_drift_retrieval(self, query: str, memories: list[dict[str, Any]], limit: int = 5) -> dict[str, Any]:
        retrieved = self.drift.retrieve(query=query, memories=memories, limit=limit)
        return {"query": query, "retrieved": retrieved, "pipeline_stages": len(self.drift.STAGES)}

    def run_topology_scan(self, nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, Any]:
        homology = self.topology.analyze(nodes=nodes, edges=edges)
        holes = self.gap_detector.detect(nodes=nodes, edges=edges)
        return {"homology": homology, "holes": holes}

    def run_immune_check(
        self,
        anomaly_signature: str,
        detector_signals: list[bool],
        complexity: float,
        impact: float,
        uncertainty: float,
    ) -> dict[str, Any]:
        return self.immune.handle(
            anomaly_signature=anomaly_signature,
            detector_signals=detector_signals,
            complexity=complexity,
            impact=impact,
            uncertainty=uncertainty,
        )

    def project_future(self, current_scores: dict[str, float], daily_improvement: float, days: int, intent: str) -> dict[str, Any]:
        projection = self.future_sim.project(current_scores=current_scores, daily_improvement=daily_improvement, days=days)
        memory = self.future_memory.generate(horizon_days=days, intent=intent)
        priorities = self.trajectory.prioritize(current=current_scores, target=projection, top_n=5)
        return {"projection": projection, "future_memory": memory, "priorities": priorities}

    def metacognitive_scan(
        self,
        reasoning_text: str,
        confidence_outcomes: list[tuple[float, bool]],
        task_type: str,
        elapsed_seconds: float,
        uncertainty: float,
        impact: float,
        deadline_pressure: float,
    ) -> dict[str, Any]:
        biases = self.bias_detector.detect(reasoning_text)
        mode = self.mode_switcher.choose(task_type=task_type, elapsed_seconds=elapsed_seconds)
        tension = self.tension_meter.score(
            uncertainty=uncertainty,
            impact=impact,
            deadline_pressure=deadline_pressure,
        )
        return {
            "biases": biases,
            "recommended_mode": mode,
            "dramatic_tension": tension,
            "samples": len(confidence_outcomes),
        }

    def goal_alignment(self, action: str, option_scores: dict[str, float]) -> dict[str, Any]:
        coherent = self.coherence.verify(action=action, hierarchy=self.goals)
        weighted_choice = self.goal_conflicts.resolve(option_scores=option_scores)
        discounted = {
            "30d": self.goal_discount.weight(value=1.0, horizon_days=30),
            "180d": self.goal_discount.weight(value=1.0, horizon_days=180),
        }
        return {"coherent": coherent, "winner": weighted_choice["winner"], "discounted": discounted}

    def quantum_decide(self, amplitudes: dict[str, float]) -> dict[str, Any]:
        normalized = self.superposition.set_hypotheses(amplitudes)
        probs = self.superposition.probabilities()
        collapsed = self.collapse.collapse(probs)
        return {"normalized": normalized, "probabilities": probs, "decision": collapsed}

