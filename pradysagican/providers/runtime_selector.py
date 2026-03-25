"""Hardware-aware runtime selector for inference backends."""

from __future__ import annotations

import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeDecision:
    runtime: str
    reason: str


def select_runtime() -> RuntimeDecision:
    # NVIDIA path
    try:
        import torch  # type: ignore[import-not-found]
        if torch.cuda.is_available():
            return RuntimeDecision(runtime="vllm", reason="cuda_available")
    except Exception:
        pass

    # Apple Silicon path
    if platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}:
        return RuntimeDecision(runtime="mlx", reason="apple_silicon")

    # Default local fallback
    return RuntimeDecision(runtime="ollama", reason="default_fallback")
