"""
Prometheus — Self-Evolution Engine — PRADYSAGICAN
Implements continuous self-improvement: research monitoring, automated testing,
crisis preparation, knowledge distillation, and self-benchmarking.

Inspired by the Darwin Gödel Machine (Sakana AI) concept of self-referential
improvement and Stark Doctrine's "build for the crisis that hasn't happened yet."
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import os
import random
import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class CrisisSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_id: str
    name: str
    status: TestStatus
    duration_ms: float
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)


@dataclass
class CrisisScenario:
    """A simulated crisis scenario with response plans."""
    scenario_id: str
    name: str
    description: str
    severity: CrisisSeverity
    probability: float  # 0.0 - 1.0
    impact_score: float  # 0.0 - 1.0
    mitigation_steps: list[str] = field(default_factory=list)
    rehearsed: bool = False
    last_rehearsal: float = 0.0
    success_rate: float = 0.0  # from rehearsals


@dataclass
class KnowledgeEntry:
    """Compressed knowledge representation."""
    entry_id: str
    topic: str
    summary: str
    source_count: int
    confidence: float  # 0.0 - 1.0
    created_at: float = field(default_factory=time.time)
    last_validated: float = field(default_factory=time.time)
    associations: list[str] = field(default_factory=list)
    embedding: np.ndarray | None = None


@dataclass
class BenchmarkResult:
    """Performance benchmark measurement."""
    benchmark_id: str
    metric_name: str
    value: float
    unit: str
    baseline: float
    delta_pct: float  # % change from baseline
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchFinding:
    """A discovered research insight."""
    finding_id: str
    domain: str
    title: str
    summary: str
    relevance_score: float  # 0.0 - 1.0
    novelty_score: float  # 0.0 - 1.0
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    keywords: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Utility: deterministic pseudo-embedding
# ---------------------------------------------------------------------------

def _text_to_embedding(text: str, dim: int = 64) -> np.ndarray:
    """Deterministic hash-based pseudo-embedding for text."""
    h = hashlib.sha256(text.encode()).digest()
    rng = np.random.RandomState(int.from_bytes(h[:4], "big"))
    vec = rng.randn(dim).astype(np.float32)
    norm = np.linalg.norm(vec)
    return vec / max(norm, 1e-8)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity clamped to [-1, 1]."""
    dot = float(np.dot(a, b))
    denom = float(np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return max(-1.0, min(1.0, dot / denom))


# ---------------------------------------------------------------------------
# ResearchDaemon — monitors domains for new insights
# ---------------------------------------------------------------------------

class ResearchDaemon:
    """Continuously scans configured domains for new knowledge.

    In production this would poll arXiv, GitHub trending, RSS feeds, etc.
    Here it simulates the research pipeline with deterministic logic so the
    module can run offline without any external API calls.
    """

    def __init__(self, domains: list[str] | None = None) -> None:
        self._domains: list[str] = domains or [
            "machine_learning", "security", "systems", "data_engineering",
        ]
        self._findings: list[ResearchFinding] = []
        self._scan_count: int = 0
        self._keyword_index: dict[str, list[str]] = {}  # keyword -> finding_ids

    async def scan_domain(self, domain: str, query: str = "") -> list[ResearchFinding]:
        """Simulate scanning a knowledge domain for relevant findings.

        Generates deterministic pseudo-findings based on domain+query hash
        so that results are reproducible across runs.
        """
        self._scan_count += 1
        seed_text = f"{domain}:{query}:{self._scan_count}"
        seed = int(hashlib.sha256(seed_text.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        n_findings = rng.randint(1, 4)
        results: list[ResearchFinding] = []

        topic_pool = {
            "machine_learning": ["transformers", "diffusion", "rl", "graph_nn", "moe"],
            "security": ["zero_trust", "supply_chain", "fuzzing", "sbom", "cve"],
            "systems": ["scheduling", "memory", "concurrency", "io", "containers"],
            "data_engineering": ["streaming", "lakehouse", "lineage", "quality", "catalog"],
        }
        topics = topic_pool.get(domain, ["general_topic"])

        for i in range(n_findings):
            topic = rng.choice(topics)
            relevance = max(0.0, min(1.0, rng.gauss(0.6, 0.2)))
            novelty = max(0.0, min(1.0, rng.gauss(0.5, 0.25)))
            fid = f"rf_{domain[:3]}_{self._scan_count}_{i}"
            finding = ResearchFinding(
                finding_id=fid,
                domain=domain,
                title=f"Advances in {topic} for {domain}",
                summary=f"New approaches to {topic} show {novelty:.0%} novelty in {domain}",
                relevance_score=relevance,
                novelty_score=novelty,
                source=f"simulated_{domain}_scan",
                keywords=[domain, topic, query] if query else [domain, topic],
            )
            results.append(finding)
            self._findings.append(finding)

            # Update keyword index
            for kw in finding.keywords:
                self._keyword_index.setdefault(kw, []).append(fid)

        logger.info("ResearchDaemon scanned %s: %d findings", domain, len(results))
        return results

    async def scan_all_domains(self) -> dict[str, list[ResearchFinding]]:
        """Scan all configured domains concurrently."""
        results: dict[str, list[ResearchFinding]] = {}
        tasks = [self.scan_domain(d) for d in self._domains]
        domain_results = await asyncio.gather(*tasks)
        for domain, findings in zip(self._domains, domain_results):
            results[domain] = findings
        return results

    async def search_findings(self, query: str, top_k: int = 5) -> list[ResearchFinding]:
        """Semantic search over accumulated findings."""
        if not self._findings:
            return []
        q_emb = _text_to_embedding(query)
        scored = []
        for f in self._findings:
            f_emb = _text_to_embedding(f.title + " " + f.summary)
            sim = _cosine_similarity(q_emb, f_emb)
            scored.append((sim, f))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in scored[:top_k]]

    @property
    def total_findings(self) -> int:
        return len(self._findings)

    @property
    def scan_count(self) -> int:
        return self._scan_count


# ---------------------------------------------------------------------------
# ContinuousTestRunner — runs test suites and tracks reliability
# ---------------------------------------------------------------------------

class ContinuousTestRunner:
    """Executes test suites, tracks pass rates, detects regressions.

    Implements statistical process control (SPC) to detect when failure rates
    exceed control limits, signalling a regression.
    """

    def __init__(self, control_limit_sigma: float = 2.0) -> None:
        self._results: list[TestResult] = []
        self._suite_history: dict[str, list[bool]] = {}  # suite -> pass/fail bools
        self._control_limit_sigma = control_limit_sigma
        self._run_count: int = 0

    async def run_test(
        self,
        name: str,
        test_fn: Callable[[], Awaitable[bool]] | None = None,
        tags: list[str] | None = None,
    ) -> TestResult:
        """Execute a single test and record the result.

        If *test_fn* is None a simulated test is run (always passes).
        """
        self._run_count += 1
        test_id = f"t_{self._run_count}_{int(time.time())}"
        start = time.monotonic()
        try:
            if test_fn is not None:
                passed = await test_fn()
            else:
                passed = True  # simulated pass
            duration = (time.monotonic() - start) * 1000
            status = TestStatus.PASSED if passed else TestStatus.FAILED
            msg = "OK" if passed else "Assertion failed"
        except Exception as exc:
            duration = (time.monotonic() - start) * 1000
            status = TestStatus.ERROR
            msg = str(exc)

        result = TestResult(
            test_id=test_id, name=name, status=status,
            duration_ms=duration, message=msg, tags=tags or [],
        )
        self._results.append(result)

        # Track suite-level history
        suite = tags[0] if tags else "default"
        self._suite_history.setdefault(suite, []).append(status == TestStatus.PASSED)

        logger.debug("Test %s: %s (%.1fms)", name, status.value, duration)
        return result

    async def run_suite(
        self,
        suite_name: str,
        tests: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run a batch of tests and return aggregate statistics.

        Each entry in *tests* should have 'name' and optionally 'fn'.
        """
        results: list[TestResult] = []
        for t in tests:
            r = await self.run_test(
                name=t.get("name", f"test_{len(results)}"),
                test_fn=t.get("fn"),
                tags=[suite_name],
            )
            results.append(r)

        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        errored = sum(1 for r in results if r.status == TestStatus.ERROR)
        total_ms = sum(r.duration_ms for r in results)

        return {
            "suite": suite_name,
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "errored": errored,
            "pass_rate": passed / max(len(results), 1),
            "duration_ms": total_ms,
            "results": results,
        }

    async def detect_regression(self, suite: str, window: int = 20) -> dict[str, Any]:
        """Detect if recent failure rate exceeds SPC control limits.

        Uses a p-chart approach: if recent failure proportion exceeds
        baseline mean + k*sigma, flags a regression.
        """
        history = self._suite_history.get(suite, [])
        if len(history) < window:
            return {"suite": suite, "regression": False, "reason": "insufficient data",
                    "data_points": len(history)}

        baseline = history[:-window]
        recent = history[-window:]

        if not baseline:
            return {"suite": suite, "regression": False, "reason": "no baseline"}

        p_baseline = sum(not x for x in baseline) / len(baseline)  # failure rate
        p_recent = sum(not x for x in recent) / len(recent)

        # Standard deviation for proportion
        sigma = math.sqrt(max(p_baseline * (1 - p_baseline) / len(recent), 1e-12))
        ucl = p_baseline + self._control_limit_sigma * sigma

        regression = p_recent > ucl
        return {
            "suite": suite,
            "regression": regression,
            "baseline_failure_rate": round(p_baseline, 4),
            "recent_failure_rate": round(p_recent, 4),
            "upper_control_limit": round(ucl, 4),
            "sigma": round(sigma, 6),
            "window": window,
        }

    @property
    def total_runs(self) -> int:
        return self._run_count

    @property
    def overall_pass_rate(self) -> float:
        if not self._results:
            return 0.0
        return sum(1 for r in self._results if r.status == TestStatus.PASSED) / len(self._results)


# ---------------------------------------------------------------------------
# CrisisPreparator — scenario simulation & contingency planning
# ---------------------------------------------------------------------------

class CrisisPreparator:
    """Models potential crises, rehearses responses, measures readiness.

    Implements risk-matrix scoring (probability × impact) and Monte-Carlo
    rehearsal to estimate response success rates.
    """

    def __init__(self) -> None:
        self._scenarios: dict[str, CrisisScenario] = {}
        self._rehearsal_log: list[dict[str, Any]] = []

    async def register_scenario(
        self,
        name: str,
        description: str,
        severity: CrisisSeverity = CrisisSeverity.MEDIUM,
        probability: float = 0.5,
        impact_score: float = 0.5,
        mitigation_steps: list[str] | None = None,
    ) -> CrisisScenario:
        """Register a new crisis scenario for tracking and rehearsal."""
        sid = f"crisis_{hashlib.md5(name.encode()).hexdigest()[:8]}"
        scenario = CrisisScenario(
            scenario_id=sid,
            name=name,
            description=description,
            severity=severity,
            probability=max(0.0, min(1.0, probability)),
            impact_score=max(0.0, min(1.0, impact_score)),
            mitigation_steps=mitigation_steps or [],
        )
        self._scenarios[sid] = scenario
        logger.info("Registered crisis scenario: %s (%s)", name, severity.value)
        return scenario

    async def rehearse(self, scenario_id: str, n_simulations: int = 100) -> dict[str, Any]:
        """Monte-Carlo rehearsal of a crisis scenario.

        Simulates *n_simulations* response attempts. Success probability is
        influenced by number of mitigation steps and prior rehearsals.
        """
        scenario = self._scenarios.get(scenario_id)
        if scenario is None:
            return {"error": f"Scenario {scenario_id} not found"}

        # Base success probability scales with preparation
        step_bonus = min(len(scenario.mitigation_steps) * 0.08, 0.4)
        practice_bonus = min(scenario.success_rate * 0.2, 0.2)
        base_p = 0.3 + step_bonus + practice_bonus

        rng = np.random.default_rng(int(time.time()) % (2**31))
        outcomes = rng.random(n_simulations) < base_p
        success_rate = float(np.mean(outcomes))

        # Response time model: gamma distribution (realistic skew)
        response_times = rng.gamma(shape=2.0, scale=5.0, size=n_simulations)
        mean_response_time = float(np.mean(response_times))
        p95_response_time = float(np.percentile(response_times, 95))

        # Update scenario
        scenario.rehearsed = True
        scenario.last_rehearsal = time.time()
        # Exponential moving average of success rate
        if scenario.success_rate > 0:
            scenario.success_rate = 0.7 * scenario.success_rate + 0.3 * success_rate
        else:
            scenario.success_rate = success_rate

        entry = {
            "scenario_id": scenario_id,
            "n_simulations": n_simulations,
            "success_rate": round(success_rate, 4),
            "cumulative_success_rate": round(scenario.success_rate, 4),
            "mean_response_time": round(mean_response_time, 2),
            "p95_response_time": round(p95_response_time, 2),
            "timestamp": time.time(),
        }
        self._rehearsal_log.append(entry)
        return entry

    async def risk_matrix(self) -> list[dict[str, Any]]:
        """Return all scenarios ranked by risk score (probability × impact)."""
        ranked = []
        for s in self._scenarios.values():
            risk = s.probability * s.impact_score
            ranked.append({
                "scenario_id": s.scenario_id,
                "name": s.name,
                "severity": s.severity.value,
                "probability": s.probability,
                "impact": s.impact_score,
                "risk_score": round(risk, 4),
                "rehearsed": s.rehearsed,
                "success_rate": round(s.success_rate, 4),
            })
        ranked.sort(key=lambda x: x["risk_score"], reverse=True)
        return ranked

    async def readiness_score(self) -> dict[str, Any]:
        """Aggregate readiness across all registered scenarios."""
        if not self._scenarios:
            return {"readiness": 0.0, "total_scenarios": 0, "rehearsed": 0}

        rehearsed = sum(1 for s in self._scenarios.values() if s.rehearsed)
        avg_success = statistics.mean(
            s.success_rate for s in self._scenarios.values() if s.rehearsed
        ) if rehearsed > 0 else 0.0
        coverage = rehearsed / len(self._scenarios)

        readiness = 0.4 * coverage + 0.6 * avg_success
        return {
            "readiness": round(readiness, 4),
            "total_scenarios": len(self._scenarios),
            "rehearsed": rehearsed,
            "coverage": round(coverage, 4),
            "avg_success_rate": round(avg_success, 4),
        }


# ---------------------------------------------------------------------------
# KnowledgeDistillery — compresses and organises knowledge
# ---------------------------------------------------------------------------

class KnowledgeDistillery:
    """Distills raw information into compressed, validated knowledge entries.

    Implements a simple TF-IDF-style keyword extraction and embedding-based
    deduplication to keep the knowledge base lean.
    """

    def __init__(self, dedup_threshold: float = 0.85) -> None:
        self._entries: dict[str, KnowledgeEntry] = {}
        self._dedup_threshold = dedup_threshold

    async def distill(
        self,
        topic: str,
        raw_texts: list[str],
        source_label: str = "",
    ) -> KnowledgeEntry:
        """Compress multiple raw texts into a single knowledge entry.

        Extracts keywords via term-frequency, creates a summary by selecting
        the most representative sentence, and deduplicates against existing
        entries using cosine similarity on embeddings.
        """
        # Simple TF aggregation
        tf: dict[str, int] = {}
        all_sentences: list[str] = []
        for text in raw_texts:
            for word in text.lower().split():
                clean = "".join(c for c in word if c.isalnum())
                if len(clean) > 3:
                    tf[clean] = tf.get(clean, 0) + 1
            all_sentences.extend(s.strip() for s in text.split(".") if len(s.strip()) > 10)

        # Top keywords
        top_keywords = sorted(tf, key=tf.get, reverse=True)[:10]

        # Pick most representative sentence (highest keyword coverage)
        best_sentence = topic
        best_score = -1
        for sent in all_sentences:
            score = sum(1 for kw in top_keywords if kw in sent.lower())
            if score > best_score:
                best_score = score
                best_sentence = sent

        summary = f"{best_sentence}. Key concepts: {', '.join(top_keywords[:5])}"
        embedding = _text_to_embedding(topic + " " + summary)
        confidence = max(0.0, min(1.0, len(raw_texts) * 0.15))

        # Deduplication check
        for existing in self._entries.values():
            if existing.embedding is not None:
                sim = _cosine_similarity(embedding, existing.embedding)
                if sim >= self._dedup_threshold:
                    # Update existing entry instead of creating duplicate
                    existing.source_count += len(raw_texts)
                    existing.confidence = max(0.0, min(1.0, existing.confidence + 0.05))
                    existing.last_validated = time.time()
                    existing.summary = summary  # refresh with latest
                    logger.info("Merged into existing entry %s (sim=%.3f)", existing.entry_id, sim)
                    return existing

        eid = f"ke_{hashlib.md5(topic.encode()).hexdigest()[:8]}"
        entry = KnowledgeEntry(
            entry_id=eid,
            topic=topic,
            summary=summary,
            source_count=len(raw_texts),
            confidence=confidence,
            associations=top_keywords[:5],
            embedding=embedding,
        )
        self._entries[eid] = entry
        logger.info("Distilled new entry: %s (%d sources)", topic, len(raw_texts))
        return entry

    async def query(self, question: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Semantic search over the knowledge base."""
        if not self._entries:
            return []
        q_emb = _text_to_embedding(question)
        scored = []
        for e in self._entries.values():
            if e.embedding is not None:
                sim = _cosine_similarity(q_emb, e.embedding)
                scored.append((sim, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"entry_id": e.entry_id, "topic": e.topic, "summary": e.summary,
             "confidence": e.confidence, "relevance": round(s, 4)}
            for s, e in scored[:top_k]
        ]

    async def validate(self, entry_id: str) -> dict[str, Any]:
        """Mark a knowledge entry as recently validated."""
        entry = self._entries.get(entry_id)
        if entry is None:
            return {"error": f"Entry {entry_id} not found"}
        entry.last_validated = time.time()
        entry.confidence = max(0.0, min(1.0, entry.confidence + 0.05))
        return {"entry_id": entry_id, "confidence": entry.confidence, "validated_at": entry.last_validated}

    async def prune_stale(self, max_age_seconds: float = 86400 * 30) -> int:
        """Remove entries not validated within max_age_seconds."""
        now = time.time()
        stale = [eid for eid, e in self._entries.items() if now - e.last_validated > max_age_seconds]
        for eid in stale:
            del self._entries[eid]
        logger.info("Pruned %d stale knowledge entries", len(stale))
        return len(stale)

    @property
    def size(self) -> int:
        return len(self._entries)


# ---------------------------------------------------------------------------
# SelfBenchmarker — performance measurement and tracking
# ---------------------------------------------------------------------------

class SelfBenchmarker:
    """Measures, records, and analyses system performance benchmarks.

    Tracks metrics over time and detects statistically significant changes
    using Welch's t-test.
    """

    def __init__(self) -> None:
        self._benchmarks: dict[str, list[BenchmarkResult]] = {}  # metric -> history
        self._baselines: dict[str, float] = {}

    async def set_baseline(self, metric_name: str, value: float) -> None:
        """Set a baseline value for a metric."""
        self._baselines[metric_name] = value

    async def record(
        self,
        metric_name: str,
        value: float,
        unit: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> BenchmarkResult:
        """Record a benchmark measurement."""
        baseline = self._baselines.get(metric_name, value)
        delta_pct = ((value - baseline) / max(abs(baseline), 1e-12)) * 100

        bid = f"bm_{metric_name}_{int(time.time())}"
        result = BenchmarkResult(
            benchmark_id=bid,
            metric_name=metric_name,
            value=value,
            unit=unit,
            baseline=baseline,
            delta_pct=round(delta_pct, 2),
            metadata=metadata or {},
        )
        self._benchmarks.setdefault(metric_name, []).append(result)
        return result

    async def trend(self, metric_name: str, window: int = 20) -> dict[str, Any]:
        """Analyse recent trend for a metric."""
        history = self._benchmarks.get(metric_name, [])
        if len(history) < 2:
            return {"metric": metric_name, "trend": "insufficient data", "points": len(history)}

        recent = history[-window:]
        values = [r.value for r in recent]
        mean_val = statistics.mean(values)
        std_val = statistics.stdev(values) if len(values) > 1 else 0.0

        # Simple linear regression for direction
        x = np.arange(len(values), dtype=np.float64)
        y = np.array(values, dtype=np.float64)
        slope = float(np.polyfit(x, y, 1)[0]) if len(values) > 1 else 0.0

        if slope > std_val * 0.1:
            direction = "improving" if metric_name.endswith("_rate") else "increasing"
        elif slope < -std_val * 0.1:
            direction = "degrading" if metric_name.endswith("_rate") else "decreasing"
        else:
            direction = "stable"

        return {
            "metric": metric_name,
            "trend": direction,
            "mean": round(mean_val, 4),
            "std": round(std_val, 4),
            "slope": round(slope, 6),
            "points": len(values),
            "latest": round(values[-1], 4),
            "baseline": self._baselines.get(metric_name),
        }

    async def compare_to_baseline(self, metric_name: str) -> dict[str, Any]:
        """Statistical comparison of recent measurements vs baseline.

        Uses Welch's t-test approximation for small-sample significance.
        """
        history = self._benchmarks.get(metric_name, [])
        baseline = self._baselines.get(metric_name)
        if baseline is None:
            return {"error": "no baseline set"}
        if len(history) < 3:
            return {"error": "insufficient measurements (need >= 3)"}

        values = np.array([r.value for r in history[-20:]])
        mean_val = float(np.mean(values))
        std_val = float(np.std(values, ddof=1))
        n = len(values)

        # One-sample t-test against baseline
        t_stat = (mean_val - baseline) / max(std_val / math.sqrt(n), 1e-12)
        # Rough p-value approximation (two-tailed, using normal approx for large n)
        p_approx = 2 * (1.0 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))

        significant = p_approx < 0.05
        better = mean_val > baseline if metric_name.endswith("_rate") else mean_val < baseline

        return {
            "metric": metric_name,
            "baseline": baseline,
            "mean": round(mean_val, 4),
            "std": round(std_val, 4),
            "t_statistic": round(t_stat, 4),
            "p_value_approx": round(p_approx, 6),
            "significant": significant,
            "improved": better and significant,
            "n": n,
        }

    async def leaderboard(self) -> list[dict[str, Any]]:
        """Return latest value for all tracked metrics with delta from baseline."""
        board = []
        for metric, history in self._benchmarks.items():
            if history:
                latest = history[-1]
                board.append({
                    "metric": metric,
                    "latest_value": latest.value,
                    "unit": latest.unit,
                    "delta_pct": latest.delta_pct,
                    "measurements": len(history),
                })
        board.sort(key=lambda x: abs(x["delta_pct"]), reverse=True)
        return board


# ---------------------------------------------------------------------------
# PrometheusEngine — orchestrates all self-evolution subsystems
# ---------------------------------------------------------------------------

class PrometheusEngine:
    """Top-level orchestrator for the Self-Evolution Engine.

    Coordinates ResearchDaemon, ContinuousTestRunner, CrisisPreparator,
    KnowledgeDistillery, and SelfBenchmarker into a unified improvement loop.

    Usage::

        engine = PrometheusEngine()
        report = await engine.evolution_cycle()
    """

    def __init__(
        self,
        domains: list[str] | None = None,
        control_limit_sigma: float = 2.0,
        dedup_threshold: float = 0.85,
    ) -> None:
        self.research = ResearchDaemon(domains=domains)
        self.tests = ContinuousTestRunner(control_limit_sigma=control_limit_sigma)
        self.crisis = CrisisPreparator()
        self.knowledge = KnowledgeDistillery(dedup_threshold=dedup_threshold)
        self.benchmarks = SelfBenchmarker()
        self._cycle_count: int = 0

    async def evolution_cycle(self) -> dict[str, Any]:
        """Run one full self-evolution cycle.

        1. Research: scan all domains for new findings.
        2. Distill: compress findings into knowledge entries.
        3. Benchmark: record current metrics.
        4. Crisis check: evaluate readiness.
        5. Return comprehensive report.
        """
        self._cycle_count += 1
        report: dict[str, Any] = {"cycle": self._cycle_count, "timestamp": time.time()}

        # 1. Research
        findings_by_domain = await self.research.scan_all_domains()
        total_findings = sum(len(v) for v in findings_by_domain.values())
        report["research"] = {
            "domains_scanned": len(findings_by_domain),
            "new_findings": total_findings,
        }

        # 2. Distill findings into knowledge
        for domain, findings in findings_by_domain.items():
            if findings:
                raw_texts = [f.summary for f in findings]
                await self.knowledge.distill(
                    topic=f"{domain}_cycle_{self._cycle_count}",
                    raw_texts=raw_texts,
                    source_label="research_daemon",
                )
        report["knowledge"] = {"total_entries": self.knowledge.size}

        # 3. Benchmark
        await self.benchmarks.record("knowledge_size", float(self.knowledge.size), "entries")
        await self.benchmarks.record("research_findings_rate", float(total_findings), "findings/cycle")
        await self.benchmarks.record("test_pass_rate", self.tests.overall_pass_rate, "ratio")
        report["benchmarks"] = await self.benchmarks.leaderboard()

        # 4. Crisis readiness
        report["readiness"] = await self.crisis.readiness_score()

        # 5. Summary
        report["health"] = "healthy" if self.tests.overall_pass_rate >= 0.9 else "degraded"

        logger.info(
            "Prometheus cycle %d complete: %d findings, %d knowledge entries, health=%s",
            self._cycle_count, total_findings, self.knowledge.size, report["health"],
        )
        return report

    async def status(self) -> dict[str, Any]:
        """Return a snapshot of engine state."""
        return {
            "cycles_completed": self._cycle_count,
            "research_total_findings": self.research.total_findings,
            "research_scans": self.research.scan_count,
            "test_runs": self.tests.total_runs,
            "test_pass_rate": round(self.tests.overall_pass_rate, 4),
            "knowledge_entries": self.knowledge.size,
            "crisis_scenarios": len(self.crisis._scenarios),
            "benchmark_metrics": len(self.benchmarks._benchmarks),
        }
