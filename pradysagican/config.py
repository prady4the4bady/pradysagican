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
