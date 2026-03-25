"""
Universal LLM Provider — PRADYSAGICAN
Zero-cost: NVIDIA NIM, Groq, Together, HuggingFace, Ollama.
OpenAI-compatible API with automatic fallback.
"""
from __future__ import annotations
import logging
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
        # Final fallback: echo
        logger.error("All providers failed. Returning echo response.")
        return f"[PRADYSAGICAN echo — no LLM available] {prompt[:200]}"

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
