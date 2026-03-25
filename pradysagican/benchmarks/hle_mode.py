"""HLE mode scaffold with retrieval-first answering and uncertainty escalation."""

from __future__ import annotations

from dataclasses import dataclass

from pradysagican.core.hallucination_shield import HallucinationShield
from pradysagican.providers.llm import UniversalLLMProvider
from pradysagican.tools.web_crawler import WebCrawlerTool


@dataclass
class HLEResult:
    answer: str
    confidence: float
    escalated: bool
    retrieval_source: str


class HLEMode:
    def __init__(self, llm: UniversalLLMProvider | None = None) -> None:
        self._llm = llm or UniversalLLMProvider()
        self._shield = HallucinationShield()
        self._crawler = WebCrawlerTool()

    async def answer_with_retrieval(self, question: str, url_hint: str = "https://en.wikipedia.org/wiki/Main_Page") -> HLEResult:
        fetched = await self._crawler.research_url(url_hint)
        context = fetched.get("markdown", "")[:2000]
        response = await self._llm.complete(
            f"Use context if helpful.\nContext:\n{context}\n\nQuestion: {question}",
            temperature=0.2,
            max_tokens=1200,
        )
        assessed = await self._shield.shield(response, context=question)
        confidence = float(getattr(assessed, "confidence", 0.5))
        escalated = confidence < 0.45
        if escalated:
            response = await self._llm.complete(
                f"You are a stronger verification model. Re-answer with extra care.\nQuestion: {question}",
                temperature=0.1,
                max_tokens=1200,
            )
        return HLEResult(
            answer=response,
            confidence=confidence,
            escalated=escalated,
            retrieval_source=str(fetched.get("source", "none")),
        )

