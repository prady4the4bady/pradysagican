"""Optional provider router with LiteLLM bridge and legacy fallback."""

from __future__ import annotations

import logging
from typing import Any

from pradysagican.config import load_config
from pradysagican.providers.llm import UniversalLLMProvider

logger = logging.getLogger(__name__)


class ProviderRouter:
    """Routes requests through LiteLLM when enabled, else uses legacy provider."""

    def __init__(self) -> None:
        self._cfg = load_config()
        self._legacy = UniversalLLMProvider()
        self._litellm_available = False
        self._litellm = None
        if (
            self._cfg.upgrades.enable_litellm_router
            and not self._cfg.upgrades.force_legacy_provider
            and not self._cfg.upgrades.kill_switch_new_paths
        ):
            try:
                import litellm  # type: ignore[import-not-found]
                self._litellm = litellm
                self._litellm_available = True
            except Exception as exc:  # pragma: no cover
                logger.warning("LiteLLM not available, falling back to legacy provider: %s", exc)

    async def complete(
        self,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        if self._litellm_available and self._litellm is not None:
            try:
                resp = await self._litellm.acompletion(
                    model=model or "openai/gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return resp["choices"][0]["message"]["content"]
            except Exception as exc:
                logger.warning("LiteLLM route failed, falling back: %s", exc)
        return await self._legacy.complete(prompt, model=model, max_tokens=max_tokens, temperature=temperature)

    async def chat(self, messages: list[dict[str, str]], model: str | None = None, **kwargs: Any) -> str:
        prompt = "\n".join(f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages)
        return await self.complete(prompt, model=model, **kwargs)
