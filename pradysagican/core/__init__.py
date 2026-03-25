"""Core engines: consciousness, reasoning, memory, world model, prometheus, atlas, aegis, temporal, resilience, quantum, collective, cognitive bus, neuro-symbolic, hallucination shield, bio core, prediction engine, auto tool builder, feature registry, system manifest, god powers."""
from pradysagican.core.consciousness import ConsciousnessEngine
from pradysagican.core.reasoning import ReasoningEngine
from pradysagican.core.memory import MemorySystem
from pradysagican.core.world_model import WorldModel
from pradysagican.core.prometheus import PrometheusEngine
from pradysagican.core.atlas import AtlasRuntime
from pradysagican.core.aegis import AegisWiring
from pradysagican.core.temporal_cortex import TemporalCortex, TemporalEvent, TimePoint, TimeInterval, TemporalRelation, EventStatus
from pradysagican.core.cognitive_resilience import CognitiveResilience, ExecutionTrace, Checkpoint, StepResult
from pradysagican.core.quantum_ready import QuantumReadyInterface, QuantumConfig, QuantumBackend, QuantumResult
from pradysagican.core.collective_intelligence import CollectiveIntelligence, PeerNode, KnowledgeShard, ConsensusProtocol, SwarmResult
from pradysagican.core.cognitive_bus import UnifiedCognitiveBus, CognitiveSignal, SignalType, CognitivePipeline, ModuleRegistry
from pradysagican.core.neuro_symbolic import NeuroSymbolicReasoner, KnowledgeBase, LogicalRule, Fact
from pradysagican.core.hallucination_shield import HallucinationShield, ConfidenceCalibrator, ClaimVerifier
from pradysagican.core.bio_core import BioCore, Homeostasis, SelfRepair, Metabolism, EvolutionaryAdaptation
from pradysagican.core.prediction_engine import PredictionEngine, BayesianPredictor, EnsemblePredictor, EnsembleMethod
from pradysagican.core.auto_tool_builder import AutoToolBuilder, WebConnector, ToolBlueprint, BuiltTool
from pradysagican.core.feature_registry import FeatureRegistry, FeatureCategory, Feature
from pradysagican.core.system_manifest import SystemManifest, ModuleInfo, ConnectionInfo
from pradysagican.core.prompt_registry import PromptRegistry, PromptVersion
from pradysagican.core.session_store import SessionStore
from pradysagican.core.memory_middleware import MemoryMiddleware
from pradysagican.core.god_powers import (
    DreamEngine, DreamResult, CausalSuperpower, CausalEffect,
    MetaCognitionV2, MetaCognitiveLayer, MultiScaleAttention,
    KnowledgeSynthesizer, SynthesizedInsight, MoralCompass, MoralAssessment,
)

# Phase 5: Evolution, Self-Reference, Learning, Autonomous
from pradysagican.core.evolution import (
    Validator, ValidationReport, ValidationDecision, BenchmarkResult, BenchmarkType,
    DGMArchive, Variant, VariantType, VariantMetrics, SamplingStrategy,
)
from pradysagican.core.self_ref import (
    SelfRefEditor, EditResult, Improvement, ImprovementType, CodeMetrics,
)
from pradysagican.core.learning import (
    AutoRL, FailureTrajectory, FailureEvent, FailureCategory, Principle, RetrievalResult,
)
from pradysagican.core.autonomous import (
    Heartbeat, HeartbeatPhase, ApprovalGate, ApprovalDecision, CycleMetrics, FailureQueueItem,
)

__all__ = [
    "ConsciousnessEngine", "ReasoningEngine", "MemorySystem", "WorldModel",
    "PrometheusEngine", "AtlasRuntime", "AegisWiring",
    # Temporal Cortex
    "TemporalCortex", "TemporalEvent", "TimePoint", "TimeInterval", "TemporalRelation", "EventStatus",
    # Cognitive Resilience
    "CognitiveResilience", "ExecutionTrace", "Checkpoint", "StepResult",
    # Quantum Ready
    "QuantumReadyInterface", "QuantumConfig", "QuantumBackend", "QuantumResult",
    # Collective Intelligence
    "CollectiveIntelligence", "PeerNode", "KnowledgeShard", "ConsensusProtocol", "SwarmResult",
    # Cognitive Bus
    "UnifiedCognitiveBus", "CognitiveSignal", "SignalType", "CognitivePipeline", "ModuleRegistry",
    # Neuro-Symbolic
    "NeuroSymbolicReasoner", "KnowledgeBase", "LogicalRule", "Fact",
    # Hallucination Shield
    "HallucinationShield", "ConfidenceCalibrator", "ClaimVerifier",
    # Bio Core
    "BioCore", "Homeostasis", "SelfRepair", "Metabolism", "EvolutionaryAdaptation",
    # Prediction Engine
    "PredictionEngine", "BayesianPredictor", "EnsemblePredictor", "EnsembleMethod",
    # Auto Tool Builder
    "AutoToolBuilder", "WebConnector", "ToolBlueprint", "BuiltTool",
    # Feature Registry
    "FeatureRegistry", "FeatureCategory", "Feature",
    # System Manifest
    "SystemManifest", "ModuleInfo", "ConnectionInfo",
    # Prompt + memory middleware
    "PromptRegistry", "PromptVersion", "SessionStore", "MemoryMiddleware",
    # God Powers
    "DreamEngine", "DreamResult", "CausalSuperpower", "CausalEffect",
    "MetaCognitionV2", "MetaCognitiveLayer", "MultiScaleAttention",
    "KnowledgeSynthesizer", "SynthesizedInsight", "MoralCompass", "MoralAssessment",
    # Phase 5: Evolution
    "Validator", "ValidationReport", "ValidationDecision", "BenchmarkResult", "BenchmarkType",
    "DGMArchive", "Variant", "VariantType", "VariantMetrics", "SamplingStrategy",
    # Phase 5: Self-Reference
    "SelfRefEditor", "EditResult", "Improvement", "ImprovementType", "CodeMetrics",
    # Phase 5: Learning
    "AutoRL", "FailureTrajectory", "FailureEvent", "FailureCategory", "Principle", "RetrievalResult",
    # Phase 5: Autonomous
    "Heartbeat", "HeartbeatPhase", "ApprovalGate", "ApprovalDecision", "CycleMetrics", "FailureQueueItem",
]
