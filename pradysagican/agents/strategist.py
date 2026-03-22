"""
Strategic Planner (ULTRON v2.0) — PRADYSAGICAN
Long-horizon strategic planning with Monte Carlo simulation, game theory,
SWOT analysis, and war-gaming capabilities.
"""
from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class Strategy:
    """A named strategy with scored attributes."""
    name: str
    steps: list[str]
    expected_outcome: str
    risk_level: float = 0.3
    resource_cost: float = 0.5
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SWOTAnalysis:
    """Strengths, Weaknesses, Opportunities, Threats."""
    strengths: list[str]
    weaknesses: list[str]
    opportunities: list[str]
    threats: list[str]
    overall_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "opportunities": self.opportunities,
            "threats": self.threats,
            "overall_score": self.overall_score,
        }


@dataclass
class WarGame:
    """Adversarial simulation result."""
    scenario: str
    our_strategy: Strategy
    adversary_strategy: Strategy
    outcome: str  # "win", "lose", "draw"
    payoff_matrix: list[list[float]] = field(default_factory=list)
    nash_equilibrium: list[float] | None = None
    rounds_played: int = 0


@dataclass
class SimulationResult:
    """Monte Carlo simulation output."""
    strategy_name: str
    simulations: int
    success_rate: float
    mean_outcome: float
    std_outcome: float
    worst_case: float
    best_case: float
    percentile_5: float
    percentile_95: float
    var_95: float  # Value at Risk


# ── Strategic Planner ────────────────────────────────────────────────────────

class StrategicPlanner:
    """ULTRON v2.0 — Long-horizon strategic intelligence.

    Capabilities:
    - Multi-strategy generation with scoring
    - Monte Carlo outcome simulation
    - SWOT analysis
    - Game-theoretic war-gaming with Nash equilibrium
    - Adaptive re-planning from real-time feedback
    - Scenario analysis (best/worst/most-likely)
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._strategy_history: list[Strategy] = []
        self._simulation_cache: dict[str, SimulationResult] = {}

    # ── Strategy Generation ──────────────────────────────────────────────

    async def generate_strategy(
        self,
        goal: str,
        constraints: list[str] | None = None,
        n_strategies: int = 3,
    ) -> list[Strategy]:
        """Generate and score multiple strategic approaches."""
        archetypes = [
            ("conservative", 0.2, 0.3, "Steady, low-risk incremental progress"),
            ("aggressive", 0.7, 0.8, "Bold, high-resource rapid push"),
            ("balanced", 0.4, 0.5, "Sustainable middle ground"),
            ("guerrilla", 0.6, 0.2, "High-risk but low-resource opportunistic"),
            ("fortress", 0.1, 0.6, "Defensive, resource-heavy consolidation"),
        ]

        strategies: list[Strategy] = []
        constraint_text = f" [constraints: {', '.join(constraints)}]" if constraints else ""

        for i in range(min(n_strategies, len(archetypes))):
            name, risk, cost, desc = archetypes[i]
            steps = [
                f"Phase 1: Analyse '{goal[:30]}'{constraint_text}",
                f"Phase 2: {desc}",
                f"Phase 3: Execute with {name} approach",
                f"Phase 4: Evaluate and iterate",
            ]
            strategy = Strategy(
                name=name,
                steps=steps,
                expected_outcome=desc,
                risk_level=risk,
                resource_cost=cost,
            )
            # Score: weighted combination of inverse risk and inverse cost
            strategy.score = round(
                (1.0 - risk) * 0.4 + (1.0 - cost) * 0.3 + self._rng.uniform(0.0, 0.3), 3
            )
            strategies.append(strategy)

        strategies.sort(key=lambda s: s.score, reverse=True)
        self._strategy_history.extend(strategies)
        return strategies

    # ── Monte Carlo Simulation ───────────────────────────────────────────

    async def simulate_strategy(
        self,
        strategy: Strategy,
        simulations: int = 1000,
    ) -> SimulationResult:
        """Monte Carlo simulation of strategy outcomes.

        Models outcome as normally distributed around (1 - risk_level),
        with volatility proportional to risk.
        """
        loc = 1.0 - strategy.risk_level
        scale = strategy.risk_level * 0.5 + 0.1
        outcomes = self._rng.normal(loc=loc, scale=scale, size=simulations)

        result = SimulationResult(
            strategy_name=strategy.name,
            simulations=simulations,
            success_rate=round(float(np.mean(outcomes > 0.5)), 4),
            mean_outcome=round(float(np.mean(outcomes)), 4),
            std_outcome=round(float(np.std(outcomes)), 4),
            worst_case=round(float(np.min(outcomes)), 4),
            best_case=round(float(np.max(outcomes)), 4),
            percentile_5=round(float(np.percentile(outcomes, 5)), 4),
            percentile_95=round(float(np.percentile(outcomes, 95)), 4),
            var_95=round(float(np.percentile(outcomes, 5)), 4),  # VaR at 95% confidence
        )
        self._simulation_cache[strategy.name] = result
        return result

    # ── SWOT Analysis ────────────────────────────────────────────────────

    async def swot_analysis(
        self,
        subject: str,
        context: dict[str, list[str]] | None = None,
    ) -> SWOTAnalysis:
        """Generate a SWOT analysis for a subject."""
        ctx = context or {}
        strengths = ctx.get("strengths", [f"Core competency in {subject[:20]}", "Existing infrastructure"])
        weaknesses = ctx.get("weaknesses", [f"Limited experience with {subject[:20]}", "Resource constraints"])
        opportunities = ctx.get("opportunities", [f"Growing demand for {subject[:20]}", "Technology enablers"])
        threats = ctx.get("threats", [f"Competition in {subject[:20]} space", "Regulatory uncertainty"])

        # Score: (S + O) - (W + T), normalized to [-1, 1]
        pos = len(strengths) + len(opportunities)
        neg = len(weaknesses) + len(threats)
        total = pos + neg
        overall = (pos - neg) / total if total > 0 else 0.0

        return SWOTAnalysis(
            strengths=strengths,
            weaknesses=weaknesses,
            opportunities=opportunities,
            threats=threats,
            overall_score=round(overall, 3),
        )

    # ── Game Theory / War-Gaming ─────────────────────────────────────────

    async def war_game(
        self,
        scenario: str,
        our_strategy: Strategy,
        adversary_strategy: Strategy,
        rounds: int = 10,
    ) -> WarGame:
        """Adversarial simulation using 2-player game theory.

        Constructs a 2x2 payoff matrix (cooperate/defect for each side)
        and computes mixed-strategy Nash equilibrium.
        """
        # Build payoff matrix based on risk/cost profiles
        our_strength = 1.0 - our_strategy.risk_level
        adv_strength = 1.0 - adversary_strategy.risk_level

        # Payoff matrix: [our_cooperate, our_defect] x [adv_cooperate, adv_defect]
        # Each cell is (our_payoff, adv_payoff)
        matrix = [
            [round(our_strength * 0.6, 3), round(adv_strength * 0.6, 3)],   # both cooperate
            [round(our_strength * 0.9, 3), round(adv_strength * 0.1, 3)],   # we defect, they cooperate
            [round(our_strength * 0.1, 3), round(adv_strength * 0.9, 3)],   # we cooperate, they defect
            [round(our_strength * 0.3, 3), round(adv_strength * 0.3, 3)],   # both defect
        ]

        # Mixed-strategy Nash equilibrium for 2x2 game
        nash = self._compute_nash_2x2(matrix)

        # Simulate rounds
        our_total = 0.0
        adv_total = 0.0
        for _ in range(rounds):
            our_move = 0 if self._rng.random() < (nash[0] if nash else 0.5) else 1
            adv_move = 0 if self._rng.random() < (nash[1] if nash else 0.5) else 1
            idx = our_move * 2 + adv_move
            our_total += matrix[idx][0]
            adv_total += matrix[idx][1]

        if our_total > adv_total * 1.05:
            outcome = "win"
        elif adv_total > our_total * 1.05:
            outcome = "lose"
        else:
            outcome = "draw"

        return WarGame(
            scenario=scenario,
            our_strategy=our_strategy,
            adversary_strategy=adversary_strategy,
            outcome=outcome,
            payoff_matrix=matrix,
            nash_equilibrium=nash,
            rounds_played=rounds,
        )

    def _compute_nash_2x2(self, matrix: list[list[float]]) -> list[float] | None:
        """Compute mixed-strategy Nash equilibrium for a 2x2 game.

        matrix layout: [[CC], [DC], [CD], [DD]] where each cell is [our_payoff, adv_payoff].
        Returns [our_cooperate_prob, adv_cooperate_prob] or None if pure strategy.
        """
        if len(matrix) < 4:
            return None

        # Player 1 (us): makes adversary indifferent
        # p * matrix[0][1] + (1-p) * matrix[2][1] = p * matrix[1][1] + (1-p) * matrix[3][1]
        denom_adv = (matrix[0][1] - matrix[2][1] - matrix[1][1] + matrix[3][1])
        if abs(denom_adv) < 1e-10:
            return [0.5, 0.5]
        p = (matrix[3][1] - matrix[2][1]) / denom_adv

        # Player 2 (adversary): makes us indifferent
        denom_us = (matrix[0][0] - matrix[1][0] - matrix[2][0] + matrix[3][0])
        if abs(denom_us) < 1e-10:
            return [0.5, 0.5]
        q = (matrix[3][0] - matrix[1][0]) / denom_us

        return [round(max(0.0, min(1.0, p)), 4), round(max(0.0, min(1.0, q)), 4)]

    # ── Adaptive Re-planning ─────────────────────────────────────────────

    async def adaptive_replan(
        self,
        current_strategy: Strategy,
        feedback: dict[str, Any],
    ) -> Strategy:
        """Adjust strategy based on real-time feedback."""
        success_signal = feedback.get("success_rate", 0.5)
        adjusted_risk = current_strategy.risk_level

        if success_signal < 0.3:
            # Failing: reduce risk, add conservative steps
            adjusted_risk = max(current_strategy.risk_level - 0.15, 0.05)
            new_steps = current_strategy.steps + [
                f"PIVOT: reduce exposure (feedback success_rate={success_signal:.2f})",
                "Consolidate gains before next push",
            ]
        elif success_signal > 0.7:
            # Winning: can afford more risk
            adjusted_risk = min(current_strategy.risk_level + 0.1, 0.9)
            new_steps = current_strategy.steps + [
                f"ACCELERATE: increase ambition (feedback success_rate={success_signal:.2f})",
            ]
        else:
            new_steps = current_strategy.steps + [
                f"HOLD: maintain course (feedback success_rate={success_signal:.2f})",
            ]

        adjusted = Strategy(
            name=f"{current_strategy.name}_v{len(self._strategy_history) + 1}",
            steps=new_steps,
            expected_outcome=f"Adapted from {current_strategy.name}",
            risk_level=round(adjusted_risk, 3),
            resource_cost=current_strategy.resource_cost,
        )
        adjusted.score = round((1.0 - adjusted.risk_level) * 0.5 + success_signal * 0.5, 3)
        self._strategy_history.append(adjusted)
        return adjusted

    # ── Scenario Analysis ────────────────────────────────────────────────

    async def scenario_analysis(
        self,
        goal: str,
        variables: dict[str, tuple[float, float]],
    ) -> dict[str, dict[str, float]]:
        """Best/worst/most-likely scenario analysis over variable ranges.

        Args:
            goal: What we're analyzing.
            variables: {name: (min_val, max_val)} ranges for each variable.
        """
        scenarios: dict[str, dict[str, float]] = {}

        for scenario_type in ("best", "worst", "most_likely"):
            values: dict[str, float] = {}
            for var_name, (lo, hi) in variables.items():
                if scenario_type == "best":
                    values[var_name] = hi
                elif scenario_type == "worst":
                    values[var_name] = lo
                else:
                    values[var_name] = round((lo + hi) / 2.0, 4)

            # Aggregate score from all variable values
            all_vals = list(values.values())
            aggregate = float(np.mean(all_vals)) if all_vals else 0.5
            values["_aggregate_score"] = round(aggregate, 4)
            scenarios[scenario_type] = values

        return scenarios

    # ── Portfolio Optimisation (Markowitz-inspired) ───────────────────────

    async def optimise_portfolio(
        self,
        strategies: list[Strategy],
        target_risk: float = 0.4,
    ) -> dict[str, Any]:
        """Allocate resources across strategies to minimise risk for target return.

        Simplified Markowitz: treat strategy scores as returns, risk_levels as volatility.
        """
        if not strategies:
            return {"error": "No strategies to optimise"}

        n = len(strategies)
        returns = np.array([s.score for s in strategies])
        risks = np.array([s.risk_level for s in strategies])

        # Simple inverse-variance weighting
        inv_risk = 1.0 / (risks + 0.01)
        weights = inv_risk / inv_risk.sum()

        # Adjust toward target risk
        portfolio_risk = float(np.dot(weights, risks))
        if portfolio_risk > target_risk and n > 1:
            # Shift weight toward lower-risk strategies
            risk_order = np.argsort(risks)
            weights[risk_order[0]] += 0.1
            weights = weights / weights.sum()
            portfolio_risk = float(np.dot(weights, risks))

        portfolio_return = float(np.dot(weights, returns))

        allocation = {
            strategies[i].name: round(float(weights[i]), 4)
            for i in range(n)
        }

        return {
            "allocation": allocation,
            "expected_return": round(portfolio_return, 4),
            "expected_risk": round(portfolio_risk, 4),
            "sharpe_ratio": round(portfolio_return / max(portfolio_risk, 0.01), 4),
            "target_risk": target_risk,
        }
