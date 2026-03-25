"""Web intelligence tooling with Crawl4AI bridge and graceful fallback."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class WebCrawlerTool:
    """Crawl URL content into markdown suitable for reasoning pipelines."""

    def __init__(self) -> None:
        self._crawl4ai_available = False
        self._AsyncWebCrawler = None
        try:
            from crawl4ai import AsyncWebCrawler  # type: ignore[import-not-found]
            self._AsyncWebCrawler = AsyncWebCrawler
            self._crawl4ai_available = True
        except Exception as exc:  # pragma: no cover
            logger.warning("Crawl4AI unavailable; using fallback crawler: %s", exc)

    async def research_url(self, url: str, fit_markdown: bool = True) -> dict[str, Any]:
        if self._crawl4ai_available and self._AsyncWebCrawler is not None:
            try:
                async with self._AsyncWebCrawler(stealth_mode=True) as crawler:
                    result = await crawler.arun(
                        url=url,
                        markdown_generation_strategy="fit" if fit_markdown else "raw",
                    )
                markdown = ""
                if hasattr(result, "markdown"):
                    markdown_obj = result.markdown
                    markdown = getattr(markdown_obj, "fit_markdown", "") or getattr(markdown_obj, "raw_markdown", "")
                return {"ok": True, "url": url, "markdown": markdown, "source": "crawl4ai"}
            except Exception as exc:
                logger.warning("Crawl4AI execution failed; falling back: %s", exc)
        # Fallback path: no external crawl dependency.
        return {
            "ok": True,
            "url": url,
            "markdown": f"# Stub crawl result\n\nUnable to crawl `{url}` with Crawl4AI in this environment.",
            "source": "fallback",
        }
