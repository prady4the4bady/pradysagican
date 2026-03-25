"""OMEGA benchmark automation and regression guard scaffolds."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pradysagican.benchmarks.benchmark_suite import BenchmarkSuite


@dataclass
class PerformanceLeaderboard:
    rows: list[dict[str, Any]] = field(default_factory=list)

    def update(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows


class AutoBenchmarker:
    def __init__(self) -> None:
        self._suite = BenchmarkSuite()

    async def run_daily(self) -> dict[str, Any]:
        results = await self._suite.run_all()
        report = self._suite.generate_report()
        return {"results": {k: v.percentage for k, v in results.items()}, "report": report}


class WeaknessFinder:
    def find(self, report: dict[str, Any], threshold: float = 70.0) -> list[dict[str, Any]]:
        weaknesses: list[dict[str, Any]] = []
        top = report.get("leaderboard_top5", [])
        for row in top:
            score = float(row.get("our_score") or 0.0)
            if score < threshold:
                weaknesses.append({"benchmark": row.get("benchmark"), "score": score})
        return weaknesses


class BenchmarkOracle:
    def verify(self, prediction: str, expected: str) -> bool:
        return prediction.strip().lower() == expected.strip().lower()


class HumanEvalQueue:
    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def push(self, item: dict[str, Any]) -> None:
        self._items.append(item)

    def pop_batch(self, n: int = 10) -> list[dict[str, Any]]:
        batch = self._items[:n]
        self._items = self._items[n:]
        return batch


class RegressionGuard:
    def check(self, previous: float, current: float, max_drop_pct: float = 1.0) -> dict[str, Any]:
        delta = current - previous
        return {
            "ok": delta >= (-1.0 * max_drop_pct),
            "delta": round(delta, 4),
            "max_drop_pct": max_drop_pct,
        }

