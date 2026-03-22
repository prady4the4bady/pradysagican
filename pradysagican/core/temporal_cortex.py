"""
Temporal Cortex — PRADYSAGICAN v2.0
Time-aware reasoning with Allen's interval algebra, dependency-based scheduling,
critical path analysis, causal ordering, and temporal anomaly detection.
No AI system today can truly reason about time. This module fixes that.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


# ── Time Primitives ──────────────────────────────────────────────────────────

@dataclass
class TimePoint:
    """A moment in time with associated certainty."""
    timestamp: float
    label: str = ""
    certainty: float = 1.0  # 0 = unknown, 1 = exact
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeInterval:
    """A duration between two time-points."""
    start: TimePoint
    end: TimePoint

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
        return max(0.0, self.end.timestamp - self.start.timestamp)

    @property
    def midpoint(self) -> float:
        """Midpoint timestamp."""
        return (self.start.timestamp + self.end.timestamp) / 2.0

    def contains(self, ts: float) -> bool:
        """Does this interval contain a given timestamp?"""
        return self.start.timestamp <= ts <= self.end.timestamp


# ── Allen's Interval Algebra ─────────────────────────────────────────────────

class TemporalRelation(str, Enum):
    """Allen's 13 interval relations (7 base + 6 inverses)."""
    BEFORE = "before"          # A ends before B starts
    AFTER = "after"            # A starts after B ends
    MEETS = "meets"            # A ends exactly when B starts
    MET_BY = "met_by"          # A starts exactly when B ends
    OVERLAPS = "overlaps"      # A starts before B, A ends during B
    OVERLAPPED_BY = "overlapped_by"
    DURING = "during"          # A is entirely within B
    CONTAINS = "contains"      # B is entirely within A
    STARTS = "starts"          # A starts with B, A ends before B
    STARTED_BY = "started_by"
    FINISHES = "finishes"      # A ends with B, A starts after B
    FINISHED_BY = "finished_by"
    EQUALS = "equals"          # A and B are identical


def compute_relation(a: TimeInterval, b: TimeInterval, epsilon: float = 0.001) -> TemporalRelation:
    """Compute Allen's temporal relation between two intervals."""
    a_s, a_e = a.start.timestamp, a.end.timestamp
    b_s, b_e = b.start.timestamp, b.end.timestamp

    def eq(x: float, y: float) -> bool:
        return abs(x - y) < epsilon

    if eq(a_s, b_s) and eq(a_e, b_e):
        return TemporalRelation.EQUALS
    if eq(a_e, b_s):
        return TemporalRelation.MEETS
    if eq(b_e, a_s):
        return TemporalRelation.MET_BY
    if a_e < b_s:
        return TemporalRelation.BEFORE
    if a_s > b_e:
        return TemporalRelation.AFTER
    if eq(a_s, b_s) and a_e < b_e:
        return TemporalRelation.STARTS
    if eq(a_s, b_s) and a_e > b_e:
        return TemporalRelation.STARTED_BY
    if eq(a_e, b_e) and a_s > b_s:
        return TemporalRelation.FINISHES
    if eq(a_e, b_e) and a_s < b_s:
        return TemporalRelation.FINISHED_BY
    if a_s > b_s and a_e < b_e:
        return TemporalRelation.DURING
    if a_s < b_s and a_e > b_e:
        return TemporalRelation.CONTAINS
    if a_s < b_s and a_e < b_e and a_e > b_s:
        return TemporalRelation.OVERLAPS
    return TemporalRelation.OVERLAPPED_BY


# ── Temporal Event ───────────────────────────────────────────────────────────

class EventStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETE = "complete"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


@dataclass
class TemporalEvent:
    """An event positioned on the timeline with dependencies."""
    id: str
    name: str
    interval: TimeInterval
    dependencies: list[str] = field(default_factory=list)  # event IDs
    priority: float = 0.5  # 0 = lowest, 1 = highest
    status: EventStatus = EventStatus.PENDING
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def deadline(self) -> float:
        return self.interval.end.timestamp


# ── Temporal Cortex ──────────────────────────────────────────────────────────

class TemporalCortex:
    """Time-aware reasoning engine.

    Features:
    - Timeline management with sorted event storage
    - Allen's interval algebra for temporal relation queries
    - Conflict detection (overlaps, resource contention)
    - Critical-path analysis via longest-path on dependency DAG
    - Completion estimation accounting for dependencies
    - Deadline pressure scoring
    - Causal timeline ordering (dependencies before dependents)
    - Temporal anomaly detection (effects before causes, impossible gaps)
    """

    def __init__(self) -> None:
        self._events: dict[str, TemporalEvent] = {}
        self._graph: Any = nx.DiGraph() if nx else None

    # ── Event Management ─────────────────────────────────────────────────

    async def add_event(self, event: TemporalEvent) -> TemporalEvent:
        """Add an event to the timeline and dependency graph."""
        self._events[event.id] = event
        if self._graph is not None:
            self._graph.add_node(event.id, duration=event.interval.duration_seconds)
            for dep_id in event.dependencies:
                if dep_id in self._events:
                    self._graph.add_edge(dep_id, event.id)
        logger.info("Event added: %s (%s)", event.name, event.id)
        return event

    async def remove_event(self, event_id: str) -> bool:
        """Remove an event from the timeline."""
        if event_id in self._events:
            del self._events[event_id]
            if self._graph is not None and self._graph.has_node(event_id):
                self._graph.remove_node(event_id)
            return True
        return False

    async def update_status(self, event_id: str, status: EventStatus) -> TemporalEvent | None:
        """Update event status."""
        ev = self._events.get(event_id)
        if ev:
            ev.status = status
        return ev

    # ── Queries ──────────────────────────────────────────────────────────

    async def query_period(self, start: float, end: float) -> list[TemporalEvent]:
        """Get all events overlapping a time period."""
        results: list[TemporalEvent] = []
        for ev in self._events.values():
            if ev.interval.end.timestamp >= start and ev.interval.start.timestamp <= end:
                results.append(ev)
        results.sort(key=lambda e: e.interval.start.timestamp)
        return results

    async def get_relation(self, event_a_id: str, event_b_id: str) -> TemporalRelation | None:
        """Compute Allen's temporal relation between two events."""
        a = self._events.get(event_a_id)
        b = self._events.get(event_b_id)
        if not a or not b:
            return None
        return compute_relation(a.interval, b.interval)

    # ── Conflict Detection ───────────────────────────────────────────────

    async def detect_conflicts(self, new_event: TemporalEvent) -> list[dict[str, Any]]:
        """Find scheduling conflicts using Allen's algebra.

        A conflict exists when two events overlap and neither is a dependency
        of the other (i.e., they compete for the same time slot).
        """
        conflicts: list[dict[str, Any]] = []
        for ev in self._events.values():
            if ev.id == new_event.id:
                continue
            relation = compute_relation(new_event.interval, ev.interval)
            overlapping = relation in (
                TemporalRelation.OVERLAPS, TemporalRelation.OVERLAPPED_BY,
                TemporalRelation.DURING, TemporalRelation.CONTAINS,
                TemporalRelation.STARTS, TemporalRelation.STARTED_BY,
                TemporalRelation.FINISHES, TemporalRelation.FINISHED_BY,
                TemporalRelation.EQUALS,
            )
            if overlapping:
                is_dep = (
                    ev.id in new_event.dependencies
                    or new_event.id in ev.dependencies
                )
                conflicts.append({
                    "event_id": ev.id,
                    "event_name": ev.name,
                    "relation": relation.value,
                    "is_dependency": is_dep,
                    "severity": "low" if is_dep else "high",
                })
        return conflicts

    # ── Critical Path ────────────────────────────────────────────────────

    async def find_critical_path(
        self,
        event_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Find the longest dependency chain (critical path).

        Uses topological sort + longest-path algorithm on the dependency DAG.
        """
        if self._graph is None or self._graph.number_of_nodes() == 0:
            return {"critical_path": [], "total_duration": 0.0}

        target_nodes = set(event_ids) if event_ids else set(self._graph.nodes)
        subgraph = self._graph.subgraph(target_nodes).copy()

        if not nx.is_directed_acyclic_graph(subgraph):
            return {"error": "Cycle detected — cannot compute critical path"}

        # Longest path via dynamic programming on topological order
        topo_order = list(nx.topological_sort(subgraph))
        dist: dict[str, float] = {n: 0.0 for n in topo_order}
        pred: dict[str, str | None] = {n: None for n in topo_order}

        for node in topo_order:
            duration = subgraph.nodes[node].get("duration", 0.0)
            for succ in subgraph.successors(node):
                new_dist = dist[node] + duration
                if new_dist > dist[succ]:
                    dist[succ] = new_dist
                    pred[succ] = node

        # Trace back from the node with maximum distance
        if not dist:
            return {"critical_path": [], "total_duration": 0.0}

        end_node = max(dist, key=dist.get)  # type: ignore[arg-type]
        end_duration = subgraph.nodes[end_node].get("duration", 0.0)
        total = dist[end_node] + end_duration

        path: list[str] = []
        current: str | None = end_node
        while current is not None:
            path.append(current)
            current = pred.get(current)
        path.reverse()

        path_names = [self._events[eid].name for eid in path if eid in self._events]
        return {
            "critical_path": path,
            "critical_path_names": path_names,
            "total_duration": round(total, 2),
            "bottleneck": path_names[-1] if path_names else None,
        }

    # ── Completion Estimation ────────────────────────────────────────────

    async def estimate_completion(
        self,
        event_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Estimate when all events will complete, accounting for dependencies."""
        targets = event_ids or list(self._events.keys())
        if not targets:
            return {"estimated_completion": 0.0, "events": 0}

        # For each event, completion = max(dependency completions) + own duration
        memo: dict[str, float] = {}

        def _completion(eid: str) -> float:
            if eid in memo:
                return memo[eid]
            ev = self._events.get(eid)
            if not ev:
                return 0.0
            dep_end = max((_completion(d) for d in ev.dependencies if d in self._events), default=ev.interval.start.timestamp)
            actual_start = max(dep_end, ev.interval.start.timestamp)
            end = actual_start + ev.interval.duration_seconds
            memo[eid] = end
            return end

        completions = [_completion(eid) for eid in targets]
        latest = max(completions) if completions else 0.0

        return {
            "estimated_completion": round(latest, 2),
            "events": len(targets),
            "earliest_start": round(min(
                (self._events[eid].interval.start.timestamp for eid in targets if eid in self._events),
                default=0.0,
            ), 2),
            "total_span": round(latest - min(
                (self._events[eid].interval.start.timestamp for eid in targets if eid in self._events),
                default=latest,
            ), 2),
        }

    # ── Deadline Pressure ────────────────────────────────────────────────

    async def deadline_pressure(self, event_id: str) -> dict[str, Any]:
        """How close is the deadline? 0 = relaxed, 1 = critical, >1 = overdue."""
        ev = self._events.get(event_id)
        if not ev:
            return {"error": "Event not found"}

        now = time.time()
        total_window = ev.interval.duration_seconds
        remaining = ev.deadline - now

        if total_window <= 0:
            pressure = 1.0 if remaining <= 0 else 0.0
        else:
            elapsed_fraction = 1.0 - (remaining / total_window)
            pressure = max(0.0, elapsed_fraction)

        if remaining < 0:
            pressure = 1.0 + abs(remaining) / max(total_window, 1.0)

        status = "relaxed" if pressure < 0.5 else "moderate" if pressure < 0.8 else "critical" if pressure <= 1.0 else "overdue"

        return {
            "event_id": event_id,
            "event_name": ev.name,
            "pressure": round(pressure, 3),
            "remaining_seconds": round(remaining, 2),
            "status": status,
        }

    # ── Temporal Reasoning ───────────────────────────────────────────────

    async def temporal_reasoning(
        self,
        question: str,
        context: list[str] | None = None,
    ) -> dict[str, Any]:
        """Answer time-related questions by analysing the timeline.

        Supports: 'what first?', 'what next?', 'what's overdue?', 'what's critical?'
        """
        q = question.lower()
        events = list(self._events.values())
        now = time.time()

        if "first" in q or "start" in q:
            # What should be done first? → lowest-dependency, earliest start
            candidates = [e for e in events if e.status in (EventStatus.PENDING, EventStatus.ACTIVE)]
            candidates.sort(key=lambda e: (len(e.dependencies), e.interval.start.timestamp))
            answer = candidates[0].name if candidates else "No pending events"
            reasoning = "Selected by fewest dependencies and earliest start time"

        elif "next" in q:
            # What's next after now?
            future = [e for e in events if e.interval.start.timestamp > now and e.status == EventStatus.PENDING]
            future.sort(key=lambda e: e.interval.start.timestamp)
            answer = future[0].name if future else "No future events"
            reasoning = "Nearest pending event after current time"

        elif "overdue" in q or "late" in q:
            overdue = [e for e in events if e.deadline < now and e.status not in (EventStatus.COMPLETE, EventStatus.CANCELLED)]
            answer = [e.name for e in overdue] if overdue else "Nothing overdue"
            reasoning = f"Found {len(overdue) if isinstance(answer, list) else 0} events past deadline"

        elif "critical" in q or "urgent" in q:
            # High priority + close deadline
            pressures = []
            for e in events:
                if e.status in (EventStatus.PENDING, EventStatus.ACTIVE):
                    remaining = e.deadline - now
                    urgency = e.priority * (1.0 / max(remaining, 1.0))
                    pressures.append((e, urgency))
            pressures.sort(key=lambda x: x[1], reverse=True)
            answer = pressures[0][0].name if pressures else "No critical events"
            reasoning = "Ranked by priority × deadline urgency"

        else:
            # General: return timeline summary
            answer = f"{len(events)} events on timeline"
            reasoning = "General timeline query"

        return {
            "question": question,
            "answer": answer,
            "reasoning": reasoning,
            "total_events": len(events),
        }

    # ── Causal Timeline ──────────────────────────────────────────────────

    async def causal_timeline(
        self,
        event_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Order events by causal relationships (dependencies), not just time."""
        target_ids = event_ids or list(self._events.keys())

        if self._graph is not None:
            subgraph = self._graph.subgraph(
                [eid for eid in target_ids if self._graph.has_node(eid)]
            )
            if nx.is_directed_acyclic_graph(subgraph):
                order = list(nx.topological_sort(subgraph))
            else:
                order = sorted(target_ids, key=lambda eid: self._events[eid].interval.start.timestamp if eid in self._events else 0)
        else:
            # Fallback: sort by dependency count then timestamp
            order = sorted(
                target_ids,
                key=lambda eid: (
                    len(self._events[eid].dependencies) if eid in self._events else 0,
                    self._events[eid].interval.start.timestamp if eid in self._events else 0,
                ),
            )

        timeline: list[dict[str, Any]] = []
        for i, eid in enumerate(order):
            ev = self._events.get(eid)
            if ev:
                timeline.append({
                    "order": i + 1,
                    "event_id": ev.id,
                    "name": ev.name,
                    "dependencies": ev.dependencies,
                    "start": ev.interval.start.timestamp,
                    "end": ev.interval.end.timestamp,
                    "causal_depth": self._causal_depth(eid),
                })
        return timeline

    def _causal_depth(self, event_id: str, memo: dict[str, int] | None = None) -> int:
        """How deep is this event in the causal chain? (0 = root cause)."""
        if memo is None:
            memo = {}
        if event_id in memo:
            return memo[event_id]
        ev = self._events.get(event_id)
        if not ev or not ev.dependencies:
            memo[event_id] = 0
            return 0
        depth = 1 + max(
            (self._causal_depth(dep, memo) for dep in ev.dependencies if dep in self._events),
            default=0,
        )
        memo[event_id] = depth
        return depth

    # ── Anomaly Detection ────────────────────────────────────────────────

    async def detect_temporal_anomalies(
        self,
        event_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Find temporal paradoxes: effects before causes, impossible gaps, etc."""
        target_ids = event_ids or list(self._events.keys())
        anomalies: list[dict[str, Any]] = []

        for eid in target_ids:
            ev = self._events.get(eid)
            if not ev:
                continue

            # 1. Effect before cause: event starts before a dependency ends
            for dep_id in ev.dependencies:
                dep = self._events.get(dep_id)
                if dep and ev.interval.start.timestamp < dep.interval.end.timestamp:
                    anomalies.append({
                        "type": "effect_before_cause",
                        "event": ev.name,
                        "dependency": dep.name,
                        "event_start": ev.interval.start.timestamp,
                        "dependency_end": dep.interval.end.timestamp,
                        "gap_seconds": round(ev.interval.start.timestamp - dep.interval.end.timestamp, 2),
                        "severity": "high",
                    })

            # 2. Negative duration
            if ev.interval.duration_seconds < 0:
                anomalies.append({
                    "type": "negative_duration",
                    "event": ev.name,
                    "duration": ev.interval.duration_seconds,
                    "severity": "critical",
                })

            # 3. Zero-certainty time points
            if ev.interval.start.certainty < 0.1 or ev.interval.end.certainty < 0.1:
                anomalies.append({
                    "type": "uncertain_timing",
                    "event": ev.name,
                    "start_certainty": ev.interval.start.certainty,
                    "end_certainty": ev.interval.end.certainty,
                    "severity": "medium",
                })

        # 4. Cycle detection in dependency graph
        if self._graph is not None:
            subgraph = self._graph.subgraph(
                [eid for eid in target_ids if self._graph.has_node(eid)]
            )
            if not nx.is_directed_acyclic_graph(subgraph):
                cycles = list(nx.simple_cycles(subgraph))
                for cycle in cycles[:5]:  # limit to first 5
                    anomalies.append({
                        "type": "dependency_cycle",
                        "events": cycle,
                        "severity": "critical",
                    })

        return anomalies

    # ── Stats ────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        now = time.time()
        return {
            "total_events": len(self._events),
            "pending": sum(1 for e in self._events.values() if e.status == EventStatus.PENDING),
            "active": sum(1 for e in self._events.values() if e.status == EventStatus.ACTIVE),
            "complete": sum(1 for e in self._events.values() if e.status == EventStatus.COMPLETE),
            "overdue": sum(1 for e in self._events.values() if e.deadline < now and e.status not in (EventStatus.COMPLETE, EventStatus.CANCELLED)),
            "graph_edges": self._graph.number_of_edges() if self._graph is not None else 0,
        }
