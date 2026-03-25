"""Langfuse instrumentation adapter with safe no-op fallback."""

from __future__ import annotations

from typing import Any


class LangfuseAdapter:
    """Minimal wrapper so code can emit traces even without Langfuse installed."""

    def __init__(self) -> None:
        self._available = False
        self._client = None
        try:
            from langfuse import Langfuse  # type: ignore[import-not-found]
            self._client = Langfuse()
            self._available = True
        except Exception:
            self._available = False

    @property
    def available(self) -> bool:
        return self._available and self._client is not None

    def trace(self, name: str, input_data: Any, output_data: Any, metadata: dict[str, Any] | None = None) -> None:
        if not self.available:
            return
        try:
            self._client.trace(
                name=name,
                input=input_data,
                output=output_data,
                metadata=metadata or {},
            )
        except Exception:
            return

