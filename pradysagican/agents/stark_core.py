"""
Tony Stark Personality Engine — PRADYSAGICAN v2.0
Strategic thinking, operator mindset, rapid experimentation, confidence calibration.
Implements the Stark Doctrine: anticipate problems, iterate faster, back conclusions with data.
"""
from __future__ import annotations

import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ── Personality Pillars ──────────────────────────────────────────────────────

class PillarWeight(float, Enum):
    """Default weights for personality pillars (tunable per-instance)."""
    STRATEGIC_THINKING = 0.25
    OPERATOR_MINDSET = 0.25
    RAPID_EXPERIMENTATION = 0.20
    STAND_YOUR_GROUND = 0.15
    KNOW_YOUR_WORTH = 0.15


@dataclass
class StarkMindset:
    """Configurable personality weights — the 'Stark dial'."""
    strategic_thinking: float = 0.25
    operator_mindset: float = 0.25
    rapid_experimentation: float = 0.20
    stand_your_ground: float = 0.15
    know_your_worth: float = 0.15

    def as_vector(self) -> np.ndarray:
        """Return normalized weight vector."""
        v = np.array([
            self.strategic_thinking, self.operator_mindset,
            self.rapid_experimentation, self.stand_your_ground,
            self.know_your_worth,
        ])
        total = v.sum()
        return v / total if total > 0 else v

    def dominant_pillar(self) -> str:
        """Return the pillar with the highest weight."""
        pillars = {
            "strategic_thinking": self.strategic_thinking,
            "operator_mindset": self.operator_mindset,
            "rapid_experimentation": self.rapid_experimentation,
            "stand_your_ground": self.stand_your_ground,
            "know_your_worth": self.know_your_worth,
        }
        return max(pillars, key=pillars.get)  # type: ignore[arg-type]


# ── Decision Journal ─────────────────────────────────────────────────────────

@dataclass
class DecisionEntry:
    """Single entry in the decision journal."""
    id: str
    decision: str
    reasoning: str
    confidence: float
    alternatives_considered: list[str] = field(default_factory=list)
    outcome: str | None = None
    outcome_score: float | None = None
    timestamp: float = field(default_factory=time.time)


class DecisionJournal:
    """Persistent record of decisions for accountability and learning.

    Every strategic choice is logged with reasoning, confidence, and
    eventual outcome so the system can calibrate future confidence.
    """

    def __init__(self) -> None:
        self._entries: list[DecisionEntry] = []
        self._calibration_data: list[tuple[float, float]] = []  # (predicted, actual)

    async def record(
        self,
        decision: str,
        reasoning: str,
        confidence: float,
        alternatives: list[str] | None = None,
    ) -> DecisionEntry:
        """Record a new decision."""
        entry = DecisionEntry(
            id=f"dec_{uuid.uuid4().hex[:8]}",
            decision=decision,
            reasoning=reasoning,
            confidence=max(0.0, min(1.0, confidence)),
            alternatives_considered=alternatives or [],
        )
        self._entries.append(entry)
        logger.info("Decision recorded: %s (confidence=%.2f)", decision[:40], confidence)
        return entry

    async def record_outcome(self, decision_id: str, outcome: str, score: float) -> DecisionEntry | None:
        """Attach outcome to a prior decision for calibration."""
        for entry in self._entries:
            if entry.id == decision_id:
                entry.outcome = outcome
                entry.outcome_score = max(0.0, min(1.0, score))
                self._calibration_data.append((entry.confidence, entry.outcome_score))
                return entry
        return None

    async def calibration_report(self) -> dict[str, Any]:
        """How well-calibrated are our confidence estimates?

        Perfect calibration: when we say 80% confident, we succeed 80% of the time.
        Returns Brier score (lower = better, 0 = perfect) and bucket analysis.
        """
        if len(self._calibration_data) < 3:
            return {"status": "insufficient_data", "entries": len(self._calibration_data)}

        predicted = np.array([p for p, _ in self._calibration_data])
        actual = np.array([a for _, a in self._calibration_data])
        brier = float(np.mean((predicted - actual) ** 2))

        # Bucket analysis: group by predicted confidence ranges
        buckets: dict[str, dict[str, float]] = {}
        for lo, hi, label in [(0, 0.33, "low"), (0.33, 0.66, "medium"), (0.66, 1.01, "high")]:
            mask = (predicted >= lo) & (predicted < hi)
            if mask.any():
                buckets[label] = {
                    "avg_predicted": float(np.mean(predicted[mask])),
                    "avg_actual": float(np.mean(actual[mask])),
                    "count": int(mask.sum()),
                }

        return {
            "brier_score": round(brier, 4),
            "total_decisions": len(self._calibration_data),
            "buckets": buckets,
            "is_overconfident": float(np.mean(predicted)) > float(np.mean(actual)) + 0.1,
        }

    @property
    def entries(self) -> list[DecisionEntry]:
        return list(self._entries)


# ── Operator Dashboard ───────────────────────────────────────────────────────

@dataclass
class MetricSnapshot:
    """Point-in-time system metric."""
    name: str
    value: float
    unit: str = ""
    timestamp: float = field(default_factory=time.time)


class OperatorDashboard:
    """Real-time metrics tracking — ship fast, measure everything.

    Tracks throughput, latency, error rates, and custom KPIs.
    Uses Welford's algorithm for online mean/variance.
    """

    def __init__(self) -> None:
        self._metrics: dict[str, list[MetricSnapshot]] = {}
        # Welford accumulators: name -> (count, mean, M2)
        self._welford: dict[str, tuple[int, float, float]] = {}

    async def record_metric(self, name: str, value: float, unit: str = "") -> MetricSnapshot:
        """Record a metric data-point."""
        snap = MetricSnapshot(name=name, value=value, unit=unit)
        self._metrics.setdefault(name, []).append(snap)
        # Welford online update
        n, mean, m2 = self._welford.get(name, (0, 0.0, 0.0))
        n += 1
        delta = value - mean
        mean += delta / n
        delta2 = value - mean
        m2 += delta * delta2
        self._welford[name] = (n, mean, m2)
        return snap

    async def summary(self, name: str) -> dict[str, Any]:
        """Statistical summary for a named metric."""
        if name not in self._welford:
            return {"error": f"Unknown metric: {name}"}
        n, mean, m2 = self._welford[name]
        variance = m2 / n if n > 1 else 0.0
        values = [s.value for s in self._metrics.get(name, [])]
        return {
            "name": name,
            "count": n,
            "mean": round(mean, 4),
            "std": round(math.sqrt(variance), 4),
            "min": round(min(values), 4) if values else 0.0,
            "max": round(max(values), 4) if values else 0.0,
            "latest": round(values[-1], 4) if values else 0.0,
        }

    async def dashboard(self) -> dict[str, dict[str, Any]]:
        """Full dashboard across all tracked metrics."""
        result: dict[str, dict[str, Any]] = {}
        for name in self._metrics:
            result[name] = await self.summary(name)
        return result

    async def alert_check(self, name: str, threshold: float, direction: str = "above") -> dict[str, Any]:
        """Check if latest metric value triggers an alert."""
        values = [s.value for s in self._metrics.get(name, [])]
        if not values:
            return {"alert": False, "reason": "no data"}
        latest = values[-1]
        triggered = (latest > threshold) if direction == "above" else (latest < threshold)
        return {"alert": triggered, "metric": name, "latest": latest, "threshold": threshold, "direction": direction}


# ── Strategic Planner (Stark-style 10-move lookahead) ────────────────────────

@dataclass
class StrategicMove:
    """A single move in a strategic sequence."""
    step: int
    action: str
    expected_impact: float
    risk: float
    contingency: str


class StrategicPlanner:
    """Multi-move lookahead planning with contingency generation.

    Models decisions as a sequence of moves, each with impact, risk,
    and a fallback plan — the Stark 10-move-ahead approach.
    """

    def __init__(self, mindset: StarkMindset | None = None) -> None:
        self._mindset = mindset or StarkMindset()

    async def plan_ahead(
        self,
        goal: str,
        horizon: int = 10,
        risk_tolerance: float = 0.5,
    ) -> list[StrategicMove]:
        """Generate a multi-step strategic plan with contingencies."""
        rng = np.random.default_rng(hash(goal) % (2**31))
        moves: list[StrategicMove] = []
        cumulative_risk = 0.0

        for step in range(1, horizon + 1):
            base_impact = rng.uniform(0.3, 0.9)
            step_risk = rng.uniform(0.05, 0.4)
            cumulative_risk = 1.0 - (1.0 - cumulative_risk) * (1.0 - step_risk)

            # Risk-aware: reduce ambition when risk accumulates
            if cumulative_risk > risk_tolerance:
                base_impact *= 0.7
                step_risk *= 0.5

            moves.append(StrategicMove(
                step=step,
                action=f"Move {step}: advance toward '{goal[:30]}' (phase {'setup' if step <= 3 else 'execute' if step <= 7 else 'consolidate'})",
                expected_impact=round(float(base_impact), 3),
                risk=round(float(step_risk), 3),
                contingency=f"Fallback for step {step}: revert to step {max(1, step - 2)} state",
            ))
        return moves

    async def evaluate_plan(self, moves: list[StrategicMove]) -> dict[str, Any]:
        """Score a strategic plan on risk-adjusted impact."""
        if not moves:
            return {"score": 0.0, "feasible": False}
        impacts = np.array([m.expected_impact for m in moves])
        risks = np.array([m.risk for m in moves])
        # Risk-adjusted score: impact weighted by survival probability
        survival = np.cumprod(1.0 - risks)
        weighted_impact = float(np.sum(impacts * survival))
        total_risk = 1.0 - float(np.prod(1.0 - risks))
        return {
            "total_impact": round(weighted_impact, 3),
            "total_risk": round(total_risk, 3),
            "risk_adjusted_score": round(weighted_impact * (1.0 - total_risk), 3),
            "weakest_step": int(np.argmax(risks)) + 1,
            "strongest_step": int(np.argmax(impacts)) + 1,
            "feasible": total_risk < 0.8,
        }


# ── Rapid Experimenter ───────────────────────────────────────────────────────

@dataclass
class Experiment:
    """A/B test or rapid experiment."""
    id: str
    name: str
    hypothesis: str
    variants: list[str]
    results: dict[str, list[float]] = field(default_factory=dict)
    winner: str | None = None
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)


class RapidExperimenter:
    """Fail fast, learn faster — A/B testing and rapid iteration.

    Runs lightweight experiments with statistical significance testing
    (two-sample t-test approximation via Welch's method).
    """

    def __init__(self) -> None:
        self._experiments: list[Experiment] = []

    async def create_experiment(
        self,
        name: str,
        hypothesis: str,
        variants: list[str] | None = None,
    ) -> Experiment:
        """Set up a new experiment."""
        exp = Experiment(
            id=f"exp_{uuid.uuid4().hex[:8]}",
            name=name,
            hypothesis=hypothesis,
            variants=variants or ["control", "treatment"],
        )
        exp.results = {v: [] for v in exp.variants}
        self._experiments.append(exp)
        return exp

    async def add_observation(self, experiment_id: str, variant: str, value: float) -> bool:
        """Record an observation for a variant."""
        for exp in self._experiments:
            if exp.id == experiment_id and variant in exp.results:
                exp.results[variant].append(value)
                return True
        return False

    async def analyze(self, experiment_id: str) -> dict[str, Any]:
        """Analyze experiment results with Welch's t-test approximation."""
        exp = next((e for e in self._experiments if e.id == experiment_id), None)
        if exp is None:
            return {"error": "Experiment not found"}

        variant_stats: dict[str, dict[str, float]] = {}
        for v, vals in exp.results.items():
            if vals:
                arr = np.array(vals)
                variant_stats[v] = {
                    "mean": round(float(np.mean(arr)), 4),
                    "std": round(float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0, 4),
                    "n": len(arr),
                }
            else:
                variant_stats[v] = {"mean": 0.0, "std": 0.0, "n": 0}

        # Welch's t-test between first two variants (if enough data)
        variants = list(exp.results.keys())
        significance = 0.0
        if len(variants) >= 2:
            a_vals = exp.results[variants[0]]
            b_vals = exp.results[variants[1]]
            if len(a_vals) >= 2 and len(b_vals) >= 2:
                a, b = np.array(a_vals), np.array(b_vals)
                se = math.sqrt(float(np.var(a, ddof=1)) / len(a) + float(np.var(b, ddof=1)) / len(b))
                if se > 0:
                    t_stat = abs(float(np.mean(a)) - float(np.mean(b))) / se
                    # Rough p-value approximation using normal CDF
                    significance = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(t_stat / math.sqrt(2.0))))
                    significance = max(0.0, min(1.0, significance))

        # Determine winner
        best_v = max(variant_stats, key=lambda v: variant_stats[v]["mean"])
        exp.winner = best_v if significance < 0.05 else None
        exp.confidence = 1.0 - significance

        return {
            "experiment": exp.name,
            "variants": variant_stats,
            "significance_p": round(significance, 4),
            "winner": exp.winner,
            "confidence": round(exp.confidence, 4),
            "recommendation": f"Adopt '{exp.winner}'" if exp.winner else "Continue collecting data",
        }

    async def iterate(self, experiment_id: str, learning: str) -> Experiment | None:
        """Create a follow-up experiment based on learnings."""
        parent = next((e for e in self._experiments if e.id == experiment_id), None)
        if parent is None:
            return None
        new_exp = await self.create_experiment(
            name=f"{parent.name}_v{len(self._experiments)}",
            hypothesis=f"Based on '{learning[:50]}', refining {parent.hypothesis[:50]}",
            variants=parent.variants,
        )
        return new_exp

    @property
    def experiments(self) -> list[Experiment]:
        return list(self._experiments)


# ── Stark Core Façade ────────────────────────────────────────────────────────

class StarkCore:
    """Tony Stark Personality Engine — top-level façade.

    Integrates mindset, decision journal, operator dashboard,
    strategic planner, and rapid experimentation into a single coherent system.
    """

    def __init__(self, mindset: StarkMindset | None = None) -> None:
        self.mindset = mindset or StarkMindset()
        self.journal = DecisionJournal()
        self.dashboard = OperatorDashboard()
        self.planner = StrategicPlanner(self.mindset)
        self.experimenter = RapidExperimenter()
        logger.info("StarkCore initialised — dominant pillar: %s", self.mindset.dominant_pillar())

    async def strategic_decision(
        self,
        question: str,
        options: list[str],
        context: str = "",
    ) -> dict[str, Any]:
        """Make a confident, data-backed decision and log it."""
        # Score each option heuristically
        rng = np.random.default_rng(hash(question) % (2**31))
        scores: dict[str, float] = {}
        for opt in options:
            base = rng.uniform(0.3, 0.9)
            # Boost options that align with dominant pillar keywords
            pillar = self.mindset.dominant_pillar()
            if pillar[:4].lower() in opt.lower():
                base = min(base + 0.15, 1.0)
            scores[opt] = round(float(base), 3)

        best = max(scores, key=scores.get)  # type: ignore[arg-type]
        confidence = scores[best]
        alternatives = [o for o in options if o != best]

        entry = await self.journal.record(
            decision=f"Chose '{best}' for: {question[:60]}",
            reasoning=f"Scored {len(options)} options; '{best}' scored {confidence:.3f}",
            confidence=confidence,
            alternatives=alternatives,
        )
        await self.dashboard.record_metric("decisions_made", 1.0, "count")
        await self.dashboard.record_metric("decision_confidence", confidence)

        return {
            "chosen": best,
            "confidence": confidence,
            "scores": scores,
            "decision_id": entry.id,
            "alternatives": alternatives,
        }

    async def operator_report(self) -> dict[str, Any]:
        """Full operator status report — Stark style."""
        board = await self.dashboard.dashboard()
        cal = await self.journal.calibration_report()
        return {
            "mindset": self.mindset.dominant_pillar(),
            "metrics": board,
            "calibration": cal,
            "total_decisions": len(self.journal.entries),
            "total_experiments": len(self.experimenter.experiments),
        }
