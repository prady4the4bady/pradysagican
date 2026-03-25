"""
Universal LLM Provider — PRADYSAGICAN
Zero-cost: NVIDIA NIM, Groq, Together, HuggingFace, Ollama.
OpenAI-compatible API with automatic fallback.
"""
from __future__ import annotations
import logging
import os
import time
from typing import Any

import httpx

from pradysagican.config import ProviderConfig, load_config
from pradysagican.telemetry.costs import cost_metadata
from pradysagican.telemetry.metrics import MetricsCollector
from pradysagican.telemetry.traces import TraceLogger

logger = logging.getLogger(__name__)


class UniversalLLMProvider:
    """Unified interface to multiple LLM providers with fallback."""

    def __init__(self, providers: dict[str, ProviderConfig] | None = None, fallback_chain: list[str] | None = None) -> None:
        cfg = load_config()
        self._cfg = cfg
        self._providers = providers or cfg.providers
        self._fallback = fallback_chain or cfg.fallback_chain
        self._request_count = 0
        self._total_tokens = 0
        self._total_estimated_cost = 0.0
        self._metrics = MetricsCollector()
        self._traces = TraceLogger()
        self._litellm = None
        self._litellm_enabled = False
        if (
            cfg.upgrades.enable_litellm_router
            and not cfg.upgrades.force_legacy_provider
            and not cfg.upgrades.kill_switch_new_paths
        ):
            try:
                import litellm  # type: ignore[import-not-found]
                self._litellm = litellm
                self._litellm_enabled = True
            except Exception as exc:  # pragma: no cover
                logger.warning("LiteLLM unavailable, using legacy provider calls: %s", exc)

    async def complete(self, prompt: str, model: str | None = None, max_tokens: int = 2048, temperature: float = 0.7) -> str:
        """Generate completion with automatic fallback across providers."""
        if self._litellm_enabled and self._litellm is not None:
            try:
                return await self._complete_litellm(prompt, model=model, max_tokens=max_tokens, temperature=temperature)
            except Exception as exc:
                logger.warning("LiteLLM route failed, falling back to legacy chain: %s", exc)

        for provider_name in self._fallback:
            provider = self._providers.get(provider_name)
            if not provider or not provider.api_key:
                continue
            try:
                return await self._call_provider(provider, prompt, model or provider.default_model, max_tokens, temperature)
            except Exception as e:
                logger.warning("Provider %s failed: %s — trying next", provider_name, e)
                continue
        
        # All providers failed — provide helpful error instead of misleading echo
        logger.error("All LLM providers failed or unavailable")
        return await self._graceful_degradation(prompt)
    
    async def _graceful_degradation(self, prompt: str) -> str:
        """
        Graceful degradation when all providers fail.
        Returns helpful error message instead of misleading echo.
        """
        configured_providers = [
            name for name, cfg in self._providers.items() 
            if cfg.api_key
        ]
        
        if not configured_providers:
            error_msg = (
                "❌ No LLM providers configured.\n\n"
                "PRADYSAGICAN requires an LLM to think. Please configure one:\n\n"
                "Option 1: Use Free Cloud APIs (fastest):\n"
                "  - Groq: https://console.groq.com/keys (set GROQ_API_KEY)\n"
                "  - Together AI: https://api.together.xyz (set TOGETHER_API_KEY)\n"
                "  - NVIDIA NIM: https://api.nvidia.com (set NVIDIA_API_KEY)\n"
                "  - HuggingFace: https://huggingface.co/settings/tokens (set HF_TOKEN)\n\n"
                "Option 2: Use Local Ollama (free, runs locally):\n"
                "  docker run -d -p 11434:11434 ollama/ollama\n"
                "  ollama pull llama3.2\n\n"
                "Then restart the system. Quick start:\n"
                "  source .venv/bin/activate\n"
                "  pradysagican chat"
            )
        else:
            error_msg = (
                f"❌ All configured providers ({', '.join(configured_providers)}) failed.\n\n"
                "Debugging steps:\n"
                "1. Check your internet connection\n"
                "2. Verify API keys are correct:\n"
            )
            for name in configured_providers:
                error_msg += f"     - {name}: {os.getenv(self._get_env_var_for_provider(name), '(not set)')}\n"
            error_msg += (
                "3. Check provider status pages:\n"
                "     - Groq: https://status.groq.com\n"
                "     - Together AI: https://status.together.xyz\n"
                "4. Or use local Ollama as fallback:\n"
                "     docker run -d -p 11434:11434 ollama/ollama && ollama pull llama3.2\n"
            )
        
        logger.error(error_msg)
        return error_msg
    
    def _get_env_var_for_provider(self, provider_name: str) -> str:
        """Get environment variable name for a provider."""
        env_map = {
            "nvidia": "NVIDIA_API_KEY",
            "groq": "GROQ_API_KEY",
            "together": "TOGETHER_API_KEY",
            "huggingface": "HF_TOKEN",
            "ollama": "OLLAMA_BASE_URL",
        }
        return env_map.get(provider_name, "UNKNOWN")

    async def chat(self, messages: list[dict[str, str]], model: str | None = None, **kwargs: Any) -> str:
        """Chat-style completion."""
        prompt = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
        return await self.complete(prompt, model=model, **kwargs)

    async def _complete_litellm(
        self, prompt: str, model: str | None = None, max_tokens: int = 2048, temperature: float = 0.7
    ) -> str:
        assert self._litellm is not None
        started = time.time()
        response = await self._litellm.acompletion(
            model=model or "openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        ended = time.time()
        content = response["choices"][0]["message"]["content"]
        usage = response.get("usage", {})
        meta = cost_metadata("litellm", model or "openai/gpt-4o-mini", usage)
        self._request_count += 1
        self._total_tokens += int(meta["total_tokens"])
        self._total_estimated_cost += float(meta["estimated_cost_usd"])
        self._metrics.record("llm.complete", started, ended, meta)
        self._traces.emit("llm.complete", {"path": "litellm", **meta})
        return content

    async def _call_provider(self, provider: ProviderConfig, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Make OpenAI-compatible API call."""
        started = time.time()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{provider.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            response.raise_for_status()
            data = response.json()
            ended = time.time()
            self._request_count += 1
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            self._total_tokens += usage.get("total_tokens", 0)
            meta = cost_metadata(provider.name, model, usage)
            self._total_estimated_cost += float(meta["estimated_cost_usd"])
            self._metrics.record("llm.complete", started, ended, meta)
            self._traces.emit("llm.complete", {"path": "legacy", **meta})
            return content

    def stats(self) -> dict[str, Any]:
        return {
            "requests": self._request_count,
            "total_tokens": self._total_tokens,
            "estimated_cost_usd": round(self._total_estimated_cost, 8),
            "providers_configured": len([p for p in self._providers.values() if p.api_key]),
            "litellm_enabled": self._litellm_enabled,
            "latency": self._metrics.summary(),
        }
