"""GPQA benchmark mode with domain prompts and self-consistency voting."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from pradysagican.providers.llm import UniversalLLMProvider


@dataclass
class GPQAModeResult:
    answer: str
    votes: dict[str, int]
    samples: int
    domain: str


class GPQAMode:
    """Expert-style CoT sampling and majority-vote aggregation scaffold."""

    DOMAIN_PREFIX = {
        "physics": "Reason as a PhD-level physicist, step by step.",
        "chemistry": "Reason as a PhD-level chemist, step by step.",
        "biology": "Reason as a PhD-level biologist, step by step.",
        "computer_science": "Reason as a PhD-level computer scientist, step by step.",
    }

    def __init__(self, llm: UniversalLLMProvider | None = None) -> None:
        self._llm = llm or UniversalLLMProvider()

    async def answer(self, question: str, domain: str = "physics", samples: int = 5) -> GPQAModeResult:
        prefix = self.DOMAIN_PREFIX.get(domain, "Reason carefully and step by step.")
        outputs: list[str] = []
        for _ in range(max(samples, 1)):
            out = await self._llm.complete(
                f"{prefix}\nQuestion: {question}\nReturn final answer in one line at the end.",
                temperature=0.4,
                max_tokens=900,
            )
            outputs.append(out.strip())
        vote_counts = Counter(outputs)
        best = vote_counts.most_common(1)[0][0] if vote_counts else ""
        return GPQAModeResult(answer=best, votes=dict(vote_counts), samples=samples, domain=domain)

