"""
Self-Improvement Engine (EDITH v2.0) — PRADYSAGICAN
Gödel Agent recursive self-improvement with learning episodes,
skill trees, heuristic distillation, and meta-learning.
Based on "Gödel Agent" (Yin et al. 2025) and Darwin Gödel Machine (Sakana AI).
"""
from __future__ import annotations

import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class LearningEpisode:
    """Record of a learning experience with outcome and extracted lessons."""
    id: str
    task: str
    actions: list[str]
    outcome: str
    success: bool
    reward: float = 0.0
    lessons: list[str] = field(default_factory=list)
    difficulty: float = 0.5  # 0 = trivial, 1 = very hard
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillNode:
    """A node in the skill tree."""
    name: str
    level: int = 0  # 0=novice, 5=expert
    xp: float = 0.0
    xp_to_next: float = 100.0
    parent: str | None = None
    children: list[str] = field(default_factory=list)
    unlocked: bool = True


@dataclass
class Heuristic:
    """A learned rule-of-thumb distilled from experience."""
    id: str
    rule: str
    context: str  # when to apply
    confidence: float
    times_applied: int = 0
    times_succeeded: int = 0
    created_from: list[str] = field(default_factory=list)  # episode IDs


@dataclass
class SelfModification:
    """Record of a self-referential code/config modification."""
    id: str
    target: str  # what was modified
    change_description: str
    before_score: float
    after_score: float
    accepted: bool = False
    timestamp: float = field(default_factory=time.time)


# ── Skill Tree ───────────────────────────────────────────────────────────────

class SkillTree:
    """Hierarchical skill progression with XP and leveling."""

    def __init__(self) -> None:
        self._nodes: dict[str, SkillNode] = {}

    def add_skill(
        self,
        name: str,
        parent: str | None = None,
        unlocked: bool = True,
    ) -> SkillNode:
        """Register a new skill in the tree."""
        node = SkillNode(name=name, parent=parent, unlocked=unlocked)
        self._nodes[name] = node
        if parent and parent in self._nodes:
            self._nodes[parent].children.append(name)
        return node

    async def gain_xp(self, skill_name: str, amount: float) -> dict[str, Any]:
        """Award XP to a skill; auto-level-up when threshold reached."""
        node = self._nodes.get(skill_name)
        if not node or not node.unlocked:
            return {"error": f"Skill '{skill_name}' not found or locked"}

        node.xp += amount
        leveled_up = False
        while node.xp >= node.xp_to_next and node.level < 5:
            node.xp -= node.xp_to_next
            node.level += 1
            node.xp_to_next *= 1.5  # exponential scaling
            leveled_up = True
            # Unlock children on level 2+
            if node.level >= 2:
                for child_name in node.children:
                    if child_name in self._nodes:
                        self._nodes[child_name].unlocked = True

        return {
            "skill": skill_name,
            "level": node.level,
            "xp": round(node.xp, 1),
            "xp_to_next": round(node.xp_to_next, 1),
            "leveled_up": leveled_up,
        }

    def skill_profile(self) -> dict[str, dict[str, Any]]:
        """Return full skill tree state."""
        return {
            name: {
                "level": node.level,
                "xp": round(node.xp, 1),
                "unlocked": node.unlocked,
                "children": node.children,
            }
            for name, node in self._nodes.items()
        }

    @property
    def total_level(self) -> int:
        return sum(n.level for n in self._nodes.values())


# ── Self-Improvement Engine ──────────────────────────────────────────────────

class SelfImprovementEngine:
    """EDITH v2.0 — Recursive self-improvement through reflection.

    Features:
    - Learning episode recording with reward signals
    - Heuristic distillation from experience
    - Skill tree with XP-based progression
    - Performance trend analysis with change-point detection
    - Meta-learning: learn HOW to learn better
    - Self-modification proposals (Gödel Agent pattern)
    """

    def __init__(self) -> None:
        self._episodes: list[LearningEpisode] = []
        self._heuristics: dict[str, Heuristic] = {}
        self._performance_log: list[float] = []
        self._modifications: list[SelfModification] = []
        self.skill_tree = SkillTree()
        self._meta_params: dict[str, float] = {
            "learning_rate": 0.1,
            "exploration_rate": 0.3,
            "reflection_depth": 3,
        }

    # ── Learning Episodes ────────────────────────────────────────────────

    async def reflect(
        self,
        task: str,
        actions: list[str],
        outcome: str,
        success: bool,
        difficulty: float = 0.5,
    ) -> LearningEpisode:
        """Reflect on a completed task to extract lessons."""
        reward = self._compute_reward(success, difficulty, len(actions))
        lessons: list[str] = []

        if success:
            lessons.append(f"Effective approach for '{task[:30]}' (difficulty={difficulty:.1f})")
            if len(actions) <= 3:
                lessons.append("Concise action sequence — efficient problem solving")
            if difficulty > 0.7:
                lessons.append("Handled high-difficulty task successfully — skill growth")
        else:
            lessons.append(f"Approach failed for '{task[:30]}' — analyse root cause")
            if len(actions) > 5:
                lessons.append("Long action sequence may indicate floundering — try simplification")
            if difficulty < 0.3:
                lessons.append("Failed easy task — possible knowledge gap or careless error")

        episode = LearningEpisode(
            id=f"ep_{uuid.uuid4().hex[:8]}",
            task=task,
            actions=actions,
            outcome=outcome,
            success=success,
            reward=round(reward, 3),
            lessons=lessons,
            difficulty=difficulty,
        )
        self._episodes.append(episode)
        self._performance_log.append(reward)
        logger.info("Reflected on '%s': success=%s, reward=%.3f", task[:30], success, reward)
        return episode

    def _compute_reward(self, success: bool, difficulty: float, n_actions: int) -> float:
        """Reward shaped by success, difficulty, and efficiency."""
        base = 1.0 if success else -0.5
        difficulty_bonus = difficulty * 0.5 if success else 0.0
        efficiency_bonus = max(0.0, (5 - n_actions) * 0.05) if success else 0.0
        return base + difficulty_bonus + efficiency_bonus

    # ── Heuristic Distillation ───────────────────────────────────────────

    async def distill_heuristics(self, min_episodes: int = 3) -> dict[str, Heuristic]:
        """Extract reusable heuristics from accumulated experience."""
        if len(self._episodes) < min_episodes:
            return {}

        successes = [e for e in self._episodes if e.success]
        failures = [e for e in self._episodes if not e.success]

        # Pattern: optimal action count
        if successes:
            avg_steps = float(np.mean([len(e.actions) for e in successes]))
            h_id = "optimal_steps"
            self._heuristics[h_id] = Heuristic(
                id=h_id,
                rule=f"Successful tasks average {avg_steps:.0f} action steps",
                context="task_planning",
                confidence=min(len(successes) / 10.0, 0.95),
                times_applied=len(successes),
                times_succeeded=len(successes),
                created_from=[e.id for e in successes[:5]],
            )

        # Pattern: failure avoidance
        if failures:
            h_id = "failure_avoidance"
            avg_fail_steps = float(np.mean([len(e.actions) for e in failures]))
            self._heuristics[h_id] = Heuristic(
                id=h_id,
                rule=f"Failures tend to have {avg_fail_steps:.0f} steps — watch for this",
                context="risk_detection",
                confidence=min(len(failures) / 10.0, 0.9),
                times_applied=len(failures),
                times_succeeded=0,
                created_from=[e.id for e in failures[:5]],
            )

        # Pattern: difficulty sweet spot
        if successes:
            difficulties = [e.difficulty for e in successes]
            sweet_spot = float(np.mean(difficulties))
            h_id = "difficulty_sweet_spot"
            self._heuristics[h_id] = Heuristic(
                id=h_id,
                rule=f"Optimal difficulty zone is around {sweet_spot:.2f}",
                context="task_selection",
                confidence=0.6,
                created_from=[e.id for e in successes[:3]],
            )

        # Overall success rate heuristic
        rate = len(successes) / max(len(self._episodes), 1)
        self._heuristics["success_rate"] = Heuristic(
            id="success_rate",
            rule=f"Overall success rate: {rate:.1%}",
            context="self_assessment",
            confidence=min(len(self._episodes) / 20.0, 0.95),
            times_applied=len(self._episodes),
            times_succeeded=len(successes),
        )

        return dict(self._heuristics)

    # ── Performance Analysis ─────────────────────────────────────────────

    async def performance_trend(self) -> dict[str, Any]:
        """Analyse performance improvement over time with trend detection."""
        if len(self._performance_log) < 2:
            return {"trend": "insufficient_data", "total_episodes": len(self._performance_log)}

        log = np.array(self._performance_log)
        n = len(log)
        mid = n // 2

        recent = log[mid:]
        older = log[:mid]

        # Linear regression for trend
        x = np.arange(n, dtype=float)
        slope = float(np.polyfit(x, log, 1)[0])

        # Change-point detection: compare first half vs second half
        mean_diff = float(np.mean(recent)) - float(np.mean(older))

        return {
            "total_episodes": n,
            "recent_mean_reward": round(float(np.mean(recent)), 4),
            "older_mean_reward": round(float(np.mean(older)), 4),
            "improvement": round(mean_diff, 4),
            "improving": mean_diff > 0.05,
            "slope": round(slope, 4),
            "trend": "improving" if slope > 0.01 else "declining" if slope < -0.01 else "stable",
            "cumulative_reward": round(float(np.sum(log)), 4),
        }

    # ── Meta-Learning ────────────────────────────────────────────────────

    async def meta_learn(self) -> dict[str, Any]:
        """Learn HOW to learn better by analysing learning dynamics."""
        if len(self._episodes) < 5:
            return {"status": "insufficient_data"}

        rewards = np.array([e.reward for e in self._episodes])
        difficulties = np.array([e.difficulty for e in self._episodes])

        # Correlation between difficulty and reward
        if np.std(difficulties) > 0 and np.std(rewards) > 0:
            correlation = float(np.corrcoef(difficulties, rewards)[0, 1])
        else:
            correlation = 0.0

        # Adjust meta-parameters
        recent_success = float(np.mean(rewards[-5:]))
        if recent_success > 0.5:
            # Doing well: explore more, learn faster
            self._meta_params["exploration_rate"] = min(self._meta_params["exploration_rate"] + 0.02, 0.6)
            self._meta_params["learning_rate"] = min(self._meta_params["learning_rate"] + 0.01, 0.3)
        else:
            # Struggling: consolidate, slow down
            self._meta_params["exploration_rate"] = max(self._meta_params["exploration_rate"] - 0.02, 0.1)
            self._meta_params["reflection_depth"] = min(self._meta_params["reflection_depth"] + 1, 10)

        return {
            "difficulty_reward_correlation": round(correlation, 4),
            "recent_performance": round(recent_success, 4),
            "meta_params": {k: round(v, 3) for k, v in self._meta_params.items()},
            "recommendation": (
                "Increase challenge level"
                if recent_success > 0.7
                else "Consolidate current skills"
                if recent_success < 0.3
                else "Maintain current approach"
            ),
        }

    # ── Self-Modification (Gödel Agent) ──────────────────────────────────

    async def propose_self_modification(
        self,
        target: str,
        change_description: str,
        before_score: float,
        after_score: float,
    ) -> SelfModification:
        """Propose a self-referential modification with before/after scoring.

        Following the Gödel Agent pattern: only accept modifications
        that demonstrably improve performance.
        """
        accepted = after_score > before_score and (after_score - before_score) > 0.01
        mod = SelfModification(
            id=f"mod_{uuid.uuid4().hex[:8]}",
            target=target,
            change_description=change_description,
            before_score=round(before_score, 4),
            after_score=round(after_score, 4),
            accepted=accepted,
        )
        self._modifications.append(mod)
        logger.info(
            "Self-modification proposed: %s — %s (%.3f → %.3f)",
            target, "ACCEPTED" if accepted else "REJECTED",
            before_score, after_score,
        )
        return mod

    async def evolutionary_search(
        self,
        candidates: list[dict[str, Any]],
        fitness_fn_name: str = "default",
    ) -> dict[str, Any]:
        """Evolutionary search over candidate configurations (Darwin Gödel Machine).

        Scores each candidate, selects top-k, applies mutation.
        """
        if not candidates:
            return {"error": "No candidates provided"}

        rng = np.random.default_rng()

        # Score candidates
        scored: list[tuple[float, dict[str, Any]]] = []
        for c in candidates:
            # Simple fitness: sum of float values + noise
            values = [v for v in c.values() if isinstance(v, (int, float))]
            fitness = float(np.mean(values)) if values else float(rng.uniform(0, 1))
            scored.append((round(fitness, 4), c))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Select top 50%
        top_k = max(1, len(scored) // 2)
        survivors = scored[:top_k]

        # Mutate survivors to produce next generation
        next_gen: list[dict[str, Any]] = []
        for fitness, candidate in survivors:
            mutant = dict(candidate)
            for key, val in mutant.items():
                if isinstance(val, float):
                    mutant[key] = round(val + float(rng.normal(0, 0.1)), 4)
            next_gen.append(mutant)

        return {
            "generation_size": len(candidates),
            "survivors": top_k,
            "best_fitness": scored[0][0],
            "best_candidate": scored[0][1],
            "next_generation": next_gen,
        }

    # ── Stats ────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        return {
            "total_episodes": len(self._episodes),
            "total_heuristics": len(self._heuristics),
            "total_modifications": len(self._modifications),
            "accepted_modifications": sum(1 for m in self._modifications if m.accepted),
            "skill_tree_level": self.skill_tree.total_level,
            "meta_params": dict(self._meta_params),
        }
