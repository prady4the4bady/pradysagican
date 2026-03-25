"""God-layer invented tools registry (151 synthesized tools)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class InventedToolSpec:
    tool_id: str
    tool_name: str
    system: str
    domain: str
    maturity: str
    description: str


SYSTEM_DEFINITIONS: list[dict[str, object]] = [
    {
        "system": "SOMNIUM",
        "domain": "Biological Cognition",
        "target": 28,
        "tools": [
            ("SomniumCycle", "Sleep-wake state machine for wake/NREM/REM intelligence."),
            ("DualStoreADM", "Dual episodic-semantic active dreaming memory store."),
            ("ConsolidationScheduler", "NREM window multiplexer for consolidation timing."),
            ("DreamerProcess", "Background counterfactual replay and insight extraction."),
            ("NightlyInsightReport", "Structured post-sleep learning report."),
            ("SleepDeprivationDetector", "Awake-duration risk monitor and emergency sleep trigger."),
            ("CounterfactualVerifier", "Rule pressure-testing before semantic commit."),
            ("WakePhaseBuffer", "High-fidelity wake trace recorder."),
            ("REMRemixer", "Creative recombination of knowledge clusters."),
            ("SWSRuleCompressor", "Slow-wave compression of episodic traces."),
        ],
    },
    {
        "system": "DRIFT",
        "domain": "Identity and Retrieval",
        "target": 12,
        "tools": [
            ("DriftRetrievalPipeline", "N-stage retrieval and filtering pipeline."),
            ("PerMemoryQLearning", "Bandit value learning for memory utility."),
            ("TopologicCognitiveFingerprint", "Graph-structure identity signature."),
            ("RejectionLogIdentity", "Identity by consistent rejection behavior."),
            ("PredictiveCodingRetrieval", "Prediction-error retrieval adaptation."),
            ("SpringDamperMood", "Mood dynamics as spring-damper physical process."),
            ("StageWeightBandit", "Stage-level adaptive weighting policy."),
            ("IdentityAttestor", "Cryptographically signed identity snapshots."),
            ("CognitiveFingerprintGenerator", "Graph-structure continuity fingerprint."),
            ("IdentityDriftMonitor", "Identity drift monitor across sessions."),
            ("AttestableIdentityChain", "Append-only cryptographic identity chain."),
            ("RejectionPatternAnalyzer", "Negative-identity behavior signature."),
        ],
    },
    {
        "system": "AMORY",
        "domain": "Narrative Memory",
        "target": 8,
        "tools": [
            ("EpisodicNarrativeBuilder", "Story-arc memory construction from events."),
            ("MomentumAwareConsolidator", "Narrative-thread-sensitive consolidation."),
            ("SemanticSemantizer", "Peripheral fact semanticization into stable memory."),
            ("CoherenceDrivenRetriever", "Narrative coherence retrieval strategy."),
            ("NarrativeContextProtocol", "Layered narrative context export format."),
            ("StoryThreadIndexer", "Thread-level indexing for episodic arcs."),
        ],
    },
    {
        "system": "SOMATIC",
        "domain": "Affective Decisioning",
        "target": 9,
        "tools": [
            ("SomaticMarkerEngine", "Valence prefilter before deep reasoning."),
            ("ValenceMemory", "Situation-to-valence associative memory."),
            ("AffectModulatedSearch", "Arousal-conditioned retrieval strategy."),
            ("EmotionTaggedMemory", "Valence/arousal-tagged memory store."),
            ("GutCheckGate", "Fast bypass gate for strong somatic signals."),
            ("EmotionSelectorNode", "Emotion-aware symbolic task ordering."),
            ("AffectiveRiskScorer", "Risk scoring using somatic prior."),
        ],
    },
    {
        "system": "MORPHAGENT",
        "domain": "Adaptive Multi-Agent",
        "target": 12,
        "tools": [
            ("DynamicProfileMechanism", "Self-evolving role and expertise profiles."),
            ("WarmUpPhaseOptimizer", "Pre-task profile calibration drills."),
            ("TaskExecutionAdapter", "Live profile adaptation during tasks."),
            ("ComplementarityScorer", "Profile diversity and overlap control."),
            ("ProfileEvolutionLog", "Longitudinal profile drift history."),
            ("NicheBalancer", "Ecological niche balancing across team."),
            ("EvolutionaryCurriculumSwarm", "Fitness-weighted curriculum evolution."),
            ("SwarmConsensusDebater", "Weighted debate consensus engine."),
            ("EcologyDrivenRoleAssignment", "Niche-aware role allocation."),
            ("EmergentBehaviorDetector", "Emergence pattern detector."),
            ("SwarmMemoryECAN", "Economic attention and contribution credits."),
        ],
    },
    {
        "system": "TOPO_CARTOGRAPHER",
        "domain": "Topological Intelligence",
        "target": 10,
        "tools": [
            ("PersistentHomologyAnalyzer", "H0/H1/H2 shape metrics for reasoning graphs."),
            ("KnowledgeGapDetector", "Topological-hole detection in knowledge graph."),
            ("TopologicalLaplacian", "Geometry-sensitive topological operator."),
            ("BarcodeReasoningQualityMetric", "Barcode complexity scoring for chains."),
            ("ShapeOfKnowledgeVisualizer", "Human-readable topology projection."),
            ("TopologicalPruner", "Structure-preserving memory graph pruning."),
            ("SheafRetriever", "Sheaf-based retrieval across heterogeneous shards."),
            ("FiltrationPlanner", "Filtration strategy optimizer."),
        ],
    },
    {
        "system": "IMMUNE",
        "domain": "Self-Healing and Reliability",
        "target": 9,
        "tools": [
            ("ImmuneSystemKernel", "Detection-diagnosis-repair control plane."),
            ("AnomalyDetectionSwarm", "Consensus anomaly voting swarm."),
            ("AutoRunbookBuilder", "Self-growing repair runbook extraction."),
            ("ImmunologicalMemory", "Failure antibodies and rapid response memory."),
            ("PoisonResistanceLayer", "Byzantine-style repair vote hardening."),
            ("SelfHealingCodePatcher", "Patch synthesis from logs and symptoms."),
            ("EscalationOracle", "Meta escalation policy to human operator."),
            ("RepairConsensusEngine", "Thresholded autonomous repair approval."),
        ],
    },
    {
        "system": "FUTURE_SELF",
        "domain": "Temporal Self-Modeling",
        "target": 7,
        "tools": [
            ("FutureSelfSimulator", "Capability projection over future horizons."),
            ("TemporalSelfModel", "Structured self-growth state model."),
            ("FutureMemoryGenerator", "Synthetic future-memory planning cues."),
            ("RetrospectivenessOracle", "Backcast-derived learning extraction."),
            ("CapabilityTrajectoryPlanner", "Goal-path planning to target self."),
            ("TemporalConsultationBridge", "Future-self guidance interface."),
        ],
    },
    {
        "system": "QSR",
        "domain": "Quantum-Inspired Reasoning",
        "target": 6,
        "tools": [
            ("BeliefSuperpositionEngine", "Superposed hypothesis state maintenance."),
            ("QuantumContextEffectCorrector", "Order-effect correction pipeline."),
            ("WavefunctionCollapseDecider", "Decision-time collapse policy."),
            ("EntanglementDetector", "Coupled subproblem detector."),
            ("AmplitudeStabilizer", "Numerical stability for amplitudes."),
            ("InterferenceExplorer", "Constructive/destructive interference probe."),
        ],
    },
    {
        "system": "RGR",
        "domain": "Multi-Scale Abstraction",
        "target": 5,
        "tools": [
            ("RGFlowReasoner", "Renormalization flow abstraction controller."),
            ("IrrelevantOperatorRemover", "Scale-irrelevant detail eliminator."),
            ("FixedPointDetector", "Scale-invariant fixed-point detection."),
            ("ScaleHopper", "Compute-budget-conditioned scale selector."),
            ("UniversalityMapper", "Class-level problem family mapping."),
        ],
    },
    {
        "system": "TNAM",
        "domain": "Tensor Associative Memory",
        "target": 5,
        "tools": [
            ("MPSMemoryStore", "Matrix-product-state memory encoding."),
            ("MERAHierarchicalCompression", "MERA multi-scale memory compression."),
            ("BondDimensionAdaptor", "Dynamic bond-dimension shaping."),
            ("QuantumInspiredRetrieval", "Tensor contraction retrieval pipeline."),
            ("EntanglementAwareIndexer", "Association-strength indexing layer."),
        ],
    },
    {
        "system": "CPTE",
        "domain": "Constructal Pipeline Optimization",
        "target": 4,
        "tools": [
            ("PipelineTopologyEvolver", "Constructal optimization of tool graph."),
            ("FlowResistanceMinimizer", "Latency/failure resistance minimization."),
            ("DendriticToolRouter", "Log-depth dendritic routing."),
            ("TopologyStressTester", "Flow topology robustness validation."),
        ],
    },
    {
        "system": "MCO",
        "domain": "Metacognition",
        "target": 8,
        "tools": [
            ("CognitiveBiasDetector", "Bias pattern detector across chains."),
            ("EpistemicHumilityMeter", "Confidence-accuracy calibration meter."),
            ("MetaCognitiveSwitcher", "Reasoning-mode switching controller."),
            ("CognitiveLoadEstimator", "Task load and resource balancing."),
            ("ImpasseNavigator", "Structured escape protocol."),
            ("TransferLearningDetector", "Cross-domain isomorphism detector."),
            ("KnowingWhatYouDontKnowEngine", "Proactive unknowns map."),
            ("MetaTraceAuditor", "Meta-level reasoning quality auditor."),
        ],
    },
    {
        "system": "NCE",
        "domain": "Narrative Cognition",
        "target": 6,
        "tools": [
            ("StorySchemaPlanner", "Story-schema-first task planner."),
            ("CharacterizedSubAgents", "Narrative role assignment for agents."),
            ("NarrativeConsistencyChecker", "Long-horizon contradiction detector."),
            ("StoryArcMemory", "Arc-level persistent memory structure."),
            ("DramaticTensionMeter", "Criticality-sensitive compute allocator."),
            ("NarrativePhaseRouter", "Reasoning mode by story phase."),
        ],
    },
    {
        "system": "SIIL",
        "domain": "Substrate Independence",
        "target": 5,
        "tools": [
            ("CognitionTranspiler", "Cross-substrate cognition IR compiler."),
            ("HybridSubstrateOrchestrator", "Operation-to-substrate router."),
            ("EnergyBudgetAllocation", "Energy-aware workload planner."),
            ("SubstrateFailover", "Fallback continuity manager."),
            ("SubstrateCapabilityProbe", "Runtime substrate capability scanner."),
        ],
    },
    {
        "system": "OMEGA_SELF_MODEL",
        "domain": "Recursive Self-Awareness",
        "target": 6,
        "tools": [
            ("AgentSelfModel", "Structured self-capability representation."),
            ("SelfModelUpdater", "Prediction-vs-outcome self-model updater."),
            ("HumilityCalibrator", "Conservative self-claim regulator."),
            ("ExistentialStabilityModule", "Self-consistency guard and repair."),
            ("CapabilityBoundEstimator", "Formal domain bound checker."),
            ("SelfCoherenceReporter", "Periodic coherence telemetry."),
        ],
    },
    {
        "system": "UEE",
        "domain": "Empathic Communication",
        "target": 6,
        "tools": [
            ("CognitiveStateInferrer", "User cognition inference from interaction."),
            ("ExpertiseAdaptor", "Depth/style adaptation by expertise."),
            ("FrustrationDetector", "Friction and frustration signal detector."),
            ("GroundingChecker", "Comprehension checkpoint engine."),
            ("CrossCulturalAdaptor", "Culture-sensitive communication adapter."),
            ("EmpathyFeedbackLoop", "Adaptive empathy strategy update."),
        ],
    },
    {
        "system": "TGA",
        "domain": "Transcendent Goal Architecture",
        "target": 5,
        "tools": [
            ("SevenLevelGoalHierarchy", "Token-to-existential layered goal stack."),
            ("GoalCoherenceVerifier", "Cross-level action-goal consistency check."),
            ("GoalAbstractionLift", "Pattern-to-goal proposal mechanism."),
            ("TemporalDiscountingCalibrator", "Short/long horizon balancing."),
            ("GoalConflictResolver", "Conflict trade-off and resolution engine."),
        ],
    },
]


def _placeholder_tools(system: str, count: int) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for i in range(1, count + 1):
        items.append(
            (
                f"{system}Extension{i:02d}",
                f"{system} extension slot {i:02d} for future implementation.",
            )
        )
    return items


def _build_registry() -> list[InventedToolSpec]:
    specs: list[InventedToolSpec] = []
    counter = 1
    for definition in SYSTEM_DEFINITIONS:
        system = str(definition["system"])
        domain = str(definition["domain"])
        target = int(definition["target"])
        tools = list(definition["tools"])  # type: ignore[assignment]
        if len(tools) < target:
            tools.extend(_placeholder_tools(system, target - len(tools)))
        elif len(tools) > target:
            tools = tools[:target]
        for idx, (name, description) in enumerate(tools):
            specs.append(
                InventedToolSpec(
                    tool_id=f"GL{counter:03d}",
                    tool_name=name,
                    system=system,
                    domain=domain,
                    maturity="prototype" if idx < len(definition["tools"]) else "planned",
                    description=description,
                )
            )
            counter += 1
    return specs


INVENTED_TOOL_SPECS: tuple[InventedToolSpec, ...] = tuple(_build_registry())
TOTAL_INVENTED_TOOLS = len(INVENTED_TOOL_SPECS)


def inventory_summary() -> dict[str, object]:
    by_system: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    maturity: dict[str, int] = {"prototype": 0, "planned": 0}
    for spec in INVENTED_TOOL_SPECS:
        by_system[spec.system] = by_system.get(spec.system, 0) + 1
        by_domain[spec.domain] = by_domain.get(spec.domain, 0) + 1
        maturity[spec.maturity] = maturity.get(spec.maturity, 0) + 1
    return {
        "total_tools": TOTAL_INVENTED_TOOLS,
        "systems": len(by_system),
        "domains": len(by_domain),
        "by_system": by_system,
        "by_domain": by_domain,
        "maturity": maturity,
    }


def tools_for_system(system: str) -> list[InventedToolSpec]:
    return [spec for spec in INVENTED_TOOL_SPECS if spec.system == system]


def iter_tool_names() -> Iterable[str]:
    for spec in INVENTED_TOOL_SPECS:
        yield spec.tool_name
