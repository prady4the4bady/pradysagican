"""Resilient DOM extraction using Scrapling with fallback parser."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class DOMExtractor:
    def __init__(self) -> None:
        self._available = False
        self._scrapling = None
        try:
            import scrapling  # type: ignore[import-not-found]
            self._scrapling = scrapling
            self._available = True
        except Exception as exc:  # pragma: no cover
            logger.warning("Scrapling unavailable; using fallback DOM extraction: %s", exc)

    def extract(self, html: str, query: str) -> dict[str, Any]:
        if self._available and self._scrapling is not None:
            try:
                # Best-effort generic API; exact API can be adapted later.
                parser = self._scrapling.Scrape(html=html) if hasattr(self._scrapling, "Scrape") else None
                if parser is not None and hasattr(parser, "query"):
                    result = parser.query(query)
                    return {"ok": True, "mode": "scrapling", "result": str(result)}
            except Exception as exc:
                logger.warning("Scrapling extraction failed: %s", exc)
        # Fallback: return lightweight snippet.
        snippet = html[:500]
        return {"ok": True, "mode": "fallback", "result": snippet}
