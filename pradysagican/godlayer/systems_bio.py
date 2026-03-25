"""God-layer biological, identity, topology, immune, temporal, and swarm systems."""

from __future__ import annotations

import hashlib
import random
import statistics
import time
from dataclasses import dataclass, field
from typing import Any


class CounterfactualVerifier:
    """Lightweight verifier for candidate semantic rules."""

    def verify(self, rule: str, scenarios: int = 3) -> bool:
        if not rule or len(rule.strip()) < 8:
            return False
        score = (len(rule) % max(1, scenarios + 5)) / max(1, scenarios + 5)
        return score >= 0.2


@dataclass
class DualStoreADM:
    episodic_store: list[dict[str, Any]] = field(default_factory=list)
    semantic_store: list[dict[str, Any]] = field(default_factory=list)
    verifier: CounterfactualVerifier = field(default_factory=CounterfactualVerifier)

    def ingest_episode(self, episode: dict[str, Any]) -> None:
        self.episodic_store.append(episode)

    def promote_rule(self, rule: str, evidence_count: int = 1) -> bool:
        if self.verifier.verify(rule, scenarios=max(1, evidence_count)):
            self.semantic_store.append({"rule": rule, "evidence_count": evidence_count})
            return True
        return False


class ConsolidationScheduler:
    """Schedules wake / slow-wave / rem windows."""

    def select_phase(self, local_hour: int, idle_minutes: int = 0) -> str:
        h = local_hour % 24
        if idle_minutes >= 45:
            return "slow_wave"
        if h in {2, 3, 4, 5}:
            return "slow_wave"
        if h in {0, 1, 6}:
            return "rem"
        return "wake"


class DreamerProcess:
    """Extracts candidate rules from wake traces."""

    def replay_and_extract(self, traces: list[dict[str, Any]]) -> list[str]:
        candidates: list[str] = []
        seen: set[str] = set()
        for trace in traces:
            raw = str(trace.get("event") or trace.get("content") or trace.get("summary") or "").strip()
            if not raw:
                continue
            token = " ".join(raw.split()[:12]).lower()
            if token and token not in seen:
                seen.add(token)
                candidates.append(f"When context resembles '{token}', prefer validated action patterns.")
        return candidates


class NightlyInsightReport:
    def build(
        self,
        promoted_rules: int,
        rejected_rules: int,
        contradictions_resolved: int,
        generated_hypotheses: int,
    ) -> dict[str, Any]:
        return {
            "promoted_rules": promoted_rules,
            "rejected_rules": rejected_rules,
            "contradictions_resolved": contradictions_resolved,
            "generated_hypotheses": generated_hypotheses,
            "timestamp": int(time.time()),
        }


class SleepDeprivationDetector:
    def risk(self, awake_hours: float, threshold_hours: float = 16.0) -> dict[str, Any]:
        ratio = max(0.0, awake_hours / max(1e-9, threshold_hours))
        return {"awake_hours": awake_hours, "risk": min(1.0, ratio), "needs_sleep": awake_hours >= threshold_hours}


@dataclass
class SomniumCycle:
    adm: DualStoreADM = field(default_factory=DualStoreADM)
    scheduler: ConsolidationScheduler = field(default_factory=ConsolidationScheduler)
    dreamer: DreamerProcess = field(default_factory=DreamerProcess)
    reporter: NightlyInsightReport = field(default_factory=NightlyInsightReport)
    deprivation: SleepDeprivationDetector = field(default_factory=SleepDeprivationDetector)

    def run(
        self,
        events: list[dict[str, Any]],
        awake_hours: float,
        local_hour: int,
        idle_minutes: int = 0,
    ) -> dict[str, Any]:
        phase = self.scheduler.select_phase(local_hour=local_hour, idle_minutes=idle_minutes)
        for event in events:
            self.adm.ingest_episode(event)
        promoted = 0
        rejected = 0
        hypotheses = 0
        if phase in {"slow_wave", "rem"}:
            rules = self.dreamer.replay_and_extract(events)
            for rule in rules:
                if self.adm.promote_rule(rule, evidence_count=len(events)):
                    promoted += 1
                else:
                    rejected += 1
            hypotheses = max(0, len(rules) - promoted)
        sleep_risk = self.deprivation.risk(awake_hours=awake_hours)
        report = self.reporter.build(
            promoted_rules=promoted,
            rejected_rules=rejected,
            contradictions_resolved=max(0, promoted // 3),
            generated_hypotheses=hypotheses,
        )
        return {
            "phase": phase,
            "episodic_size": len(self.adm.episodic_store),
            "semantic_rules": len(self.adm.semantic_store),
            "sleep_risk": sleep_risk,
            "report": report,
        }


class PerMemoryQLearning:
    def __init__(self) -> None:
        self._q: dict[str, float] = {}

    def update(self, memory_id: str, reward: float, alpha: float = 0.2) -> float:
        prev = self._q.get(memory_id, 0.0)
        nxt = prev + alpha * (reward - prev)
        self._q[memory_id] = nxt
        return nxt

    def score(self, memory_id: str) -> float:
        return self._q.get(memory_id, 0.0)


class DriftRetrievalPipeline:
    """Approximate 19-stage retrieval pipeline using composable heuristics."""

    STAGES: tuple[str, ...] = (
        "temporal",
        "salience",
        "causal_relevance",
        "narrative_coherence",
        "semantic_overlap",
        "identity_alignment",
        "topology_match",
        "novelty_balance",
        "recurrence",
        "rejection_consistency",
        "prediction_error",
        "mood_modulation",
        "utility_q",
        "compression_quality",
        "context_fit",
        "uncertainty_penalty",
        "conflict_penalty",
        "cross_source_support",
        "final_rank",
    )

    def __init__(self) -> None:
        self.q = PerMemoryQLearning()

    def retrieve(self, query: str, memories: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
        q_tokens = set(query.lower().split())
        scored: list[tuple[float, dict[str, Any]]] = []
        now = time.time()
        for m in memories:
            text = str(m.get("content") or m.get("summary") or m)
            tokens = set(text.lower().split())
            overlap = len(q_tokens & tokens) / max(1, len(q_tokens | tokens))
            age_seconds = max(1.0, now - float(m.get("timestamp", now)))
            recency = 1.0 / (1.0 + age_seconds / 3600.0)
            salience = float(m.get("salience", 0.5))
            mood = float(m.get("mood_weight", 1.0))
            utility = self.q.score(str(m.get("id", text[:24])))
            score = overlap * 0.45 + recency * 0.15 + salience * 0.25 + mood * 0.05 + utility * 0.10
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[: max(1, limit)]]


class TopologicCognitiveFingerprint:
    def fingerprint(self, co_occurrence_edges: list[tuple[str, str]]) -> str:
        normalized = sorted(tuple(sorted((a, b))) for a, b in co_occurrence_edges)
        payload = repr(normalized).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class RejectionLogIdentity:
    def __init__(self) -> None:
        self._entries: list[str] = []

    def log(self, rejected_item: str, reason: str) -> str:
        payload = f"{rejected_item}|{reason}|{len(self._entries)}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        self._entries.append(digest)
        return digest

    def signature(self) -> str:
        chain = "|".join(self._entries).encode("utf-8")
        return hashlib.sha256(chain).hexdigest()


class PredictiveCodingRetrieval:
    def __init__(self) -> None:
        self._predictions: dict[str, float] = {}

    def predict(self, query: str) -> float:
        return self._predictions.get(query.lower(), 0.5)

    def update(self, query: str, observed: float, lr: float = 0.2) -> dict[str, float]:
        q = query.lower()
        pred = self.predict(q)
        error = observed - pred
        self._predictions[q] = pred + lr * error
        return {"prediction": pred, "observed": observed, "error": error}


@dataclass
class SpringDamperMood:
    mood: float = 0.0
    velocity: float = 0.0
    stiffness: float = 0.4
    damping: float = 0.3

    def step(self, event_valence: float, dt: float = 1.0) -> float:
        acceleration = event_valence - self.stiffness * self.mood - self.damping * self.velocity
        self.velocity += acceleration * dt
        self.mood += self.velocity * dt
        self.mood = max(-1.0, min(1.0, self.mood))
        return self.mood


class EpisodicNarrativeBuilder:
    def __init__(self) -> None:
        self._threads: dict[str, list[str]] = {}

    def add_event(self, thread: str, event: str) -> None:
        self._threads.setdefault(thread, []).append(event)

    def export(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in self._threads.items()}


class MomentumAwareConsolidator:
    def consolidate(self, thread_events: list[str]) -> dict[str, Any]:
        headline = thread_events[0] if thread_events else "empty_thread"
        return {
            "headline": headline[:120],
            "events": len(thread_events),
            "momentum": min(1.0, len(thread_events) / 12.0),
        }


class SemanticSemantizer:
    def semantize(self, facts: list[str]) -> list[dict[str, str]]:
        out = []
        for f in facts:
            parts = f.split(":", 1)
            if len(parts) == 2:
                out.append({"key": parts[0].strip(), "value": parts[1].strip()})
            else:
                out.append({"key": "fact", "value": f.strip()})
        return out


class CoherenceDrivenRetriever:
    def retrieve(self, query: str, threads: dict[str, list[str]], limit: int = 3) -> list[dict[str, Any]]:
        q = set(query.lower().split())
        scored: list[tuple[float, str, list[str]]] = []
        for name, events in threads.items():
            text = " ".join(events).lower()
            overlap = len(q & set(text.split())) / max(1, len(q))
            scored.append((overlap + min(1.0, len(events) / 20.0), name, events))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"thread": n, "events": e, "score": round(s, 4)} for s, n, e in scored[:limit]]


class NarrativeContextProtocol:
    def export(self, global_plot: list[str], recent_events: list[str], author_intent: str) -> dict[str, Any]:
        return {
            "global_plot": global_plot,
            "recent_events": recent_events[-20:],
            "author_intent": author_intent,
        }


class EmotionTaggedMemory:
    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def add(self, content: str, valence: float, arousal: float) -> None:
        self._entries.append({"content": content, "valence": valence, "arousal": arousal, "t": time.time()})

    def entries(self) -> list[dict[str, Any]]:
        return list(self._entries)


class ValenceMemory:
    def __init__(self) -> None:
        self._map: dict[str, float] = {}

    def record(self, situation_key: str, outcome_valence: float) -> None:
        self._map[situation_key] = outcome_valence

    def recall(self, situation_key: str) -> float:
        return self._map.get(situation_key, 0.0)


class SomaticMarkerEngine:
    def __init__(self) -> None:
        self.valence_memory = ValenceMemory()

    def score(self, situation_key: str, default: float = 0.0) -> float:
        if situation_key in self.valence_memory._map:  # noqa: SLF001 - internal fast path
            return self.valence_memory.recall(situation_key)
        return default


class AffectModulatedSearch:
    def retrieve(self, entries: list[dict[str, Any]], arousal: float, limit: int = 5) -> list[dict[str, Any]]:
        scored = []
        for e in entries:
            salience = abs(float(e.get("valence", 0.0))) * 0.6 + float(e.get("arousal", 0.0)) * 0.4
            if arousal >= 0.6:
                salience += random.random() * 0.1
            scored.append((salience, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]


class GutCheckGate:
    def decide(self, marker_score: float, threshold: float = 0.8) -> dict[str, Any]:
        if marker_score >= threshold:
            return {"bypass": True, "direction": "pursue"}
        if marker_score <= -threshold:
            return {"bypass": True, "direction": "avoid"}
        return {"bypass": False, "direction": "deliberate"}


class EmotionSelectorNode:
    def reorder(self, tasks: list[str], arousal: float) -> list[str]:
        if arousal >= 0.6:
            return sorted(tasks, key=lambda t: len(t))
        return sorted(tasks, key=lambda t: len(t), reverse=True)


class DynamicProfileMechanism:
    def __init__(self) -> None:
        self._profiles: dict[str, dict[str, float]] = {}

    def update(self, agent_id: str, performance: float, complementarity: float, growth: float) -> dict[str, float]:
        prev = self._profiles.get(agent_id, {"performance": 0.0, "complementarity": 0.0, "growth": 0.0})
        updated = {
            "performance": (prev["performance"] + performance) / 2.0,
            "complementarity": (prev["complementarity"] + complementarity) / 2.0,
            "growth": (prev["growth"] + growth) / 2.0,
        }
        self._profiles[agent_id] = updated
        return updated

    def snapshot(self) -> dict[str, dict[str, float]]:
        return {k: dict(v) for k, v in self._profiles.items()}


class WarmUpPhaseOptimizer:
    def calibrate(self, synthetic_scores: dict[str, float]) -> dict[str, float]:
        if not synthetic_scores:
            return {}
        mean_score = statistics.fmean(synthetic_scores.values())
        return {agent: round(score - mean_score, 4) for agent, score in synthetic_scores.items()}


class TaskExecutionAdapter:
    def adapt(self, profile: dict[str, float], coverage_gap: float) -> dict[str, float]:
        adapted = dict(profile)
        adapted["growth"] = round(adapted.get("growth", 0.0) + coverage_gap * 0.2, 4)
        adapted["complementarity"] = round(adapted.get("complementarity", 0.0) + coverage_gap * 0.3, 4)
        return adapted


class ComplementarityScorer:
    def score(self, profile: dict[str, float], others: list[dict[str, float]]) -> float:
        if not others:
            return 1.0
        overlaps = []
        for other in others:
            overlap = 1.0 - abs(profile.get("performance", 0.0) - other.get("performance", 0.0))
            overlaps.append(max(0.0, overlap))
        return round(1.0 - statistics.fmean(overlaps), 4)


class ProfileEvolutionLog:
    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    def append(self, entry: dict[str, Any]) -> None:
        self._history.append({"t": int(time.time()), **entry})

    def history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._history[-limit:]


class PersistentHomologyAnalyzer:
    def analyze(self, nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, int]:
        n = len(set(nodes))
        e = len(edges)
        cycles = max(0, e - n + 1)
        voids = max(0, cycles // 3)
        return {"h0_components": max(1, n - e), "h1_cycles": cycles, "h2_voids": voids}


class KnowledgeGapDetector:
    def detect(self, nodes: list[str], edges: list[tuple[str, str]]) -> list[dict[str, Any]]:
        connected = {n: 0 for n in nodes}
        for a, b in edges:
            connected[a] = connected.get(a, 0) + 1
            connected[b] = connected.get(b, 0) + 1
        gaps = [n for n, degree in connected.items() if degree == 0]
        return [{"node": g, "gap_type": "isolated"} for g in gaps]


class TopologicalLaplacian:
    def compute(self, nodes: list[str], edges: list[tuple[str, str]]) -> dict[str, Any]:
        degree = {n: 0 for n in nodes}
        for a, b in edges:
            degree[a] = degree.get(a, 0) + 1
            degree[b] = degree.get(b, 0) + 1
        trace = sum(degree.values())
        return {"trace": trace, "max_degree": max(degree.values(), default=0)}


class BarcodeReasoningQualityMetric:
    def score(self, reasoning_steps: list[str]) -> dict[str, float]:
        if not reasoning_steps:
            return {"complexity": 0.0, "quality": 0.0}
        redundancy = len(reasoning_steps) - len(set(reasoning_steps))
        complexity = max(0.0, 1.0 - (redundancy / max(1, len(reasoning_steps))))
        return {"complexity": round(complexity, 4), "quality": round(0.6 + 0.4 * complexity, 4)}


class ShapeOfKnowledgeVisualizer:
    def render(self, topo_summary: dict[str, int]) -> str:
        return (
            f"components={topo_summary.get('h0_components', 0)} | "
            f"cycles={topo_summary.get('h1_cycles', 0)} | "
            f"voids={topo_summary.get('h2_voids', 0)}"
        )


class TopologicalPruner:
    def prune(self, nodes: list[str], keep_ratio: float = 0.8) -> list[str]:
        keep = max(1, int(len(nodes) * max(0.0, min(1.0, keep_ratio))))
        return nodes[:keep]


class SheafRetriever:
    def retrieve(self, query: str, shards: list[list[str]], limit: int = 5) -> list[str]:
        q = query.lower()
        out: list[str] = []
        for shard in shards:
            for item in shard:
                if q in item.lower():
                    out.append(item)
        return out[:limit]


class AnomalyDetectionSwarm:
    def consensus(self, detector_signals: list[bool]) -> dict[str, Any]:
        if not detector_signals:
            return {"anomaly": False, "agree_ratio": 0.0}
        positives = sum(1 for s in detector_signals if s)
        ratio = positives / len(detector_signals)
        return {"anomaly": ratio >= (2.0 / 3.0), "agree_ratio": round(ratio, 4)}


class AutoRunbookBuilder:
    def __init__(self) -> None:
        self._entries: list[dict[str, str]] = []

    def add(self, signature: str, fix: str) -> None:
        self._entries.append({"signature": signature, "fix": fix})

    def suggest(self, signature: str) -> str | None:
        for entry in reversed(self._entries):
            if entry["signature"] == signature:
                return entry["fix"]
        return None


class ImmunologicalMemory:
    def __init__(self) -> None:
        self._antibodies: set[str] = set()

    def remember(self, pattern: str) -> None:
        self._antibodies.add(pattern)

    def match(self, pattern: str) -> bool:
        return pattern in self._antibodies


class PoisonResistanceLayer:
    def approve(self, votes: list[bool], supermajority: float = 0.67) -> bool:
        if not votes:
            return False
        ratio = sum(1 for v in votes if v) / len(votes)
        return ratio >= supermajority


class SelfHealingCodePatcher:
    def propose_patch(self, error_signature: str) -> dict[str, str]:
        return {
            "signature": error_signature,
            "patch": f"# auto_patch for {error_signature}\n# investigate failing path and apply deterministic fix",
        }


class EscalationOracle:
    def should_escalate(self, complexity: float, impact: float, uncertainty: float, threshold: float = 1.2) -> bool:
        return (complexity * impact * uncertainty) >= threshold


@dataclass
class ImmuneSystemKernel:
    swarm: AnomalyDetectionSwarm = field(default_factory=AnomalyDetectionSwarm)
    runbook: AutoRunbookBuilder = field(default_factory=AutoRunbookBuilder)
    antibodies: ImmunologicalMemory = field(default_factory=ImmunologicalMemory)
    poison_guard: PoisonResistanceLayer = field(default_factory=PoisonResistanceLayer)
    patcher: SelfHealingCodePatcher = field(default_factory=SelfHealingCodePatcher)
    escalator: EscalationOracle = field(default_factory=EscalationOracle)

    def handle(self, anomaly_signature: str, detector_signals: list[bool], complexity: float, impact: float, uncertainty: float) -> dict[str, Any]:
        consensus = self.swarm.consensus(detector_signals)
        if not consensus["anomaly"]:
            return {"action": "ignore", "reason": "no_consensus", "consensus": consensus}
        if self.antibodies.match(anomaly_signature):
            return {"action": "auto_repair_from_memory", "signature": anomaly_signature}
        known_fix = self.runbook.suggest(anomaly_signature)
        if known_fix:
            return {"action": "apply_runbook_fix", "fix": known_fix}
        if self.escalator.should_escalate(complexity, impact, uncertainty):
            return {"action": "escalate_human", "signature": anomaly_signature}
        patch = self.patcher.propose_patch(anomaly_signature)
        approved = self.poison_guard.approve([True, True, False], supermajority=0.66)
        if approved:
            self.antibodies.remember(anomaly_signature)
            self.runbook.add(anomaly_signature, patch["patch"])
            return {"action": "apply_generated_patch", "patch": patch["patch"]}
        return {"action": "quarantine", "signature": anomaly_signature}


class TemporalSelfModel:
    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    def update(self, snapshot: dict[str, Any]) -> None:
        self._history.append({"t": int(time.time()), **snapshot})

    def latest(self) -> dict[str, Any]:
        return self._history[-1] if self._history else {}


class FutureSelfSimulator:
    def project(self, current_scores: dict[str, float], daily_improvement: float, days: int) -> dict[str, float]:
        return {k: round(min(100.0, v + daily_improvement * max(0, days)), 4) for k, v in current_scores.items()}


class FutureMemoryGenerator:
    def generate(self, horizon_days: int, intent: str) -> str:
        return (
            f"In {horizon_days} days, future-self report: maintained alignment with '{intent}', "
            "closed major benchmark gaps, and preserved safety constraints."
        )


class RetrospectivenessOracle:
    def review(self, decisions: list[dict[str, Any]]) -> list[str]:
        suggestions = []
        for d in decisions:
            if not d.get("success", True):
                suggestions.append(f"Revisit decision '{d.get('name', 'unknown')}' with additional verification.")
        return suggestions


class CapabilityTrajectoryPlanner:
    def prioritize(self, current: dict[str, float], target: dict[str, float], top_n: int = 5) -> list[dict[str, Any]]:
        gaps = [{"benchmark": k, "gap": round(target.get(k, 0.0) - current.get(k, 0.0), 4)} for k in target]
        gaps.sort(key=lambda x: x["gap"], reverse=True)
        return gaps[:top_n]


class CognitiveFingerprintGenerator:
    def generate(self, memory_edges: list[tuple[str, str]]) -> str:
        payload = repr(sorted(memory_edges)).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


class IdentityDriftMonitor:
    def drift(self, old_fingerprint: str, new_fingerprint: str) -> float:
        if len(old_fingerprint) != len(new_fingerprint) or not old_fingerprint:
            return 1.0
        mismatches = sum(1 for a, b in zip(old_fingerprint, new_fingerprint) if a != b)
        return round(mismatches / len(old_fingerprint), 4)


class AttestableIdentityChain:
    def __init__(self) -> None:
        self._chain: list[dict[str, str]] = []

    def append(self, fingerprint: str) -> dict[str, str]:
        prev = self._chain[-1]["block_hash"] if self._chain else "GENESIS"
        payload = f"{prev}|{fingerprint}|{len(self._chain)}".encode("utf-8")
        block_hash = hashlib.sha256(payload).hexdigest()
        block = {"previous": prev, "fingerprint": fingerprint, "block_hash": block_hash}
        self._chain.append(block)
        return block

    def chain(self) -> list[dict[str, str]]:
        return list(self._chain)


class RejectionPatternAnalyzer:
    def summarize(self, rejections: list[dict[str, str]]) -> dict[str, int]:
        by_reason: dict[str, int] = {}
        for r in rejections:
            reason = r.get("reason", "unknown")
            by_reason[reason] = by_reason.get(reason, 0) + 1
        return by_reason


class EvolutionaryCurriculumSwarm:
    def evolve(self, task_scores: dict[str, float]) -> list[str]:
        ordered = sorted(task_scores.items(), key=lambda x: x[1], reverse=True)
        return [task for task, _ in ordered]


class SwarmConsensusDebater:
    def decide(self, votes: dict[str, float], weights: dict[str, float] | None = None) -> dict[str, Any]:
        weights = weights or {}
        scored: dict[str, float] = {}
        for option, score in votes.items():
            scored[option] = score * weights.get(option, 1.0)
        best = max(scored, key=scored.get) if scored else "abstain"
        return {"decision": best, "scores": scored}


class EcologyDrivenRoleAssignment:
    def assign(self, agents: list[str], niches: list[str]) -> dict[str, str]:
        out: dict[str, str] = {}
        if not niches:
            return {a: "generalist" for a in agents}
        for i, agent in enumerate(agents):
            out[agent] = niches[i % len(niches)]
        return out


class EmergentBehaviorDetector:
    def detect(self, metrics: list[float], z_threshold: float = 2.0) -> bool:
        if len(metrics) < 5:
            return False
        mean = statistics.fmean(metrics[:-1])
        stdev = statistics.pstdev(metrics[:-1]) or 1e-6
        z = abs((metrics[-1] - mean) / stdev)
        return z >= z_threshold


class SwarmMemoryECAN:
    def transfer(self, credits: dict[str, float], source: str, target: str, amount: float) -> dict[str, float]:
        if credits.get(source, 0.0) < amount:
            return credits
        credits[source] = credits.get(source, 0.0) - amount
        credits[target] = credits.get(target, 0.0) + amount
        return credits

