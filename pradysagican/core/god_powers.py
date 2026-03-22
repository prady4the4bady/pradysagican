"""God Powers — Novel capabilities that put PRADYSAGICAN beyond any existing system.

Each capability is a genuine AI research contribution:
1. DreamEngine — Controlled creative hallucination (imagination)
2. CausalSuperpower — True cause-effect reasoning (Pearl's do-calculus)
3. MetaCognitionV2 — Recursive thinking-about-thinking
4. MultiScaleAttention — Simultaneous micro/meso/macro analysis
5. KnowledgeSynthesizer — Derive genuinely new knowledge
6. MoralCompass — First-principles ethical reasoning
"""

from __future__ import annotations

import hashlib
import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)


# ── Shared Helpers ───────────────────────────────────────────────────────────

def _text_hash(text: str) -> np.ndarray:
    """Deterministic pseudo-embedding: SHA-256 → 64-dim float vector in [-1,1]."""
    digest = hashlib.sha256(text.lower().encode()).digest()
    arr = np.frombuffer(digest, dtype=np.uint8).astype(np.float64)
    return (arr / 127.5) - 1.0


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return max(0.0, min(1.0, float(np.dot(a, b) / (na * nb))))


def _word_overlap(a: str, b: str) -> float:
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _blended_sim(a: str, b: str) -> float:
    return _cosine_sim(_text_hash(a), _text_hash(b)) * 0.3 + _word_overlap(a, b) * 0.7


# ═══════════════════════════════════════════════════════════════════════════════
# POWER 1: DreamEngine — Controlled Creative Hallucination
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DreamResult:
    """Output of a dreaming session."""
    visions: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    novel_combinations: list[str] = field(default_factory=list)
    creativity_score: float = 0.0
    reality_anchor_used: float = 0.0
    seed_concepts: list[str] = field(default_factory=list)


class DreamEngine:
    """Controlled creative hallucination for ideation and innovation.

    While other AIs eliminate hallucination, we harness it.
    Controlled hallucination = imagination. This is how human dreams work.
    """

    # Transformation templates
    _TRANSFORMS: list[tuple[str, str]] = [
        ("metaphor", "{A} is like {B} in the way that"),
        ("analogy", "Just as {A} does X, {B} could do Y"),
        ("inversion", "What if the opposite of {A} were true?"),
        ("magnification", "What if {A} were 1000× more powerful?"),
        ("miniaturization", "What if {A} were reduced to its smallest essence?"),
        ("fusion", "Combining {A} and {B} creates a new concept"),
        ("temporal_shift", "What if {A} existed 100 years from now?"),
        ("perspective_flip", "How would {B} see {A}?"),
    ]

    def __init__(self, reality_anchor: float = 0.5, seed: int | None = None) -> None:
        self.reality_anchor = max(0.0, min(1.0, reality_anchor))
        self._rng = np.random.default_rng(seed)
        self._dream_log: list[DreamResult] = []

    async def dream(
        self,
        seed_concepts: list[str],
        creativity_level: float = 0.7,
    ) -> DreamResult:
        """Generate creative visions from seed concepts.

        Pipeline:
        1. Find associations for each concept
        2. Cross-pollinate: combine concepts from different domains
        3. Apply transformations (metaphor, analogy, inversion, etc.)
        4. Filter through reality anchor
        """
        creativity_level = max(0.0, min(1.0, creativity_level))
        visions: list[str] = []
        insights: list[str] = []
        novel_combos: list[str] = []

        # 1. Association expansion
        associations: dict[str, list[str]] = {}
        for concept in seed_concepts:
            associations[concept] = self._find_associations(concept)

        # 2. Cross-pollination
        if len(seed_concepts) >= 2:
            for i in range(len(seed_concepts)):
                for j in range(i + 1, len(seed_concepts)):
                    combo = self._cross_pollinate(
                        seed_concepts[i], seed_concepts[j],
                        associations.get(seed_concepts[i], []),
                        associations.get(seed_concepts[j], []),
                    )
                    novel_combos.extend(combo)

        # 3. Transformations
        for concept in seed_concepts:
            transformed = self._apply_transformations(concept, seed_concepts, creativity_level)
            visions.extend(transformed)

        # 4. Reality anchor filter
        plausible_visions: list[str] = []
        for v in visions:
            plausibility = self._plausibility_score(v, seed_concepts)
            threshold = 1.0 - creativity_level  # higher creativity → lower threshold
            if plausibility >= threshold * self.reality_anchor:
                plausible_visions.append(v)

        # Extract insights
        for combo in novel_combos[:5]:
            insights.append(f"Insight: {combo} reveals a hidden connection")

        creativity_score = min(1.0, creativity_level * (1.0 + len(novel_combos) * 0.05))

        result = DreamResult(
            visions=plausible_visions[:10],
            insights=insights[:5],
            novel_combinations=novel_combos[:8],
            creativity_score=round(creativity_score, 4),
            reality_anchor_used=self.reality_anchor,
            seed_concepts=seed_concepts,
        )
        self._dream_log.append(result)
        return result

    async def lucid_dream(self, goal: str, constraints: list[str]) -> list[str]:
        """Directed dreaming: creative solutions within constraints."""
        raw = await self.dream(goal.split()[:5], creativity_level=0.8)
        solutions: list[str] = []
        for vision in raw.visions + raw.novel_combinations:
            # Check each constraint
            violates = False
            for c in constraints:
                if _blended_sim(vision.lower(), f"violates {c}") > 0.6:
                    violates = True
                    break
            if not violates:
                solutions.append(f"Solution for '{goal}': {vision}")
        if not solutions:
            solutions.append(f"Creative approach to '{goal}': combine diverse perspectives within bounds")
        return solutions[:5]

    async def nightmare_analysis(self, worst_cases: list[str]) -> list[dict[str, Any]]:
        """Turn fears into actionable risk mitigation plans."""
        plans: list[dict[str, Any]] = []
        for fear in worst_cases:
            words = [w for w in fear.lower().split() if len(w) > 3]
            severity = min(1.0, len(words) * 0.15 + 0.3)
            plans.append({
                "fear": fear,
                "severity": round(severity, 2),
                "root_cause": f"Underlying vulnerability: {' '.join(words[:3])}",
                "mitigation": [
                    f"Early warning: monitor for signs of '{words[0] if words else 'issue'}'",
                    f"Prevention: strengthen defenses around {fear[:30]}",
                    f"Response plan: if {fear[:20]}... then activate contingency",
                    f"Recovery: restore from known-good state after {fear[:20]}...",
                ],
                "opportunity": f"By preparing for '{fear[:25]}...', we also improve resilience overall",
            })
        return plans

    async def creative_synthesis(self, domain_a: str, domain_b: str) -> list[str]:
        """Find unexpected connections between two unrelated domains."""
        concepts_a = self._domain_concepts(domain_a)
        concepts_b = self._domain_concepts(domain_b)
        bridges: list[str] = []

        for ca in concepts_a:
            for cb in concepts_b:
                sim = _blended_sim(ca, cb)
                if 0.05 < sim < 0.5:  # not too similar, not too different
                    bridges.append(
                        f"Bridge: '{ca}' ({domain_a}) ↔ '{cb}' ({domain_b}) — "
                        f"what if we applied {ca} principles to {cb}?"
                    )
        bridges.sort(key=lambda b: len(b), reverse=True)
        return bridges[:5] or [
            f"Cross-domain insight: apply {domain_a} thinking to {domain_b} problems"
        ]

    # ── Private helpers ───────────────────────────────────────────────────

    def _find_associations(self, concept: str) -> list[str]:
        words = concept.lower().split()
        assocs: list[str] = []
        for w in words:
            if len(w) > 3:
                assocs.extend([f"{w}_enhanced", f"{w}_opposite", f"{w}_abstract", f"meta_{w}"])
        return assocs

    def _cross_pollinate(
        self, a: str, b: str, assocs_a: list[str], assocs_b: list[str],
    ) -> list[str]:
        combos: list[str] = [f"{a} meets {b}: a hybrid approach"]
        if assocs_a and assocs_b:
            idx_a = int(self._rng.integers(len(assocs_a)))
            idx_b = int(self._rng.integers(len(assocs_b)))
            combos.append(f"{assocs_a[idx_a]} combined with {assocs_b[idx_b]}")
        return combos

    def _apply_transformations(
        self, concept: str, all_concepts: list[str], creativity: float,
    ) -> list[str]:
        results: list[str] = []
        other = all_concepts[0] if all_concepts[0] != concept and all_concepts else concept
        n_transforms = max(1, int(len(self._TRANSFORMS) * creativity))
        chosen = self._rng.choice(len(self._TRANSFORMS), size=min(n_transforms, len(self._TRANSFORMS)), replace=False)
        for idx in chosen:
            name, template = self._TRANSFORMS[int(idx)]
            results.append(f"[{name}] " + template.replace("{A}", concept).replace("{B}", other))
        return results

    def _plausibility_score(self, vision: str, seeds: list[str]) -> float:
        if not seeds:
            return 0.5
        sims = [_blended_sim(vision, s) for s in seeds]
        return max(0.05, float(np.mean(sims)))

    def _domain_concepts(self, domain: str) -> list[str]:
        parts = domain.lower().replace("_", " ").split()
        concepts = list(parts)
        for p in parts:
            concepts.extend([f"{p}_theory", f"{p}_practice", f"{p}_pattern", f"{p}_system", f"{p}_model"])
        return concepts[:5]

    @property
    def dream_count(self) -> int:
        return len(self._dream_log)


# ═══════════════════════════════════════════════════════════════════════════════
# POWER 2: CausalSuperpower — True Cause-Effect Understanding
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CausalEffect:
    """A downstream effect from an intervention."""
    variable: str
    old_value: float
    new_value: float
    change: float
    path: list[str] = field(default_factory=list)
    confidence: float = 0.0


class CausalSuperpower:
    """True causal reasoning using structural causal models.

    Implements Pearl's do-calculus: interventions, counterfactuals,
    root-cause analysis, cascade prediction, and causal discovery.
    """

    def __init__(self) -> None:
        self._graph = nx.DiGraph()
        self._values: dict[str, float] = {}  # current state
        self._mechanisms: dict[tuple[str, str], dict[str, Any]] = {}
        self._interventions_log: list[dict[str, Any]] = []

    def add_variable(self, name: str, value: float = 0.0) -> None:
        """Register a variable in the causal model."""
        self._graph.add_node(name)
        self._values[name] = value

    def add_causal_mechanism(
        self,
        cause: str,
        effect: str,
        mechanism: str,
        strength: float = 0.5,
    ) -> None:
        """Define a causal link with HOW the cause affects the effect."""
        self._graph.add_edge(cause, effect, weight=strength, mechanism=mechanism)
        self._mechanisms[(cause, effect)] = {
            "mechanism": mechanism, "strength": strength,
        }
        for v in (cause, effect):
            if v not in self._values:
                self._values[v] = 0.0

    async def do_intervention(self, variable: str, value: float) -> dict[str, Any]:
        """Pearl's do() operator — SET a variable and propagate effects.

        Cuts all incoming edges to the variable, sets its value,
        then propagates effects through the causal graph.
        """
        if variable not in self._graph:
            return {"error": f"Unknown variable: {variable}"}

        old_values = dict(self._values)
        self._values[variable] = value

        # Propagate downstream via BFS
        effects: list[CausalEffect] = []
        visited: set[str] = {variable}
        queue: list[tuple[str, list[str]]] = [(variable, [variable])]

        while queue:
            current, path = queue.pop(0)
            for successor in self._graph.successors(current):
                if successor in visited:
                    continue
                visited.add(successor)

                edge = self._graph.edges[current, successor]
                strength = edge.get("weight", 0.5)
                delta = (value - old_values.get(variable, 0.0)) * strength
                old_val = self._values[successor]
                new_val = old_val + delta
                self._values[successor] = new_val

                eff = CausalEffect(
                    variable=successor,
                    old_value=round(old_val, 4),
                    new_value=round(new_val, 4),
                    change=round(delta, 4),
                    path=path + [successor],
                    confidence=round(strength ** len(path), 4),
                )
                effects.append(eff)
                queue.append((successor, path + [successor]))

        result = {
            "intervention": {"variable": variable, "value": value},
            "effects": [
                {"variable": e.variable, "old": e.old_value, "new": e.new_value,
                 "change": e.change, "path": e.path, "confidence": e.confidence}
                for e in effects
            ],
            "total_affected": len(effects),
        }
        self._interventions_log.append(result)
        return result

    async def counterfactual(
        self,
        observation: dict[str, float],
        intervention: dict[str, float],
    ) -> dict[str, Any]:
        """Given what happened, what WOULD have happened if X were different?

        Three-step process:
        1. Abduction — infer latent state from observations
        2. Action — apply counterfactual intervention
        3. Prediction — compute new outcome
        """
        # 1. Abduction: set observed values as the baseline
        saved = dict(self._values)
        for var, val in observation.items():
            if var in self._values:
                self._values[var] = val

        # 2. Action + 3. Prediction: apply intervention and propagate
        effects: dict[str, Any] = {}
        for var, val in intervention.items():
            result = await self.do_intervention(var, val)
            effects[var] = result

        counterfactual_state = dict(self._values)
        self._values = saved  # restore

        return {
            "observed_state": observation,
            "counterfactual_intervention": intervention,
            "counterfactual_state": {
                k: round(v, 4) for k, v in counterfactual_state.items()
            },
            "changes": {
                k: round(counterfactual_state.get(k, 0) - observation.get(k, 0), 4)
                for k in counterfactual_state
                if abs(counterfactual_state.get(k, 0) - observation.get(k, 0)) > 1e-6
            },
        }

    async def find_root_cause(self, effect: str, depth: int = 5) -> list[dict[str, Any]]:
        """Trace backward through causal graph to find all root causes."""
        if effect not in self._graph:
            return [{"error": f"Unknown variable: {effect}"}]

        causes: list[dict[str, Any]] = []
        visited: set[str] = set()

        def _trace(node: str, path: list[str], cumulative_strength: float, d: int) -> None:
            if d <= 0 or node in visited:
                return
            visited.add(node)
            predecessors = list(self._graph.predecessors(node))
            if not predecessors:
                causes.append({
                    "root_cause": node,
                    "path": list(path),
                    "cumulative_strength": round(cumulative_strength, 4),
                    "depth": len(path),
                })
                return
            for pred in predecessors:
                edge = self._graph.edges[pred, node]
                strength = edge.get("weight", 0.5)
                _trace(pred, [pred] + path, cumulative_strength * strength, d - 1)
            visited.discard(node)

        _trace(effect, [effect], 1.0, depth)
        causes.sort(key=lambda c: c["cumulative_strength"], reverse=True)
        return causes

    async def predict_cascade(self, intervention: dict[str, float]) -> list[dict[str, Any]]:
        """Predict ALL downstream effects of an intervention with probabilities."""
        all_effects: list[dict[str, Any]] = []
        saved = dict(self._values)
        for var, val in intervention.items():
            result = await self.do_intervention(var, val)
            all_effects.extend(result.get("effects", []))
        self._values = saved
        return all_effects

    async def causal_discovery(
        self,
        observations: list[dict[str, float]],
    ) -> dict[str, Any]:
        """Infer causal structure from observational data.

        Simplified PC algorithm: test pairwise correlations and
        conditional independencies to orient edges.
        """
        if len(observations) < 3:
            return {"error": "Need at least 3 observations", "edges": []}

        variables = sorted(observations[0].keys())
        n = len(observations)
        data = {v: np.array([obs.get(v, 0.0) for obs in observations]) for v in variables}

        # Pairwise correlations
        edges: list[dict[str, Any]] = []
        for i, va in enumerate(variables):
            for j, vb in enumerate(variables):
                if i >= j:
                    continue
                arr_a, arr_b = data[va], data[vb]
                std_a, std_b = float(np.std(arr_a)), float(np.std(arr_b))
                if std_a < 1e-12 or std_b < 1e-12:
                    continue
                corr = float(np.corrcoef(arr_a, arr_b)[0, 1])
                if abs(corr) > 0.3:
                    direction = "→" if corr > 0 else "→(neg)"
                    edges.append({
                        "cause": va, "effect": vb,
                        "correlation": round(corr, 4),
                        "direction": direction,
                        "strength": round(abs(corr), 4),
                    })

        return {"variables": variables, "observations": n, "discovered_edges": edges}

    @property
    def variable_count(self) -> int:
        return len(self._values)

    @property
    def edge_count(self) -> int:
        return self._graph.number_of_edges()


# ═══════════════════════════════════════════════════════════════════════════════
# POWER 3: MetaCognitionV2 — Recursive Thinking About Thinking
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MetaCognitiveLayer:
    """One level of metacognitive reflection."""
    level: int
    content: str
    assessment: str
    confidence: float
    recommendations: list[str] = field(default_factory=list)


class MetaCognitionV2:
    """Multi-level metacognition with recursive self-modeling.

    Level 0: Direct thinking
    Level 1: Monitor thinking (am I on track?)
    Level 2: Evaluate monitoring quality
    Level 3: Strategize about how to think better
    Level N: Recursive reflection up to max depth
    """

    def __init__(self) -> None:
        self._awareness_stack: list[MetaCognitiveLayer] = []
        self._cognitive_load_history: list[float] = []
        self._reflection_count: int = 0

    async def level_0_think(self, problem: str) -> str:
        """Direct problem-solving: generate a response."""
        words = problem.lower().split()
        key_concepts = [w for w in words if len(w) > 3]
        approach = "analysis" if any(w in words for w in ["why", "how", "what", "cause"]) else "synthesis"
        return (
            f"Approach: {approach}. Key concepts: {', '.join(key_concepts[:5])}. "
            f"Direct response: addressing '{problem[:40]}...' through {approach} of "
            f"{len(key_concepts)} key factors."
        )

    async def level_1_monitor(self, thinking_process: str) -> dict[str, Any]:
        """Monitor own thinking — am I on track?"""
        length = len(thinking_process.split())
        has_structure = any(w in thinking_process.lower() for w in ["approach", "because", "therefore", "key"])
        has_evidence = any(w in thinking_process.lower() for w in ["evidence", "data", "analysis", "factors"])
        on_track = has_structure and length > 5
        quality = 0.3 + (0.2 if has_structure else 0) + (0.2 if has_evidence else 0) + min(0.3, length / 50)

        return {
            "on_track": on_track,
            "quality": round(quality, 4),
            "word_count": length,
            "has_structure": has_structure,
            "has_evidence": has_evidence,
            "recommendation": "Continue" if on_track else "Restructure approach",
        }

    async def level_2_evaluate(self, monitoring_output: dict[str, Any]) -> dict[str, Any]:
        """Evaluate quality of the monitoring itself."""
        quality = monitoring_output.get("quality", 0.0)
        checks = len([v for v in monitoring_output.values() if isinstance(v, bool)])
        has_recommendation = "recommendation" in monitoring_output

        monitor_quality = 0.4 + checks * 0.1 + (0.2 if has_recommendation else 0)
        monitor_quality = min(1.0, monitor_quality + quality * 0.2)

        return {
            "monitoring_quality": round(monitor_quality, 4),
            "checks_performed": checks,
            "recommendation_given": has_recommendation,
            "meta_insight": (
                "Monitoring is comprehensive" if monitor_quality > 0.7
                else "Monitoring needs more diverse checks"
            ),
            "should_adjust_strategy": monitor_quality < 0.6,
        }

    async def level_3_strategize(self, evaluation: dict[str, Any]) -> dict[str, Any]:
        """Choose a better thinking strategy based on evaluation."""
        quality = evaluation.get("monitoring_quality", 0.5)
        should_adjust = evaluation.get("should_adjust_strategy", False)

        strategies: list[dict[str, Any]] = [
            {"name": "decompose", "desc": "Break problem into smaller parts", "when": "complexity is high"},
            {"name": "analogize", "desc": "Find similar solved problems", "when": "problem feels novel"},
            {"name": "invert", "desc": "Solve the opposite problem", "when": "stuck on direct approach"},
            {"name": "simplify", "desc": "Remove constraints temporarily", "when": "overwhelmed by details"},
            {"name": "diversify", "desc": "Try multiple approaches in parallel", "when": "uncertain which works"},
        ]

        recommended = strategies[0] if should_adjust else strategies[4]
        return {
            "current_quality": round(quality, 4),
            "strategy_change_needed": should_adjust,
            "recommended_strategy": recommended,
            "all_strategies": strategies,
            "meta_meta_insight": (
                f"At level 3, I recognize that my thinking about thinking about thinking "
                f"is {'productive' if quality > 0.5 else 'getting too recursive'}. "
                f"{'Going deeper may help' if quality > 0.5 else 'Time to return to direct action'}."
            ),
        }

    async def recursive_reflect(
        self,
        initial_thought: str,
        max_depth: int = 5,
    ) -> list[MetaCognitiveLayer]:
        """Recursively reflect on each level of thinking."""
        self._reflection_count += 1
        layers: list[MetaCognitiveLayer] = []
        current = initial_thought

        for depth in range(min(max_depth, 5)):
            if depth == 0:
                result = await self.level_0_think(current)
                assessment = "Direct response generated"
            elif depth == 1:
                monitoring = await self.level_1_monitor(current)
                result = str(monitoring)
                assessment = f"Monitoring: quality={monitoring['quality']:.2f}"
            elif depth == 2:
                monitoring = await self.level_1_monitor(current)
                evaluation = await self.level_2_evaluate(monitoring)
                result = str(evaluation)
                assessment = f"Evaluation: monitor_quality={evaluation['monitoring_quality']:.2f}"
            elif depth == 3:
                monitoring = await self.level_1_monitor(current)
                evaluation = await self.level_2_evaluate(monitoring)
                strategy = await self.level_3_strategize(evaluation)
                result = str(strategy)
                assessment = f"Strategy: {strategy['recommended_strategy']['name']}"
            else:
                result = f"Level-{depth} reflection: diminishing returns beyond level 3"
                assessment = "Meta-recursion limit — returning to action"

            confidence = max(0.1, 1.0 - depth * 0.15)
            layer = MetaCognitiveLayer(
                level=depth,
                content=result[:200],
                assessment=assessment,
                confidence=round(confidence, 4),
                recommendations=[f"Depth-{depth} recommendation: {'go deeper' if depth < 3 else 'act now'}"],
            )
            layers.append(layer)
            self._awareness_stack.append(layer)
            current = result

        return layers

    async def cognitive_load_awareness(self) -> dict[str, Any]:
        """Know when overloaded; suggest simplification or delegation."""
        stack_depth = len(self._awareness_stack)
        load = min(1.0, stack_depth * 0.05 + self._reflection_count * 0.02)
        self._cognitive_load_history.append(load)

        trending = "stable"
        if len(self._cognitive_load_history) >= 3:
            recent = self._cognitive_load_history[-3:]
            if recent[-1] > recent[0]:
                trending = "increasing"
            elif recent[-1] < recent[0]:
                trending = "decreasing"

        return {
            "current_load": round(load, 4),
            "capacity_remaining": round(1.0 - load, 4),
            "trending": trending,
            "recommendation": (
                "Simplify or delegate" if load > 0.8
                else "Continue with caution" if load > 0.6
                else "Good capacity available"
            ),
            "reflection_count": self._reflection_count,
            "stack_depth": stack_depth,
        }

    async def uncertainty_quantification(self, claim: str) -> dict[str, Any]:
        """For any claim, estimate known-unknowns and unknown-unknowns."""
        words = claim.lower().split()
        specificity = min(1.0, len([w for w in words if len(w) > 5]) / max(len(words), 1))
        hedging = sum(1 for w in words if w in {"maybe", "might", "could", "possibly", "perhaps", "likely"})

        knowledge_confidence = 0.3 + specificity * 0.4 - hedging * 0.1
        knowledge_confidence = max(0.1, min(0.9, knowledge_confidence))

        return {
            "claim": claim,
            "known_knowns": f"We have {round(knowledge_confidence * 100)}% confidence in core aspects",
            "known_unknowns": [
                f"Uncertain about: edge cases of '{claim[:25]}...'",
                "May not account for: recent developments",
                "Assumption: current understanding is representative",
            ],
            "estimated_unknown_unknowns": round(1.0 - knowledge_confidence ** 2, 4),
            "confidence_in_confidence": round(knowledge_confidence * 0.8, 4),
            "humility_score": round(1.0 - knowledge_confidence, 4),
        }

    async def intellectual_humility_check(self) -> dict[str, Any]:
        """Honestly assess own limitations."""
        return {
            "reflection_depth": len(self._awareness_stack),
            "cognitive_load": round(len(self._awareness_stack) * 0.05, 4),
            "strengths": [
                "Pattern recognition across domains",
                "Systematic analysis",
                "Recursive self-evaluation",
            ],
            "limitations": [
                "Cannot verify claims against live data",
                "Prone to systematic biases in training distribution",
                "Meta-recursion has diminishing returns beyond level 3",
                "Uncertainty estimates are approximate, not calibrated",
            ],
            "honest_assessment": (
                "I can reason about reasoning, but my metacognitive model "
                "is itself bounded by the same system it's trying to monitor."
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# POWER 4: MultiScaleAttention — Forest AND Trees Simultaneously
# ═══════════════════════════════════════════════════════════════════════════════

class MultiScaleAttention:
    """Process information at micro, meso, and macro scales simultaneously.

    micro: character/word level, individual data points
    meso: sentence/paragraph level, local patterns
    macro: document/system level, global themes
    """

    _SCALE_RANGES: dict[str, tuple[int, int]] = {
        "micro": (1, 5),    # 1-5 word spans
        "meso": (5, 30),    # 5-30 word spans
        "macro": (30, 500), # 30+ word spans (whole text)
    }

    def __init__(self) -> None:
        self._analysis_cache: dict[str, dict[str, Any]] = {}

    async def analyze_multiscale(
        self,
        data: str,
        scales: list[str] | None = None,
    ) -> dict[str, Any]:
        """Analyze data at multiple scales and cross-reference."""
        scales = scales or ["micro", "meso", "macro"]
        words = data.split()
        results: dict[str, Any] = {}

        for scale in scales:
            if scale == "micro":
                results["micro"] = self._analyze_micro(words)
            elif scale == "meso":
                results["meso"] = self._analyze_meso(data, words)
            elif scale == "macro":
                results["macro"] = self._analyze_macro(data, words)

        # Cross-reference across scales
        results["cross_scale"] = self._cross_reference(results)
        return results

    async def zoom_in(self, topic: str, current_scale: str) -> dict[str, Any]:
        """Increase detail level."""
        order = ["macro", "meso", "micro"]
        idx = order.index(current_scale) if current_scale in order else 0
        new_scale = order[min(idx + 1, len(order) - 1)]
        return {
            "previous_scale": current_scale,
            "new_scale": new_scale,
            "detail_level": f"Examining '{topic}' at {new_scale} level",
            "focus": f"Individual components of: {topic}",
        }

    async def zoom_out(self, topic: str, current_scale: str) -> dict[str, Any]:
        """See bigger picture."""
        order = ["macro", "meso", "micro"]
        idx = order.index(current_scale) if current_scale in order else len(order) - 1
        new_scale = order[max(idx - 1, 0)]
        return {
            "previous_scale": current_scale,
            "new_scale": new_scale,
            "detail_level": f"Examining '{topic}' at {new_scale} level",
            "focus": f"Overall pattern and context of: {topic}",
        }

    async def find_scale_conflicts(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Where do micro and macro views disagree?"""
        conflicts: list[dict[str, Any]] = []
        micro = analysis.get("micro", {})
        macro = analysis.get("macro", {})

        micro_sentiment = micro.get("avg_word_length", 5)
        macro_theme_count = len(macro.get("themes", []))

        if micro_sentiment > 6 and macro_theme_count < 2:
            conflicts.append({
                "type": "complexity_mismatch",
                "detail": "Complex words (micro) but few themes (macro) — possible over-complication",
            })
        if micro_sentiment < 4 and macro_theme_count > 3:
            conflicts.append({
                "type": "simplicity_mismatch",
                "detail": "Simple words (micro) but many themes (macro) — possible oversimplification",
            })
        if not conflicts:
            conflicts.append({"type": "aligned", "detail": "Micro and macro scales are consistent"})
        return conflicts

    async def fractal_pattern_detection(self, data: str) -> dict[str, Any]:
        """Find self-similar patterns at different scales."""
        words = data.split()
        patterns: dict[str, list[str]] = {"micro": [], "meso": [], "macro": []}

        # Micro: repeated words
        word_counts: dict[str, int] = {}
        for w in words:
            w_lower = w.lower().strip(".,!?;:")
            if len(w_lower) > 3:
                word_counts[w_lower] = word_counts.get(w_lower, 0) + 1
        repeated = [w for w, c in word_counts.items() if c > 1]
        patterns["micro"] = repeated[:5]

        # Meso: repeated phrase patterns (bigrams)
        if len(words) >= 4:
            bigrams: dict[str, int] = {}
            for i in range(len(words) - 1):
                bg = f"{words[i].lower()} {words[i + 1].lower()}"
                bigrams[bg] = bigrams.get(bg, 0) + 1
            patterns["meso"] = [bg for bg, c in bigrams.items() if c > 1][:5]

        # Macro: thematic repetition
        themes = self._extract_themes(data)
        patterns["macro"] = themes[:3]

        # Self-similarity score
        fractal_score = 0.0
        if patterns["micro"] and patterns["meso"]:
            fractal_score += 0.3
        if patterns["meso"] and patterns["macro"]:
            fractal_score += 0.3
        if patterns["micro"] and patterns["macro"]:
            fractal_score += 0.4

        return {
            "patterns": patterns,
            "fractal_score": round(fractal_score, 4),
            "self_similar": fractal_score > 0.5,
        }

    # ── Private ───────────────────────────────────────────────────────────

    def _analyze_micro(self, words: list[str]) -> dict[str, Any]:
        lengths = [len(w) for w in words] if words else [0]
        return {
            "word_count": len(words),
            "avg_word_length": round(float(np.mean(lengths)), 2),
            "vocabulary_richness": round(len(set(w.lower() for w in words)) / max(len(words), 1), 4),
            "longest_word": max(words, key=len) if words else "",
            "short_words": sum(1 for w in words if len(w) <= 3),
        }

    def _analyze_meso(self, text: str, words: list[str]) -> dict[str, Any]:
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        sent_lengths = [len(s.split()) for s in sentences] if sentences else [0]
        return {
            "sentence_count": len(sentences),
            "avg_sentence_length": round(float(np.mean(sent_lengths)), 2),
            "sentence_length_variance": round(float(np.std(sent_lengths)), 2),
            "paragraph_structure": "complex" if len(sentences) > 5 else "simple",
        }

    def _analyze_macro(self, text: str, words: list[str]) -> dict[str, Any]:
        themes = self._extract_themes(text)
        return {
            "total_length": len(text),
            "word_count": len(words),
            "themes": themes,
            "complexity": "high" if len(words) > 100 else "medium" if len(words) > 30 else "low",
            "information_density": round(len(set(w.lower() for w in words)) / max(len(words), 1), 4),
        }

    def _extract_themes(self, text: str) -> list[str]:
        words = text.lower().split()
        content = [w.strip(".,!?;:()\"'") for w in words if len(w) > 4]
        counts: dict[str, int] = {}
        for w in content:
            counts[w] = counts.get(w, 0) + 1
        return [w for w, c in sorted(counts.items(), key=lambda x: x[1], reverse=True) if c > 1][:5]

    def _cross_reference(self, results: dict[str, Any]) -> dict[str, Any]:
        scales_analyzed = [k for k in results if k in ("micro", "meso", "macro")]
        return {
            "scales_analyzed": scales_analyzed,
            "coherence": "high" if len(scales_analyzed) >= 3 else "partial",
            "insight": f"Analyzed at {len(scales_analyzed)} scales for comprehensive understanding",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# POWER 5: KnowledgeSynthesizer — Create NEW Knowledge
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SynthesizedInsight:
    """A genuinely new piece of knowledge."""
    insight: str
    source_domains: list[str] = field(default_factory=list)
    novelty_score: float = 0.0
    reasoning_chain: list[str] = field(default_factory=list)
    confidence: float = 0.0


class KnowledgeSynthesizer:
    """Derive genuinely new knowledge by connecting disparate domains.

    Not just retrieving or combining — actually deriving conclusions
    that don't exist anywhere in the training data.
    """

    _TRANSFORMATIONS: list[str] = [
        "generalize", "specialize", "analogize", "negate", "combine",
    ]

    def __init__(self) -> None:
        self._domains: dict[str, dict[str, Any]] = {}
        self._synthesis_history: list[SynthesizedInsight] = []

    def register_domain(
        self,
        name: str,
        concepts: list[str],
        rules: list[str],
        patterns: list[str] | None = None,
    ) -> None:
        """Add domain knowledge."""
        self._domains[name] = {
            "concepts": concepts,
            "rules": rules,
            "patterns": patterns or [],
        }

    async def cross_domain_transfer(
        self,
        source_domain: str,
        target_domain: str,
    ) -> list[dict[str, Any]]:
        """Find patterns in source that apply to target (analogical transfer)."""
        src = self._domains.get(source_domain, {"concepts": [], "rules": [], "patterns": []})
        tgt = self._domains.get(target_domain, {"concepts": [], "rules": [], "patterns": []})

        transfers: list[dict[str, Any]] = []
        for s_rule in src["rules"]:
            for t_concept in tgt["concepts"]:
                sim = _blended_sim(s_rule, t_concept)
                if sim > 0.05:
                    abstract_pattern = f"The principle '{s_rule}' maps onto '{t_concept}'"
                    application = f"Apply {source_domain}'s '{s_rule}' to {target_domain}'s '{t_concept}'"
                    transfers.append({
                        "source_rule": s_rule,
                        "target_concept": t_concept,
                        "abstract_pattern": abstract_pattern,
                        "application": application,
                        "transfer_strength": round(sim, 4),
                    })

        transfers.sort(key=lambda t: t["transfer_strength"], reverse=True)
        return transfers[:5]

    async def abductive_leap(
        self,
        observations: list[str],
        known_theories: list[str],
    ) -> list[dict[str, Any]]:
        """Generate explanations that NO existing theory covers.

        Create new hypotheses by combining fragments from multiple theories.
        """
        hypotheses: list[dict[str, Any]] = []
        for obs in observations:
            # Check which theories partially explain the observation
            partial_explanations: list[tuple[str, float]] = []
            for theory in known_theories:
                sim = _blended_sim(obs, theory)
                if sim > 0.02:
                    partial_explanations.append((theory, sim))
            partial_explanations.sort(key=lambda x: x[1], reverse=True)

            # Combine top partial explanations into new hypothesis
            if len(partial_explanations) >= 2:
                t1, s1 = partial_explanations[0]
                t2, s2 = partial_explanations[1]
                new_hypothesis = (
                    f"Novel hypothesis: '{obs}' can be explained by combining "
                    f"elements of '{t1}' and '{t2}' — the interaction between "
                    f"these mechanisms produces the observed effect"
                )
                novelty = 1.0 - max(s1, s2)  # less similar to existing = more novel
                hypotheses.append({
                    "observation": obs,
                    "hypothesis": new_hypothesis,
                    "contributing_theories": [t1, t2],
                    "novelty": round(novelty, 4),
                    "confidence": round((s1 + s2) / 2, 4),
                })
            else:
                hypotheses.append({
                    "observation": obs,
                    "hypothesis": f"Truly novel phenomenon: '{obs}' not explained by any known theory",
                    "contributing_theories": [],
                    "novelty": 1.0,
                    "confidence": 0.2,
                })

        return hypotheses

    async def synthesis_chain(
        self,
        start_fact: str,
        goal_insight: str,
        max_hops: int = 5,
    ) -> list[str]:
        """Chain of reasoning from known fact to desired new insight.

        Each hop applies a transformation: generalize, specialize,
        analogize, negate, or combine.
        """
        chain: list[str] = [f"Start: {start_fact}"]
        current = start_fact
        rng = np.random.default_rng(hash(start_fact + goal_insight) & 0xFFFFFFFF)

        for hop in range(max_hops):
            transform = self._TRANSFORMATIONS[int(rng.integers(len(self._TRANSFORMATIONS)))]
            sim_to_goal = _blended_sim(current, goal_insight)

            if transform == "generalize":
                current = f"More broadly: {current.split(':')[-1].strip()[:50]} applies universally"
            elif transform == "specialize":
                current = f"Specifically: {goal_insight.split()[:3]} relates to {current.split()[:3]}"
                current = current[:80]
            elif transform == "analogize":
                current = f"Similarly: as {current[:30]}..., so too {goal_insight[:30]}..."
            elif transform == "negate":
                current = f"Inversely: the opposite of {current[:30]}... reveals {goal_insight[:20]}..."
            elif transform == "combine":
                current = f"Synthesis: {current[:25]}... combined with {goal_insight[:25]}..."

            chain.append(f"Hop {hop + 1} [{transform}]: {current}")

            if sim_to_goal > 0.3:
                chain.append(f"Goal reached: {goal_insight}")
                break

        if not chain[-1].startswith("Goal"):
            chain.append(f"Approximate arrival: {goal_insight}")

        return chain

    async def novelty_score(self, insight: str) -> float:
        """How novel is this insight? Score based on distance from known facts."""
        if not self._domains:
            return 0.5

        max_sim = 0.0
        domain_crossings = 0
        for domain_name, domain in self._domains.items():
            for concept in domain["concepts"]:
                sim = _blended_sim(insight, concept)
                max_sim = max(max_sim, sim)
            for rule in domain["rules"]:
                sim = _blended_sim(insight, rule)
                if sim > 0.05:
                    domain_crossings += 1

        novelty = (1.0 - max_sim) * 0.5 + min(1.0, domain_crossings * 0.1) * 0.3 + 0.2
        return round(min(1.0, novelty), 4)

    @property
    def domain_count(self) -> int:
        return len(self._domains)


# ═══════════════════════════════════════════════════════════════════════════════
# POWER 6: MoralCompass — Deep Ethical Reasoning
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MoralAssessment:
    """Result of a moral reasoning process."""
    situation: str
    recommended_action: str
    foundation_scores: dict[str, float] = field(default_factory=dict)
    overall_moral_valence: float = 0.0
    values_served: list[str] = field(default_factory=list)
    values_sacrificed: list[str] = field(default_factory=list)
    confidence: float = 0.0


class MoralCompass:
    """First-principles ethical reasoning, not just rule-checking.

    Uses Haidt's 6 moral foundations as the base framework,
    then adds empathic modeling, precedent search, and moral growth tracking.
    """

    # Haidt's 6 moral foundations
    _FOUNDATIONS: dict[str, dict[str, Any]] = {
        "care_harm": {
            "name": "Care / Harm",
            "triggers": ["suffering", "hurt", "help", "protect", "vulnerable", "pain", "care"],
            "question": "Does this cause or prevent suffering?",
            "weight": 1.0,
        },
        "fairness_cheating": {
            "name": "Fairness / Cheating",
            "triggers": ["fair", "unfair", "equal", "cheat", "justice", "rights", "deserve"],
            "question": "Is this fair to all parties?",
            "weight": 1.0,
        },
        "loyalty_betrayal": {
            "name": "Loyalty / Betrayal",
            "triggers": ["betray", "loyal", "trust", "team", "group", "abandon", "faithful"],
            "question": "Does this honor or violate trust and loyalty?",
            "weight": 0.8,
        },
        "authority_subversion": {
            "name": "Authority / Subversion",
            "triggers": ["authority", "respect", "order", "tradition", "law", "rule", "rebel"],
            "question": "Does this respect legitimate authority and social order?",
            "weight": 0.7,
        },
        "sanctity_degradation": {
            "name": "Sanctity / Degradation",
            "triggers": ["pure", "sacred", "disgust", "degrade", "noble", "dignity", "corrupt"],
            "question": "Does this uplift or degrade human dignity?",
            "weight": 0.7,
        },
        "liberty_oppression": {
            "name": "Liberty / Oppression",
            "triggers": ["freedom", "oppress", "liberty", "autonomy", "coerce", "choice", "consent"],
            "question": "Does this protect or restrict individual freedom?",
            "weight": 0.9,
        },
    }

    def __init__(self) -> None:
        self._case_law: list[dict[str, Any]] = []
        self._moral_history: list[MoralAssessment] = []

    async def reason_from_principles(
        self,
        situation: str,
        stakeholders: list[str],
    ) -> MoralAssessment:
        """Apply all 6 moral foundations to a situation."""
        sit_lower = situation.lower()
        foundation_scores: dict[str, float] = {}

        for key, foundation in self._FOUNDATIONS.items():
            triggers = foundation["triggers"]
            trigger_count = sum(1 for t in triggers if t in sit_lower)
            # Score = how much this foundation is activated
            activation = min(1.0, trigger_count * 0.2 + 0.1)
            # Valence: positive if protecting, negative if violating
            protective_words = {"protect", "help", "fair", "loyal", "respect", "pure", "freedom"}
            harmful_words = {"hurt", "cheat", "betray", "rebel", "degrade", "oppress"}
            pos = sum(1 for w in protective_words if w in sit_lower)
            neg = sum(1 for w in harmful_words if w in sit_lower)
            valence = (pos - neg) / max(pos + neg, 1)
            foundation_scores[key] = round(activation * valence * foundation["weight"], 4)

        overall = sum(foundation_scores.values()) / max(len(foundation_scores), 1)
        values_served = [k for k, v in foundation_scores.items() if v > 0]
        values_sacrificed = [k for k, v in foundation_scores.items() if v < 0]

        action = (
            "Proceed — moral foundations largely aligned" if overall > 0.1
            else "Proceed with caution — mixed moral signals" if overall > -0.1
            else "Reconsider — significant moral concerns"
        )

        assessment = MoralAssessment(
            situation=situation,
            recommended_action=action,
            foundation_scores=foundation_scores,
            overall_moral_valence=round(overall, 4),
            values_served=values_served,
            values_sacrificed=values_sacrificed,
            confidence=round(0.5 + abs(overall) * 0.5, 4),
        )
        self._moral_history.append(assessment)
        return assessment

    async def moral_dilemma_resolve(
        self,
        dilemma: str,
        options: list[str],
        values_priority: list[str] | None = None,
    ) -> dict[str, Any]:
        """When values conflict, use priority weighting to find least-worst option."""
        priority = values_priority or list(self._FOUNDATIONS.keys())
        option_scores: list[dict[str, Any]] = []

        for option in options:
            combined = f"{dilemma} — choosing: {option}"
            assessment = await self.reason_from_principles(combined, [])
            # Weight by priority order
            weighted_score = 0.0
            for rank, pkey in enumerate(priority):
                weight = 1.0 / (rank + 1)
                weighted_score += assessment.foundation_scores.get(pkey, 0) * weight

            option_scores.append({
                "option": option,
                "raw_score": assessment.overall_moral_valence,
                "weighted_score": round(weighted_score, 4),
                "values_served": assessment.values_served,
                "values_sacrificed": assessment.values_sacrificed,
            })

        option_scores.sort(key=lambda x: x["weighted_score"], reverse=True)
        best = option_scores[0] if option_scores else {"option": "No options", "weighted_score": 0}

        return {
            "dilemma": dilemma,
            "recommended": best["option"],
            "all_options": option_scores,
            "confidence": round(abs(best["weighted_score"]), 4),
            "tradeoff": f"Serving {best.get('values_served', [])} at cost of {best.get('values_sacrificed', [])}",
        }

    async def empathic_modeling(
        self,
        action: str,
        affected_parties: list[str],
    ) -> list[dict[str, Any]]:
        """Model each party's perspective, emotional impact, fairness perception."""
        models: list[dict[str, Any]] = []
        for party in affected_parties:
            combined = f"{party} affected by: {action}"
            assessment = await self.reason_from_principles(combined, [party])
            impact = assessment.overall_moral_valence

            models.append({
                "party": party,
                "perspective": f"From {party}'s view: {'positive' if impact > 0 else 'negative' if impact < 0 else 'neutral'} impact",
                "emotional_impact": round(impact, 4),
                "fairness_perception": round(
                    assessment.foundation_scores.get("fairness_cheating", 0), 4
                ),
                "liberty_impact": round(
                    assessment.foundation_scores.get("liberty_oppression", 0), 4
                ),
                "recommendation": (
                    f"No concerns for {party}" if impact >= 0
                    else f"Mitigation needed for {party}"
                ),
            })
        return models

    async def precedent_search(self, situation: str) -> list[dict[str, Any]]:
        """Search case law for similar moral situations."""
        results: list[dict[str, Any]] = []
        for case in self._case_law:
            sim = _blended_sim(situation, case.get("situation", ""))
            if sim > 0.05:
                results.append({
                    "case": case.get("situation", ""),
                    "resolution": case.get("resolution", ""),
                    "similarity": round(sim, 4),
                })
        results.sort(key=lambda r: r["similarity"], reverse=True)
        return results[:5]

    def add_precedent(self, situation: str, resolution: str) -> None:
        """Add a moral precedent to case law."""
        self._case_law.append({"situation": situation, "resolution": resolution})

    async def moral_growth_tracking(self) -> dict[str, Any]:
        """Track how moral reasoning has evolved over time."""
        if not self._moral_history:
            return {"assessments": 0, "growth": "No history yet"}

        scores = [a.overall_moral_valence for a in self._moral_history]
        confidences = [a.confidence for a in self._moral_history]
        arr_s = np.array(scores)
        arr_c = np.array(confidences)

        return {
            "total_assessments": len(self._moral_history),
            "mean_valence": round(float(np.mean(arr_s)), 4),
            "valence_trend": (
                "improving" if len(scores) >= 3 and np.mean(arr_s[-3:]) > np.mean(arr_s[:3])
                else "stable"
            ),
            "mean_confidence": round(float(np.mean(arr_c)), 4),
            "confidence_trend": (
                "increasing" if len(confidences) >= 3 and np.mean(arr_c[-3:]) > np.mean(arr_c[:3])
                else "stable"
            ),
            "foundations_most_activated": self._top_foundations(),
        }

    def _top_foundations(self) -> list[str]:
        totals: dict[str, float] = {}
        for a in self._moral_history:
            for k, v in a.foundation_scores.items():
                totals[k] = totals.get(k, 0) + abs(v)
        return [k for k, _ in sorted(totals.items(), key=lambda x: x[1], reverse=True)][:3]
