"""
Universal LLM Provider — PRADYSAGICAN
Zero-cost: NVIDIA NIM, Groq, Together, HuggingFace, Ollama.
OpenAI-compatible API with automatic fallback.
"""
from __future__ import annotations
import logging, asyncio, time
from typing import Any
import httpx
from pradysagican.config import ProviderConfig, load_config

logger = logging.getLogger(__name__)

class UniversalLLMProvider:
    """Unified interface to multiple LLM providers with fallback."""

    def __init__(self, providers: dict[str, ProviderConfig] | None = None, fallback_chain: list[str] | None = None) -> None:
        cfg = load_config()
        self._providers = providers or cfg.providers
        self._fallback = fallback_chain or cfg.fallback_chain
        self._request_count = 0
        self._total_tokens = 0

    async def complete(self, prompt: str, model: str | None = None, max_tokens: int = 2048, temperature: float = 0.7) -> str:
        """Generate completion with automatic fallback across providers."""
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

    async def _call_provider(self, provider: ProviderConfig, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Make OpenAI-compatible API call."""
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
            self._request_count += 1
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            self._total_tokens += usage.get("total_tokens", 0)
            return content

    def stats(self) -> dict[str, Any]:
        return {"requests": self._request_count, "total_tokens": self._total_tokens, "providers_configured": len([p for p in self._providers.values() if p.api_key])}
