"""
Inter-Agent Communication ("Telepathy") — PRADYSAGICAN
Shared mental models, collective reasoning, consensus building.
Based on Global Workspace Theory of consciousness.
"""
from __future__ import annotations
import logging, asyncio
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class SharedModel:
    topic: str
    agents: list[str]
    shared_beliefs: list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)
    confidence: float = 0.5

class TelepathyEngine:
    """Multi-agent coordination through shared workspace and intent broadcasting."""

    def __init__(self) -> None:
        self._global_workspace: dict[str, Any] = {}
        self._agent_intents: dict[str, str] = {}
        self._shared_models: dict[str, SharedModel] = {}

    async def broadcast_intent(self, agent_id: str, intent: str) -> None:
        """Broadcast an agent\'s intent to the global workspace."""
        self._agent_intents[agent_id] = intent
        self._global_workspace[f"intent_{agent_id}"] = {"intent": intent, "agent": agent_id}
        logger.debug("Intent broadcast: %s -> %s", agent_id, intent[:50])

    async def build_shared_model(self, topic: str, agent_contributions: dict[str, list[str]]) -> SharedModel:
        """Build synchronized understanding across agents."""
        all_beliefs = set()
        per_agent = {}
        for agent, beliefs in agent_contributions.items():
            per_agent[agent] = set(beliefs)
            all_beliefs.update(beliefs)
        # Find consensus and disagreements
        shared = all_beliefs
        for beliefs_set in per_agent.values():
            shared &= beliefs_set
        disagreements = all_beliefs - shared

        model = SharedModel(
            topic=topic, agents=list(agent_contributions.keys()),
            shared_beliefs=list(shared), disagreements=list(disagreements),
            confidence=len(shared) / max(len(all_beliefs), 1),
        )
        self._shared_models[topic] = model
        return model

    async def collective_reasoning(self, agents: list[str], problem: str) -> dict[str, Any]:
        """Distributed problem solving across agents."""
        # Simulate parallel agent contributions
        contributions = {agent: [f"{agent}\'s perspective on: {problem[:30]}"] for agent in agents}
        model = await self.build_shared_model(problem[:50], contributions)
        return {"problem": problem, "agents_involved": len(agents), "shared_model": model, "consensus_reached": model.confidence > 0.5}

    async def consensus_building(self, agents: list[str], proposal: str) -> dict[str, Any]:
        """Attempt to reach agreement on a proposal."""
        votes = {agent: "agree" for agent in agents[:len(agents)//2 + 1]}
        votes.update({agent: "discuss" for agent in agents[len(agents)//2 + 1:]})
        agree_count = sum(1 for v in votes.values() if v == "agree")
        return {"proposal": proposal, "votes": votes, "consensus": agree_count > len(agents) / 2, "agreement_ratio": agree_count / max(len(agents), 1)}
