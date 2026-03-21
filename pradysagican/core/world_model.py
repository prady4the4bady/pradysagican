"""
World Model — PRADYSAGICAN
============================
Internal world model inspired by JEPA (LeCun), C-JEPA (2026), and VL-JEPA.
Operates in latent representation space, not token space.

Components:
- StateEstimator: perceives & estimates current world state
- ActionPredictor: predicts consequences of actions
- ImaginationEngine: generates hypothetical scenarios
- CausalGraph: maintains causal relationships
- SocialModel: Theory of Mind for multi-agent understanding
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

import numpy as np
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class WorldState:
    """Latent representation of the current world state."""
    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    relations: list[tuple[str, str, str]] = field(default_factory=list)
    temporal_context: str = ""
    confidence: float = 0.5
    timestamp: float = field(default_factory=time.time)

    def to_vector(self) -> np.ndarray:
        """Convert to a fixed-size numerical representation."""
        features = []
        features.append(len(self.entities))
        features.append(len(self.relations))
        features.append(self.confidence)
        features.append(len(self.temporal_context.split()) / 100)
        return np.array(features, dtype=np.float32)


@dataclass
class ActionPrediction:
    """Predicted outcome of an action."""
    action: str
    predicted_state: WorldState
    confidence: float
    side_effects: list[str] = field(default_factory=list)
    risk_level: float = 0.0


@dataclass
class Scenario:
    """A hypothetical scenario from imagination."""
    description: str
    initial_state: WorldState
    final_state: WorldState
    probability: float
    steps: list[str] = field(default_factory=list)
    is_desirable: bool = True


@dataclass
class AgentBelief:
    """Model of another agent's beliefs (Theory of Mind)."""
    agent_id: str
    believed_goals: list[str] = field(default_factory=list)
    believed_knowledge: list[str] = field(default_factory=list)
    emotional_state: str = "neutral"
    trust_level: float = 0.5
    cooperation_likelihood: float = 0.5


class WorldModel:
    """
    Internal world model operating in latent space.
    Predicts, imagines, and reasons about the world causally.
    """

    def __init__(
        self,
        llm_fn: Callable[[str], Awaitable[str]] | None = None,
        history_size: int = 100,
    ) -> None:
        self._llm = llm_fn or _default_llm
        self._current_state = WorldState()
        self._state_history: deque[WorldState] = deque(maxlen=history_size)
        self._causal_graph = nx.DiGraph()
        self._agent_models: dict[str, AgentBelief] = {}
        self._prediction_cache: dict[str, ActionPrediction] = {}
        self._lock = asyncio.Lock()
        logger.info("WorldModel initialised")

    # ── State Estimation ──────────────────────────────────────────────────

    async def observe(self, observation: dict[str, Any]) -> WorldState:
        """Update world state from new observations."""
        async with self._lock:
            self._state_history.append(self._current_state)

            # Merge observation into state
            new_entities = dict(self._current_state.entities)
            for key, value in observation.get("entities", {}).items():
                if key in new_entities:
                    new_entities[key].update(value)
                else:
                    new_entities[key] = value

            new_relations = list(self._current_state.relations)
            for rel in observation.get("relations", []):
                if rel not in new_relations:
                    new_relations.append(rel)

            self._current_state = WorldState(
                entities=new_entities,
                relations=new_relations,
                temporal_context=observation.get("context", self._current_state.temporal_context),
                confidence=min(self._current_state.confidence + 0.05, 0.95),
            )

            # Update causal graph
            for subj, pred, obj in observation.get("relations", []):
                self._causal_graph.add_edge(subj, obj, relation=pred, timestamp=time.time())

            return self._current_state

    @property
    def state(self) -> WorldState:
        return self._current_state

    # ── Action Prediction ─────────────────────────────────────────────────

    async def predict_action(self, action: str) -> ActionPrediction:
        """Predict the consequence of an action in latent space."""
        cache_key = f"{action}_{self._current_state.confidence:.2f}"
        if cache_key in self._prediction_cache:
            return self._prediction_cache[cache_key]

        prompt = (
            f"Current world state has {len(self._current_state.entities)} entities "
            f"and {len(self._current_state.relations)} relationships.\n"
            f"Action to take: {action}\n"
            f"Predict: 1) New state description 2) Side effects 3) Risk level (0-1)"
        )
        response = await self._llm(prompt)

        # Parse response into prediction
        lines = response.strip().split("\n")
        description = lines[0] if lines else "State changed"
        side_effects = [l.strip("- ") for l in lines[1:] if l.strip().startswith("-")]
        risk = 0.3  # default

        predicted_state = WorldState(
            entities=dict(self._current_state.entities),
            relations=list(self._current_state.relations),
            temporal_context=f"After: {action}",
            confidence=self._current_state.confidence * 0.9,
        )

        prediction = ActionPrediction(
            action=action,
            predicted_state=predicted_state,
            confidence=predicted_state.confidence,
            side_effects=side_effects,
            risk_level=risk,
        )
        self._prediction_cache[cache_key] = prediction
        return prediction

    async def simulate_action_sequence(self, actions: list[str]) -> list[ActionPrediction]:
        """Simulate a sequence of actions (mental rehearsal)."""
        predictions = []
        saved_state = self._current_state
        for action in actions:
            pred = await self.predict_action(action)
            predictions.append(pred)
            # Temporarily advance state for next prediction
            self._current_state = pred.predicted_state
        # Restore original state (this was just simulation)
        self._current_state = saved_state
        return predictions

    # ── Imagination Engine ────────────────────────────────────────────────

    async def imagine(self, prompt: str, num_scenarios: int = 3) -> list[Scenario]:
        """
        Generate hypothetical scenarios through mental simulation.
        Uses divergent thinking + world model constraints.
        """
        scenarios = []
        for i in range(num_scenarios):
            llm_prompt = (
                f"Scenario {i + 1}/{num_scenarios} for: {prompt}\n"
                f"Current context: {self._current_state.temporal_context}\n"
                f"Generate a {'optimistic' if i == 0 else 'pessimistic' if i == 1 else 'surprising'} scenario."
            )
            response = await self._llm(llm_prompt)
            steps = [s.strip() for s in response.split("\n") if s.strip()]

            scenario = Scenario(
                description=response[:200],
                initial_state=self._current_state,
                final_state=WorldState(
                    temporal_context=f"Imagined: {prompt}",
                    confidence=0.3 + (0.2 * (num_scenarios - i) / num_scenarios),
                ),
                probability=1.0 / num_scenarios,
                steps=steps,
                is_desirable=(i == 0),
            )
            scenarios.append(scenario)

        return scenarios

    async def dream(self, seed_memories: list[str]) -> list[str]:
        """
        Dream-like creative association (REM-sleep inspired).
        Randomly combines memories to generate novel insights.
        """
        if not seed_memories:
            return ["No memories to dream about"]

        associations: list[str] = []
        rng = np.random.default_rng()

        for _ in range(min(5, len(seed_memories))):
            # Pick random pair
            idx = rng.choice(len(seed_memories), size=min(2, len(seed_memories)), replace=False)
            pair = [seed_memories[i] for i in idx]
            prompt = f"Find an unexpected creative connection between:\n1. {pair[0]}\n2. {pair[-1]}"
            insight = await self._llm(prompt)
            associations.append(insight)

        return associations

    # ── Causal Graph ──────────────────────────────────────────────────────

    async def add_causal_link(self, cause: str, effect: str, strength: float = 0.5) -> None:
        """Add a causal relationship to the world model."""
        self._causal_graph.add_edge(cause, effect, strength=strength, timestamp=time.time())

    async def trace_causes(self, effect: str, max_depth: int = 5) -> list[list[str]]:
        """Trace back through causal chains to find root causes."""
        paths: list[list[str]] = []
        if effect not in self._causal_graph:
            return paths
        for source in self._causal_graph.predecessors(effect):
            try:
                for path in nx.all_simple_paths(self._causal_graph, source, effect, cutoff=max_depth):
                    paths.append(path)
            except nx.NetworkXError:
                continue
        return paths[:10]

    async def predict_effects(self, cause: str, max_depth: int = 3) -> list[str]:
        """Predict downstream effects of a cause."""
        effects = []
        if cause not in self._causal_graph:
            return effects
        visited = set()
        queue = [(cause, 0)]
        while queue:
            node, depth = queue.pop(0)
            if depth > max_depth or node in visited:
                continue
            visited.add(node)
            for successor in self._causal_graph.successors(node):
                effects.append(successor)
                queue.append((successor, depth + 1))
        return effects

    # ── Theory of Mind (Social Model) ─────────────────────────────────────

    async def model_agent(self, agent_id: str, observations: dict[str, Any]) -> AgentBelief:
        """Build/update mental model of another agent."""
        if agent_id not in self._agent_models:
            self._agent_models[agent_id] = AgentBelief(agent_id=agent_id)

        model = self._agent_models[agent_id]
        if "goals" in observations:
            model.believed_goals = observations["goals"]
        if "knowledge" in observations:
            model.believed_knowledge = observations["knowledge"]
        if "emotion" in observations:
            model.emotional_state = observations["emotion"]
        if "trust" in observations:
            model.trust_level = float(observations["trust"])
        if "cooperative" in observations:
            model.cooperation_likelihood = float(observations["cooperative"])

        return model

    async def predict_agent_action(self, agent_id: str) -> str:
        """Predict what another agent will do based on our model of them."""
        model = self._agent_models.get(agent_id)
        if not model:
            return "unknown — no model of this agent"

        prompt = (
            f"Agent '{agent_id}' has goals: {model.believed_goals}, "
            f"emotional state: {model.emotional_state}, "
            f"cooperation likelihood: {model.cooperation_likelihood:.2f}. "
            f"What will they likely do next?"
        )
        return await self._llm(prompt)

    # ── Statistics ────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        return {
            "entities": len(self._current_state.entities),
            "relations": len(self._current_state.relations),
            "causal_nodes": self._causal_graph.number_of_nodes(),
            "causal_edges": self._causal_graph.number_of_edges(),
            "agent_models": len(self._agent_models),
            "state_history": len(self._state_history),
            "prediction_cache": len(self._prediction_cache),
        }


async def _default_llm(prompt: str) -> str:
    return f"[World model prediction based on: {prompt[:80]}...]"
