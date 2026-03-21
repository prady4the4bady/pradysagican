"""
Imagination Capability — PRADYSAGICAN
Creative scenario generation, divergent/convergent thinking, dream states.
"""
from __future__ import annotations
import logging, random
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

@dataclass
class CreativeSynthesis:
    concepts: list[str]
    novel_combination: str
    novelty_score: float
    feasibility_score: float

class ImaginationCapability:
    """Creative thinking through scenario generation and concept synthesis."""

    def __init__(self, llm_fn: Callable[[str], Awaitable[str]] | None = None) -> None:
        self._llm = llm_fn or (lambda p: _echo(p))
        self._generated_scenarios: list[dict] = []

    async def generate_scenarios(self, context: str, constraints: list[str] | None = None, n: int = 3) -> list[dict[str, Any]]:
        """Generate multiple possible future scenarios."""
        scenarios = []
        modes = ["optimistic", "pessimistic", "wildcard"][:n]
        for mode in modes:
            constraint_text = f" Constraints: {constraints}" if constraints else ""
            prompt = f"Generate a {mode} scenario for: {context}.{constraint_text}"
            result = await self._llm(prompt)
            scenarios.append({"mode": mode, "scenario": result, "context": context})
        self._generated_scenarios.extend(scenarios)
        return scenarios

    async def creative_synthesis(self, concepts: list[str]) -> CreativeSynthesis:
        """Combine unrelated concepts into novel ideas."""
        if len(concepts) < 2:
            return CreativeSynthesis(concepts=concepts, novel_combination="Need 2+ concepts", novelty_score=0, feasibility_score=0)
        # Random combination strategy (TRIZ-inspired)
        random.shuffle(concepts)
        combo = f"{concepts[0]} + {concepts[1]}"
        if len(concepts) > 2:
            combo += f" enhanced by {concepts[2]}"
        novelty = min(len(set(" ".join(concepts).lower().split())) / 20.0, 1.0)
        return CreativeSynthesis(concepts=concepts, novel_combination=combo, novelty_score=novelty, feasibility_score=0.5)

    async def counterfactual_thinking(self, event: str, changes: list[str]) -> list[str]:
        """Model alternate outcomes."""
        outcomes = []
        for change in changes:
            prompt = f"If \'{change}\' had been different in \'{event}\', what would happen?"
            result = await self._llm(prompt)
            outcomes.append(f"If {change}: {result}")
        return outcomes

    async def dream_state(self, seed_memories: list[str]) -> list[str]:
        """REM-sleep-like creative association."""
        if not seed_memories:
            return ["No seeds for dreaming"]
        associations = []
        for _ in range(min(3, len(seed_memories))):
            pair = random.sample(seed_memories, min(2, len(seed_memories)))
            associations.append(f"Dream link: \'{pair[0][:30]}\' ↔ \'{pair[-1][:30]}\'")
        return associations

async def _echo(prompt: str) -> str:
    return f"[Imagined: {prompt[:80]}]"
