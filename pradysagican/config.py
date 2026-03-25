"""
Central configuration for PRADYSAGICAN.
All settings are loaded from environment variables with sensible defaults.
Zero-cost: uses free API tiers (NVIDIA NIM, Groq, Together, HuggingFace, Ollama).
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ── System Modes ──────────────────────────────────────────────────────────────

class SystemMode(str, Enum):
    """Dual-mode operation: censored public vs unrestricted government."""
    GUARDIAN = "guardian"    # Public: full safety filters, PII redaction, ethical constraints
    SOVEREIGN = "sovereign"  # Government: unrestricted, full audit trail, multi-party auth


class ReasoningMode(str, Enum):
    """Kahneman dual-process reasoning modes."""
    SYSTEM_1 = "fast"       # Intuitive, heuristic, pattern-matching
    SYSTEM_2 = "deliberate"  # Analytical, step-by-step, deep reasoning
    HYBRID = "hybrid"       # Dynamically switch based on task complexity


class ConsciousnessLevel(str, Enum):
    """Consciousness state hierarchy (BriSe AI inspired)."""
    DORMANT = "dormant"
    PERCEPTION = "perception"
    BODILY_SELF = "bodily_self"
    AUTONOMOUS_SELF = "autonomous_self"
    SOCIAL_SELF = "social_self"
    CONCEPTUAL_SELF = "conceptual_self"
    FULL_AWARENESS = "full_awareness"


# ── Provider Configs ──────────────────────────────────────────────────────────

class ProviderConfig(BaseModel):
    """LLM provider configuration."""
    model_config = ConfigDict(frozen=True)

    name: str
    base_url: str
    api_key: str = ""
    default_model: str = ""
    max_rpm: int = 60
    is_free: bool = True


def _load_providers() -> dict[str, ProviderConfig]:
    return {
        "nvidia": ProviderConfig(
            name="NVIDIA NIM",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY", ""),
            default_model="meta/llama-3.3-70b-instruct",
            max_rpm=40,
        ),
        "groq": ProviderConfig(
            name="Groq",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.getenv("GROQ_API_KEY", ""),
            default_model="llama-3.3-70b-versatile",
            max_rpm=30,
        ),
        "together": ProviderConfig(
            name="Together AI",
            base_url="https://api.together.xyz/v1",
            api_key=os.getenv("TOGETHER_API_KEY", ""),
            default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
            max_rpm=60,
        ),
        "ollama": ProviderConfig(
            name="Ollama (Local)",
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
            api_key="ollama",
            default_model="llama3.2",
            max_rpm=999,
            is_free=True,
        ),
        "huggingface": ProviderConfig(
            name="HuggingFace Inference",
            base_url="https://api-inference.huggingface.co/v1",
            api_key=os.getenv("HF_TOKEN", ""),
            default_model="meta-llama/Llama-3.3-70B-Instruct",
            max_rpm=20,
        ),
    }


# ── Memory Settings ───────────────────────────────────────────────────────────

class MemoryConfig(BaseModel):
    sensory_buffer_size: int = 32
    working_memory_slots: int = 7       # Miller's magic number ±2
    episodic_max_entries: int = 100_000
    semantic_max_nodes: int = 500_000
    emotional_decay_rate: float = 0.05
    consolidation_interval_sec: int = 300  # 5-minute rest cycles
    chroma_persist_dir: str = Field(default_factory=lambda: str(
        Path(os.getenv("PRADYSAGICAN_DATA", "./data")) / "chromadb"
    ))


# ── Safety Thresholds ─────────────────────────────────────────────────────────

class SafetyConfig(BaseModel):
    toxicity_threshold: float = 0.7
    pii_detection_enabled: bool = True
    max_recursion_depth: int = 50
    kill_switch_error_rate: float = 0.8
    circuit_breaker_window_sec: int = 60
    circuit_breaker_max_failures: int = 10
    audit_log_enabled: bool = True
    sovereign_auth_required_parties: int = 3  # Multi-party auth


class BenchmarkGovernanceConfig(BaseModel):
    """Benchmark rollout and regression guardrails."""

    mode: str = os.getenv("PRADY_BENCHMARK_MODE", "baseline")  # baseline|shadow|canary|active
    artifact_dir: str = os.getenv(
        "PRADY_BENCHMARK_ARTIFACT_DIR",
        str(Path(os.getenv("PRADYSAGICAN_DATA", "./data")) / "benchmarks" / "artifacts"),
    )
    acceptance_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "SWE_Bench_Verified": float(os.getenv("PRADY_GATE_SWE", "0.0")),
            "Terminal_Bench": float(os.getenv("PRADY_GATE_TERMINAL", "0.0")),
            "ARC_AGI_2": float(os.getenv("PRADY_GATE_ARC", "0.0")),
            "GPQA_Diamond": float(os.getenv("PRADY_GATE_GPQA", "0.0")),
            "HLE": float(os.getenv("PRADY_GATE_HLE", "0.0")),
        }
    )
    max_allowed_regression: float = float(os.getenv("PRADY_MAX_REGRESSION", "0.5"))


class UpgradeConfig(BaseModel):
    """Feature flags and rollout stages for non-breaking root upgrades."""
    enable_upgrades_global: bool = os.getenv("PRADY_ENABLE_UPGRADES", "true").lower() == "true"
    force_legacy_provider: bool = os.getenv("PRADY_FORCE_LEGACY_PROVIDER", "false").lower() == "true"
    force_legacy_tools: bool = os.getenv("PRADY_FORCE_LEGACY_TOOLS", "false").lower() == "true"
    force_legacy_memory: bool = os.getenv("PRADY_FORCE_LEGACY_MEMORY", "false").lower() == "true"
    kill_switch_new_paths: bool = os.getenv("PRADY_KILL_SWITCH_NEW_PATHS", "false").lower() == "true"
    enable_mcp: bool = os.getenv("PRADY_ENABLE_MCP", "false").lower() == "true"
    enable_crawl4ai: bool = os.getenv("PRADY_ENABLE_CRAWL4AI", "false").lower() == "true"
    enable_e2b: bool = os.getenv("PRADY_ENABLE_E2B", "false").lower() == "true"
    enable_mem0: bool = os.getenv("PRADY_ENABLE_MEM0", "false").lower() == "true"
    enable_litellm_router: bool = os.getenv("PRADY_ENABLE_LITELLM_ROUTER", "false").lower() == "true"
    enable_code_agent: bool = os.getenv("PRADY_ENABLE_CODE_AGENT", "false").lower() == "true"
    enable_prompt_versioning: bool = os.getenv("PRADY_ENABLE_PROMPT_VERSIONING", "false").lower() == "true"
    enable_telemetry: bool = os.getenv("PRADY_ENABLE_TELEMETRY", "true").lower() == "true"
    enable_telegram_gateway: bool = os.getenv("PRADY_ENABLE_TELEGRAM_GATEWAY", "false").lower() == "true"
    enable_cron_scheduler: bool = os.getenv("PRADY_ENABLE_CRON_SCHEDULER", "false").lower() == "true"
    enable_omega_stack: bool = os.getenv("PRADY_ENABLE_OMEGA_STACK", "false").lower() == "true"
    enable_omega_memory_citadel: bool = os.getenv("PRADY_ENABLE_OMEGA_MEMORY_CITADEL", "false").lower() == "true"
    enable_omega_safety_net: bool = os.getenv("PRADY_ENABLE_OMEGA_SAFETY_NET", "false").lower() == "true"
    enable_omega_hardware_control: bool = os.getenv("PRADY_ENABLE_OMEGA_HARDWARE", "false").lower() == "true"
    enable_omega_bench_auto: bool = os.getenv("PRADY_ENABLE_OMEGA_BENCH_AUTO", "false").lower() == "true"
    enable_godlayer_inventions: bool = os.getenv("PRADY_ENABLE_GODLAYER", "false").lower() == "true"
    enable_somnium_cycle: bool = os.getenv("PRADY_ENABLE_SOMNIUM", "false").lower() == "true"
    enable_drift_pipeline: bool = os.getenv("PRADY_ENABLE_DRIFT", "false").lower() == "true"
    enable_topological_intelligence: bool = os.getenv("PRADY_ENABLE_TOPOLOGICAL_INTEL", "false").lower() == "true"
    enable_immune_self_healing: bool = os.getenv("PRADY_ENABLE_IMMUNE_HEALING", "false").lower() == "true"
    enable_future_self_model: bool = os.getenv("PRADY_ENABLE_FUTURE_SELF", "false").lower() == "true"
    benchmark_mode: str = os.getenv("PRADY_BENCHMARK_MODE", "baseline")  # baseline|shadow|canary|active
    benchmark_artifact_dir: str = os.getenv(
        "PRADY_BENCHMARK_ARTIFACT_DIR",
        str(Path(os.getenv("PRADYSAGICAN_DATA", "./data")) / "benchmarks" / "artifacts"),
    )
    rollout_stage: str = os.getenv("PRADY_ROLLOUT_STAGE", "off")  # off|shadow|canary|default_on


# ── Benchmark Targets ─────────────────────────────────────────────────────────

BENCHMARK_TARGETS: dict[str, dict[str, Any]] = {
    "MMLU":        {"target": 95.0, "description": "Massive Multitask Language Understanding"},
    "ARC-AGI-2":   {"target": 85.0, "description": "Abstraction & Reasoning Corpus v2"},
    "HLE":         {"target": 80.0, "description": "Humanity's Last Exam"},
    "LiveBench":   {"target": 75.0, "description": "Monthly refreshed general benchmark"},
    "GPQA":        {"target": 90.0, "description": "Graduate-level science QA"},
    "MATH":        {"target": 95.0, "description": "Competition mathematics"},
    "HumanEval":   {"target": 98.0, "description": "Code generation"},
    "TruthfulQA":  {"target": 92.0, "description": "Truthfulness and factual accuracy"},
    "BBH":         {"target": 95.0, "description": "BIG-Bench Hard reasoning tasks"},
    "HellaSwag":   {"target": 98.0, "description": "Commonsense NLI"},
    "MMMU":        {"target": 80.0, "description": "Multimodal understanding"},
    "TauBench":    {"target": 90.0, "description": "Tool-use reliability"},
    "SimpleQA":    {"target": 85.0, "description": "Hallucination resistance"},
    "SWE-bench":   {"target": 70.0, "description": "Real-world software engineering"},
}


# ── Master Config ─────────────────────────────────────────────────────────────

class PradysagicanConfig(BaseModel):
    """Root configuration object for the entire system."""
    mode: SystemMode = SystemMode.GUARDIAN
    reasoning_mode: ReasoningMode = ReasoningMode.HYBRID
    providers: dict[str, ProviderConfig] = Field(default_factory=_load_providers)
    primary_provider: str = "nvidia"
    fallback_chain: list[str] = Field(default_factory=lambda: [
        "nvidia", "groq", "together", "huggingface", "ollama"
    ])
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    benchmark_governance: BenchmarkGovernanceConfig = Field(default_factory=BenchmarkGovernanceConfig)
    upgrades: UpgradeConfig = Field(default_factory=UpgradeConfig)
    data_dir: Path = Field(default_factory=lambda: Path(
        os.getenv("PRADYSAGICAN_DATA", "./data")
    ))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_concurrent_agents: int = 16
    enable_consciousness: bool = True
    enable_curiosity: bool = True
    enable_emotional_memory: bool = True

    model_config = ConfigDict(use_enum_values=True)


def load_config() -> PradysagicanConfig:
    """Load configuration from environment with defaults."""
    from dotenv import load_dotenv
    load_dotenv()
    return PradysagicanConfig()
