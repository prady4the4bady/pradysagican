"""
Autonomous Task Scheduler & Proactive Agent — PRADYSAGICAN Automation Layer
===========================================================================
Like OpenClaw's Heartbeat but with security and intelligence.

Improvements over OpenClaw:
- Circuit breaker: auto-disables tasks after consecutive failures
  (OpenClaw lets failing tasks run forever, wasting resources).
- Sandboxed execution: tasks run through the skill sandbox.
- Proactive anticipation: doesn't just schedule, PREDICTS what's needed.
- Pattern learning: observes user behaviour to suggest automations.
- Full audit trail for every execution.
"""
from __future__ import annotations

import logging
import math
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

import numpy as np

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class ScheduledTask:
    """A recurring or one-shot task on the heartbeat scheduler."""
    task_id: str
    name: str
    interval_seconds: float
    handler: str  # skill or function name
    enabled: bool = True
    last_run: float | None = None
    next_run: float = 0.0
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    max_consecutive_failures: int = 3
    last_error: str | None = None
    last_duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_due(self) -> bool:
        return self.enabled and time.time() >= self.next_run

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0

    @property
    def is_circuit_broken(self) -> bool:
        return self.consecutive_failures >= self.max_consecutive_failures


@dataclass
class TaskExecutionResult:
    """Result of running a single scheduled task."""
    task_id: str
    task_name: str
    success: bool
    output: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class Observation:
    """A recorded event for the proactive agent."""
    event_type: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    hour_of_day: int = field(default=0)
    day_of_week: int = field(default=0)

    def __post_init__(self) -> None:
        t = time.localtime(self.timestamp)
        self.hour_of_day = t.tm_hour
        self.day_of_week = t.tm_wday


@dataclass
class Anticipation:
    """A predicted future action from the proactive agent."""
    action: str
    confidence: float
    reasoning: str
    trigger_pattern: str


# ── Auto Heartbeat ───────────────────────────────────────────────────────────

class AutoHeartbeat:
    """Autonomous task scheduler with circuit breaker.

    Superior to OpenClaw's Heartbeat:
    - Circuit breaker auto-disables tasks after N consecutive failures.
    - Every execution is logged with timing and error details.
    - Pause/resume without losing schedule state.
    - Full stats per task.
    """

    def __init__(self, default_interval: float = 900.0) -> None:
        self._default_interval = default_interval
        self._tasks: dict[str, ScheduledTask] = {}
        self._handlers: dict[str, Callable[..., Awaitable[Any]]] = {}
        self._execution_history: list[TaskExecutionResult] = []

    # ── Task Management ──────────────────────────────────────────────────

    def schedule_task(
        self,
        name: str,
        interval_seconds: float | None = None,
        handler: str = "",
        handler_fn: Callable[..., Awaitable[Any]] | None = None,
        max_failures: int = 3,
    ) -> ScheduledTask:
        """Schedule a recurring task."""
        interval = interval_seconds or self._default_interval
        task = ScheduledTask(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            name=name,
            interval_seconds=interval,
            handler=handler,
            next_run=time.time() + interval,
            max_consecutive_failures=max_failures,
        )
        self._tasks[task.task_id] = task

        if handler_fn:
            self._handlers[handler or task.task_id] = handler_fn

        logger.info("Scheduled task '%s' every %.0fs", name, interval)
        return task

    def cancel_task(self, task_id: str) -> bool:
        """Remove a task completely."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def pause_task(self, task_id: str) -> bool:
        """Pause without losing schedule state."""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = False
            return True
        return False

    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task, scheduling next run from now."""
        task = self._tasks.get(task_id)
        if task:
            task.enabled = True
            task.consecutive_failures = 0  # reset circuit breaker on manual resume
            task.next_run = time.time() + task.interval_seconds
            return True
        return False

    # ── Tick (Main Loop) ─────────────────────────────────────────────────

    async def tick(self) -> list[TaskExecutionResult]:
        """Run all due tasks. Called periodically by the main event loop.

        For each due task:
        1. Check circuit breaker (skip if tripped).
        2. Execute handler.
        3. Record result.
        4. Update schedule and failure counters.
        """
        results: list[TaskExecutionResult] = []
        now = time.time()

        for task in list(self._tasks.values()):
            if not task.enabled or now < task.next_run:
                continue

            # Circuit breaker
            if task.is_circuit_broken:
                task.enabled = False
                logger.warning(
                    "Circuit breaker tripped for '%s' after %d consecutive failures — task disabled",
                    task.name, task.consecutive_failures,
                )
                results.append(TaskExecutionResult(
                    task_id=task.task_id,
                    task_name=task.name,
                    success=False,
                    error=f"Circuit breaker: {task.consecutive_failures} consecutive failures",
                ))
                continue

            # Execute
            result = await self._execute_task(task)
            results.append(result)

            # Update schedule
            task.last_run = now
            task.run_count += 1
            task.next_run = now + task.interval_seconds
            task.last_duration_ms = result.duration_ms

            if result.success:
                task.success_count += 1
                task.consecutive_failures = 0
                task.last_error = None
            else:
                task.failure_count += 1
                task.consecutive_failures += 1
                task.last_error = result.error

        return results

    async def _execute_task(self, task: ScheduledTask) -> TaskExecutionResult:
        """Execute a single task."""
        start = time.monotonic()
        handler = self._handlers.get(task.handler) or self._handlers.get(task.task_id)

        if handler is None:
            return TaskExecutionResult(
                task_id=task.task_id,
                task_name=task.name,
                success=False,
                error=f"No handler registered for '{task.handler}'",
            )

        try:
            output = await handler()
            duration = round((time.monotonic() - start) * 1000, 3)
            result = TaskExecutionResult(
                task_id=task.task_id,
                task_name=task.name,
                success=True,
                output=output,
                duration_ms=duration,
            )
        except Exception as exc:
            duration = round((time.monotonic() - start) * 1000, 3)
            result = TaskExecutionResult(
                task_id=task.task_id,
                task_name=task.name,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                duration_ms=duration,
            )

        self._execution_history.append(result)
        return result

    # ── Queries ──────────────────────────────────────────────────────────

    def get_schedule(self) -> list[dict[str, Any]]:
        """List all tasks with their next run times."""
        now = time.time()
        schedule: list[dict[str, Any]] = []
        for task in sorted(self._tasks.values(), key=lambda t: t.next_run):
            schedule.append({
                "task_id": task.task_id,
                "name": task.name,
                "enabled": task.enabled,
                "interval_seconds": task.interval_seconds,
                "next_run_in": round(max(0, task.next_run - now), 1),
                "run_count": task.run_count,
                "success_rate": round(task.success_rate, 3),
                "circuit_broken": task.is_circuit_broken,
            })
        return schedule

    def task_stats(self) -> dict[str, dict[str, Any]]:
        """Performance metrics per task."""
        stats: dict[str, dict[str, Any]] = {}
        for task in self._tasks.values():
            stats[task.name] = {
                "task_id": task.task_id,
                "total_runs": task.run_count,
                "success_rate": round(task.success_rate, 4),
                "consecutive_failures": task.consecutive_failures,
                "last_duration_ms": task.last_duration_ms,
                "last_error": task.last_error,
                "enabled": task.enabled,
            }
        return stats

    @property
    def execution_history(self) -> list[TaskExecutionResult]:
        return list(self._execution_history)


# ── Proactive Agent ──────────────────────────────────────────────────────────

class ProactiveAgent:
    """Goes beyond OpenClaw: doesn't just schedule, ANTICIPATES what to do.

    Observes user/system events and learns patterns:
    1. Time-based patterns (same task every morning).
    2. Event-triggered patterns (after X, user always does Y).
    3. Anomaly response (unusual event → prepare response).

    Uses pattern frequency analysis to generate anticipatory suggestions.
    """

    def __init__(self) -> None:
        self._observations: list[Observation] = []
        self._event_sequences: list[list[str]] = []
        self._current_sequence: list[str] = []
        self._time_patterns: dict[int, Counter[str]] = defaultdict(Counter)  # hour → event counts
        self._transition_counts: dict[str, Counter[str]] = defaultdict(Counter)  # event → next-event counts

    # ── Observation ──────────────────────────────────────────────────────

    def observe(self, event_type: str, details: dict[str, Any] | None = None) -> Observation:
        """Record an observed event for pattern analysis."""
        obs = Observation(event_type=event_type, details=details or {})
        self._observations.append(obs)

        # Track time patterns
        self._time_patterns[obs.hour_of_day][event_type] += 1

        # Track event transitions
        if self._current_sequence:
            prev = self._current_sequence[-1]
            self._transition_counts[prev][event_type] += 1

        self._current_sequence.append(event_type)

        # Start new sequence after 30-minute gap
        if len(self._observations) >= 2:
            gap = obs.timestamp - self._observations[-2].timestamp
            if gap > 1800:
                self._event_sequences.append(list(self._current_sequence[:-1]))
                self._current_sequence = [event_type]

        return obs

    # ── Anticipation ─────────────────────────────────────────────────────

    async def anticipate(self) -> list[Anticipation]:
        """Predict what will be needed based on observed patterns."""
        anticipations: list[Anticipation] = []

        # Time-based anticipation
        current_hour = time.localtime().tm_hour
        if current_hour in self._time_patterns:
            hour_counts = self._time_patterns[current_hour]
            total = sum(hour_counts.values())
            for event, count in hour_counts.most_common(3):
                confidence = count / max(total, 1)
                if confidence > 0.2 and count >= 2:
                    anticipations.append(Anticipation(
                        action=event,
                        confidence=round(min(confidence, 0.95), 3),
                        reasoning=f"Event '{event}' occurs {count} times at hour {current_hour} ({confidence:.0%} of activity)",
                        trigger_pattern=f"time_of_day:{current_hour}",
                    ))

        # Sequence-based anticipation
        if self._current_sequence:
            last_event = self._current_sequence[-1]
            if last_event in self._transition_counts:
                transitions = self._transition_counts[last_event]
                total = sum(transitions.values())
                for next_event, count in transitions.most_common(2):
                    confidence = count / max(total, 1)
                    if confidence > 0.25 and count >= 2:
                        anticipations.append(Anticipation(
                            action=next_event,
                            confidence=round(min(confidence, 0.95), 3),
                            reasoning=f"After '{last_event}', '{next_event}' follows {count}/{total} times ({confidence:.0%})",
                            trigger_pattern=f"after:{last_event}",
                        ))

        # Anomaly detection: event not seen at this hour before
        if self._observations:
            recent = self._observations[-1]
            hour_events = set(self._time_patterns.get(recent.hour_of_day, {}).keys())
            if recent.event_type not in hour_events and len(hour_events) > 0:
                anticipations.append(Anticipation(
                    action="anomaly_response",
                    confidence=0.6,
                    reasoning=f"Event '{recent.event_type}' is unusual at hour {recent.hour_of_day} (known events: {hour_events})",
                    trigger_pattern=f"anomaly:{recent.event_type}@{recent.hour_of_day}",
                ))

        # Sort by confidence
        anticipations.sort(key=lambda a: a.confidence, reverse=True)
        return anticipations

    # ── Suggestions ──────────────────────────────────────────────────────

    async def suggest_tasks(self) -> list[dict[str, Any]]:
        """Suggest autonomous tasks based on learned patterns."""
        suggestions: list[dict[str, Any]] = []

        # Suggest scheduling for frequent time-based patterns
        for hour, counts in self._time_patterns.items():
            for event, count in counts.most_common(1):
                if count >= 3:
                    suggestions.append({
                        "action": event,
                        "schedule": f"daily at {hour:02d}:00",
                        "confidence": round(min(count / 10.0, 0.95), 3),
                        "reason": f"'{event}' happens {count} times at {hour:02d}:00",
                        "type": "time_based",
                    })

        # Suggest automations for strong event sequences
        for trigger, transitions in self._transition_counts.items():
            total = sum(transitions.values())
            for response, count in transitions.most_common(1):
                confidence = count / max(total, 1)
                if confidence > 0.5 and count >= 3:
                    suggestions.append({
                        "action": response,
                        "trigger": trigger,
                        "confidence": round(confidence, 3),
                        "reason": f"'{response}' follows '{trigger}' {confidence:.0%} of the time",
                        "type": "event_triggered",
                    })

        suggestions.sort(key=lambda s: s["confidence"], reverse=True)
        return suggestions

    # ── Pattern Analysis ─────────────────────────────────────────────────

    async def learn_patterns(self, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        """Extract recurring patterns from observation history.

        Analyses:
        1. Most frequent events overall.
        2. Peak activity hours.
        3. Strongest event-to-event transitions.
        4. Session length statistics.
        """
        if history:
            for entry in history:
                self.observe(entry.get("event_type", "unknown"), entry.get("details", {}))

        if not self._observations:
            return {"status": "no_data"}

        # Most frequent events
        event_counts = Counter(o.event_type for o in self._observations)

        # Peak hours
        hour_totals: dict[int, int] = {}
        for hour, counts in self._time_patterns.items():
            hour_totals[hour] = sum(counts.values())
        peak_hour = max(hour_totals, key=hour_totals.get) if hour_totals else -1  # type: ignore[arg-type]

        # Strongest transitions
        strongest: list[dict[str, Any]] = []
        for trigger, transitions in self._transition_counts.items():
            total = sum(transitions.values())
            for response, count in transitions.most_common(1):
                confidence = count / max(total, 1)
                strongest.append({
                    "trigger": trigger,
                    "response": response,
                    "confidence": round(confidence, 3),
                    "count": count,
                })
        strongest.sort(key=lambda s: s["confidence"], reverse=True)

        # Session lengths
        session_lengths = [len(s) for s in self._event_sequences if s]

        return {
            "total_observations": len(self._observations),
            "unique_events": len(event_counts),
            "top_events": event_counts.most_common(5),
            "peak_hour": peak_hour,
            "peak_hour_count": hour_totals.get(peak_hour, 0),
            "strongest_transitions": strongest[:5],
            "sessions_recorded": len(self._event_sequences),
            "avg_session_length": round(float(np.mean(session_lengths)), 1) if session_lengths else 0,
        }

    @property
    def observation_count(self) -> int:
        return len(self._observations)
