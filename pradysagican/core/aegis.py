"""
Aegis — Conflict-Free Wiring System — PRADYSAGICAN
Provides a priority message bus, deadlock detection, resource mediation,
health monitoring, and graceful degradation for inter-component communication.

Uses asyncio.PriorityQueue for ordered messaging and networkx for deadlock
(cycle) detection in the resource-wait graph.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Awaitable

import networkx as nx  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class MessagePriority(IntEnum):
    """Lower numeric value = higher priority (compatible with PriorityQueue)."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 5
    LOW = 8
    BACKGROUND = 10


class ComponentStatus(IntEnum):
    HEALTHY = 0
    DEGRADED = 1
    UNHEALTHY = 2
    OFFLINE = 3


@dataclass(order=True)
class Message:
    """A prioritised message for the bus.

    The *order=True* on the dataclass plus the *priority* being the first
    field ensures correct ordering inside ``asyncio.PriorityQueue``.
    """
    priority: int
    message_id: str = field(compare=False)
    source: str = field(compare=False)
    target: str = field(compare=False)
    payload: dict[str, Any] = field(default_factory=dict, compare=False)
    timestamp: float = field(default_factory=time.time, compare=False)
    ttl_seconds: float = field(default=60.0, compare=False)


@dataclass
class LockInfo:
    """Tracks which component holds which resource."""
    resource_id: str
    holder: str  # component_id
    acquired_at: float = field(default_factory=time.time)
    timeout_sec: float = 30.0


@dataclass
class ComponentHealth:
    """Health record for a monitored component."""
    component_id: str
    status: ComponentStatus = ComponentStatus.HEALTHY
    last_heartbeat: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    uptime_sec: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# MessageBus — async priority queue with pub/sub
# ---------------------------------------------------------------------------

class MessageBus:
    """Priority-based asynchronous message bus for inter-component communication.

    Supports both direct messaging (source → target) and topic-based pub/sub.
    Messages are ordered by priority using ``asyncio.PriorityQueue``.
    """

    def __init__(self, max_queue_size: int = 10_000) -> None:
        self._queue: asyncio.PriorityQueue[Message] = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._subscribers: dict[str, list[Callable[[Message], Awaitable[None]]]] = defaultdict(list)
        self._message_counter: int = 0
        self._delivered: int = 0
        self._expired: int = 0

    async def publish(
        self,
        source: str,
        target: str,
        payload: dict[str, Any] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        ttl_seconds: float = 60.0,
    ) -> Message:
        """Publish a message onto the bus."""
        self._message_counter += 1
        msg = Message(
            priority=int(priority),
            message_id=f"msg_{self._message_counter}_{int(time.time())}",
            source=source,
            target=target,
            payload=payload or {},
            ttl_seconds=ttl_seconds,
        )
        await self._queue.put(msg)
        logger.debug("Published %s → %s (pri=%d)", source, target, priority)
        return msg

    async def consume(self, timeout: float = 5.0) -> Message | None:
        """Consume the highest-priority message from the bus.

        Returns None if the queue is empty or on timeout.
        Expired messages (past TTL) are silently discarded.
        """
        try:
            msg = await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

        now = time.time()
        if now - msg.timestamp > msg.ttl_seconds:
            self._expired += 1
            logger.debug("Expired message %s (age=%.1fs)", msg.message_id, now - msg.timestamp)
            return None

        self._delivered += 1
        return msg

    async def consume_batch(self, max_messages: int = 10, timeout: float = 1.0) -> list[Message]:
        """Consume up to *max_messages* in one batch."""
        batch: list[Message] = []
        for _ in range(max_messages):
            msg = await self.consume(timeout=timeout)
            if msg is None:
                break
            batch.append(msg)
        return batch

    def subscribe(self, topic: str, handler: Callable[[Message], Awaitable[None]]) -> None:
        """Register a handler for a topic (target pattern)."""
        self._subscribers[topic].append(handler)

    async def dispatch(self, msg: Message) -> int:
        """Dispatch a message to all subscribers matching its target.

        Returns the number of handlers invoked.
        """
        handlers = self._subscribers.get(msg.target, [])
        # Also match wildcard subscribers
        handlers += self._subscribers.get("*", [])
        for handler in handlers:
            try:
                await handler(msg)
            except Exception as exc:
                logger.error("Handler error for %s: %s", msg.message_id, exc)
        return len(handlers)

    async def drain(self, max_messages: int = 1000) -> list[Message]:
        """Drain all messages, dispatching to subscribers."""
        messages: list[Message] = []
        for _ in range(max_messages):
            msg = await self.consume(timeout=0.01)
            if msg is None:
                break
            await self.dispatch(msg)
            messages.append(msg)
        return messages

    @property
    def pending(self) -> int:
        return self._queue.qsize()

    @property
    def stats(self) -> dict[str, int]:
        return {
            "total_published": self._message_counter,
            "delivered": self._delivered,
            "expired": self._expired,
            "pending": self.pending,
        }


# ---------------------------------------------------------------------------
# DeadlockDetector — cycle detection in resource-wait graph
# ---------------------------------------------------------------------------

class DeadlockDetector:
    """Detects deadlocks by maintaining a wait-for graph (WFG) and checking
    for cycles using networkx.

    A deadlock exists when component A holds resource X and waits for resource
    Y which is held by component B, which waits for X — forming a cycle.
    """

    def __init__(self) -> None:
        self._holds: dict[str, str] = {}  # resource_id -> holder component_id
        self._waits: dict[str, str] = {}  # component_id -> resource_id it waits for
        self._lock_info: dict[str, LockInfo] = {}
        self._deadlocks_detected: int = 0

    def acquire(self, component_id: str, resource_id: str, timeout_sec: float = 30.0) -> bool:
        """Attempt to acquire a resource. Returns True if acquired, False if already held."""
        if resource_id in self._holds:
            if self._holds[resource_id] == component_id:
                return True  # already owns it
            # Resource is held by another component — register wait
            self._waits[component_id] = resource_id
            return False

        self._holds[resource_id] = component_id
        self._lock_info[resource_id] = LockInfo(
            resource_id=resource_id, holder=component_id, timeout_sec=timeout_sec,
        )
        # Clear any wait
        self._waits.pop(component_id, None)
        return True

    def release(self, component_id: str, resource_id: str) -> bool:
        """Release a previously acquired resource."""
        if self._holds.get(resource_id) == component_id:
            del self._holds[resource_id]
            self._lock_info.pop(resource_id, None)
            return True
        return False

    def _build_wait_graph(self) -> nx.DiGraph:
        """Build the wait-for graph from current holds and waits."""
        g = nx.DiGraph()
        for waiting_comp, wanted_res in self._waits.items():
            holder = self._holds.get(wanted_res)
            if holder and holder != waiting_comp:
                g.add_edge(waiting_comp, holder, resource=wanted_res)
        return g

    def detect(self) -> list[list[str]]:
        """Find all deadlock cycles in the current wait-for graph.

        Returns a list of cycles, where each cycle is a list of component IDs.
        """
        g = self._build_wait_graph()
        cycles = list(nx.simple_cycles(g))
        if cycles:
            self._deadlocks_detected += len(cycles)
            logger.warning("Deadlocks detected: %d cycles", len(cycles))
        return cycles

    async def detect_and_resolve(self, victim_strategy: str = "youngest") -> list[dict[str, Any]]:
        """Detect deadlocks and resolve by releasing the victim's resources.

        Strategies:
        - 'youngest': release resources of the most recently waiting component.
        - 'lowest_priority': would require priority info (falls back to youngest).
        """
        cycles = self.detect()
        resolutions: list[dict[str, Any]] = []

        for cycle in cycles:
            if not cycle:
                continue

            # Pick victim
            if victim_strategy == "youngest":
                # The last component to start waiting is the youngest
                victim = cycle[-1]
            else:
                victim = cycle[-1]

            # Release all resources held by victim
            released = []
            for res, holder in list(self._holds.items()):
                if holder == victim:
                    self.release(victim, res)
                    released.append(res)

            # Clear victim's wait
            self._waits.pop(victim, None)

            resolutions.append({
                "cycle": cycle,
                "victim": victim,
                "released_resources": released,
                "strategy": victim_strategy,
            })

        return resolutions

    async def check_timeouts(self) -> list[LockInfo]:
        """Find locks that have exceeded their timeout."""
        now = time.time()
        expired = []
        for li in list(self._lock_info.values()):
            if now - li.acquired_at > li.timeout_sec:
                expired.append(li)
        return expired

    @property
    def deadlocks_detected(self) -> int:
        return self._deadlocks_detected


# ---------------------------------------------------------------------------
# ResourceMediator — fair resource allocation with back-pressure
# ---------------------------------------------------------------------------

class ResourceMediator:
    """Mediates contention for shared resources using token-bucket rate limiting
    and fair allocation policies.

    Each resource has a capacity and a refill rate. Components request tokens
    to access the resource; if the bucket is empty, they must wait.
    """

    def __init__(self) -> None:
        self._buckets: dict[str, dict[str, float]] = {}
        # resource_id -> {capacity, tokens, refill_rate, last_refill}
        self._request_log: list[dict[str, Any]] = []

    def register_resource(
        self,
        resource_id: str,
        capacity: float = 10.0,
        refill_rate: float = 1.0,
    ) -> None:
        """Register a resource with a token bucket."""
        self._buckets[resource_id] = {
            "capacity": capacity,
            "tokens": capacity,
            "refill_rate": refill_rate,
            "last_refill": time.time(),
        }

    def _refill(self, resource_id: str) -> None:
        """Refill tokens based on elapsed time."""
        bucket = self._buckets.get(resource_id)
        if bucket is None:
            return
        now = time.time()
        elapsed = now - bucket["last_refill"]
        bucket["tokens"] = min(bucket["capacity"], bucket["tokens"] + elapsed * bucket["refill_rate"])
        bucket["last_refill"] = now

    async def request(self, component_id: str, resource_id: str, tokens: float = 1.0) -> dict[str, Any]:
        """Request tokens from a resource's bucket.

        Returns immediately with 'granted' status or 'denied' if insufficient tokens.
        """
        bucket = self._buckets.get(resource_id)
        if bucket is None:
            return {"granted": False, "reason": "resource not registered"}

        self._refill(resource_id)

        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            self._request_log.append({
                "component": component_id, "resource": resource_id,
                "tokens": tokens, "granted": True, "timestamp": time.time(),
            })
            return {"granted": True, "remaining_tokens": round(bucket["tokens"], 2)}
        else:
            wait_time = (tokens - bucket["tokens"]) / max(bucket["refill_rate"], 1e-12)
            self._request_log.append({
                "component": component_id, "resource": resource_id,
                "tokens": tokens, "granted": False, "timestamp": time.time(),
            })
            return {
                "granted": False,
                "remaining_tokens": round(bucket["tokens"], 2),
                "estimated_wait_sec": round(wait_time, 2),
                "reason": "insufficient tokens",
            }

    async def request_with_wait(
        self,
        component_id: str,
        resource_id: str,
        tokens: float = 1.0,
        max_wait: float = 10.0,
    ) -> dict[str, Any]:
        """Request tokens, waiting up to *max_wait* seconds if needed."""
        deadline = time.time() + max_wait
        while time.time() < deadline:
            result = await self.request(component_id, resource_id, tokens)
            if result["granted"]:
                return result
            # Wait a short interval then retry
            await asyncio.sleep(min(0.1, deadline - time.time()))
        return {"granted": False, "reason": "timeout", "waited_sec": max_wait}

    async def utilization(self) -> dict[str, dict[str, float]]:
        """Return utilization ratio for all resources."""
        report: dict[str, dict[str, float]] = {}
        for rid, bucket in self._buckets.items():
            self._refill(rid)
            used = bucket["capacity"] - bucket["tokens"]
            report[rid] = {
                "capacity": bucket["capacity"],
                "available": round(bucket["tokens"], 2),
                "utilization_pct": round((used / max(bucket["capacity"], 1e-12)) * 100, 1),
            }
        return report


# ---------------------------------------------------------------------------
# HealthMonitor — component heartbeat and health tracking
# ---------------------------------------------------------------------------

class HealthMonitor:
    """Tracks health of registered components via heartbeats and failure counts.

    Components that miss heartbeats are progressively marked degraded → unhealthy → offline.
    """

    def __init__(
        self,
        heartbeat_interval: float = 10.0,
        degraded_threshold: int = 2,
        unhealthy_threshold: int = 5,
    ) -> None:
        self._components: dict[str, ComponentHealth] = {}
        self._heartbeat_interval = heartbeat_interval
        self._degraded_threshold = degraded_threshold
        self._unhealthy_threshold = unhealthy_threshold
        self._status_change_log: list[dict[str, Any]] = []

    def register(self, component_id: str, metadata: dict[str, Any] | None = None) -> ComponentHealth:
        """Register a component for health monitoring."""
        health = ComponentHealth(
            component_id=component_id,
            metadata=metadata or {},
        )
        self._components[component_id] = health
        return health

    async def heartbeat(self, component_id: str) -> ComponentHealth | None:
        """Record a heartbeat from a component, resetting its failure count."""
        health = self._components.get(component_id)
        if health is None:
            return None
        now = time.time()
        health.last_heartbeat = now
        health.uptime_sec = now - (health.metadata.get("registered_at", now))

        if health.status != ComponentStatus.HEALTHY:
            old_status = health.status
            health.status = ComponentStatus.HEALTHY
            health.consecutive_failures = 0
            self._status_change_log.append({
                "component": component_id, "from": old_status.name,
                "to": "HEALTHY", "timestamp": now,
            })
        else:
            health.consecutive_failures = 0

        return health

    async def report_failure(self, component_id: str) -> ComponentHealth | None:
        """Record a failure for a component."""
        health = self._components.get(component_id)
        if health is None:
            return None
        health.consecutive_failures += 1
        old_status = health.status

        if health.consecutive_failures >= self._unhealthy_threshold:
            health.status = ComponentStatus.UNHEALTHY
        elif health.consecutive_failures >= self._degraded_threshold:
            health.status = ComponentStatus.DEGRADED

        if health.status != old_status:
            self._status_change_log.append({
                "component": component_id, "from": old_status.name,
                "to": health.status.name, "timestamp": time.time(),
                "failures": health.consecutive_failures,
            })

        return health

    async def check_heartbeats(self) -> list[str]:
        """Identify components with stale heartbeats."""
        now = time.time()
        stale: list[str] = []
        for cid, health in self._components.items():
            age = now - health.last_heartbeat
            if age > self._heartbeat_interval * 3:
                if health.status != ComponentStatus.OFFLINE:
                    old = health.status
                    health.status = ComponentStatus.OFFLINE
                    self._status_change_log.append({
                        "component": cid, "from": old.name,
                        "to": "OFFLINE", "timestamp": now,
                    })
                stale.append(cid)
            elif age > self._heartbeat_interval * 2:
                if health.status.value < ComponentStatus.UNHEALTHY.value:
                    health.status = ComponentStatus.UNHEALTHY
            elif age > self._heartbeat_interval:
                if health.status.value < ComponentStatus.DEGRADED.value:
                    health.status = ComponentStatus.DEGRADED
        return stale

    async def overall_health(self) -> dict[str, Any]:
        """Aggregate health status."""
        if not self._components:
            return {"status": "no_components", "total": 0}
        statuses = [h.status for h in self._components.values()]
        healthy = sum(1 for s in statuses if s == ComponentStatus.HEALTHY)
        degraded = sum(1 for s in statuses if s == ComponentStatus.DEGRADED)
        unhealthy = sum(1 for s in statuses if s == ComponentStatus.UNHEALTHY)
        offline = sum(1 for s in statuses if s == ComponentStatus.OFFLINE)

        if offline > 0 or unhealthy > len(statuses) * 0.5:
            overall = "critical"
        elif unhealthy > 0 or degraded > len(statuses) * 0.3:
            overall = "degraded"
        else:
            overall = "healthy"

        return {
            "status": overall,
            "total": len(statuses),
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "offline": offline,
        }

    @property
    def components(self) -> dict[str, ComponentHealth]:
        return dict(self._components)


# ---------------------------------------------------------------------------
# GracefulDegrader — load-shedding and fallback management
# ---------------------------------------------------------------------------

class GracefulDegrader:
    """Manages graceful degradation when the system is under stress.

    Maintains a priority-ordered list of features that can be shed under load.
    When degradation is triggered, lower-priority features are disabled first.
    """

    def __init__(self) -> None:
        self._features: dict[str, dict[str, Any]] = {}
        # feature_id -> {priority, enabled, fallback_fn, description}
        self._degradation_level: int = 0  # 0 = full, higher = more shed
        self._history: list[dict[str, Any]] = []

    def register_feature(
        self,
        feature_id: str,
        priority: int = 5,
        description: str = "",
        fallback_fn: Callable[[], Awaitable[Any]] | None = None,
    ) -> None:
        """Register a feature that can be gracefully degraded.

        Priority 1 = most critical (shed last), 10 = least critical (shed first).
        """
        self._features[feature_id] = {
            "priority": max(1, min(10, priority)),
            "enabled": True,
            "fallback_fn": fallback_fn,
            "description": description,
        }

    async def degrade(self, level: int) -> dict[str, Any]:
        """Set degradation level: shed features with priority >= level.

        Level 0 = everything enabled. Level 10 = only priority-1 features remain.
        """
        level = max(0, min(10, level))
        old_level = self._degradation_level
        self._degradation_level = level

        shed: list[str] = []
        kept: list[str] = []

        for fid, info in self._features.items():
            if info["priority"] >= level and level > 0:
                if info["enabled"]:
                    info["enabled"] = False
                    shed.append(fid)
                    # Invoke fallback if registered
                    if info["fallback_fn"]:
                        try:
                            await info["fallback_fn"]()
                        except Exception as exc:
                            logger.error("Fallback error for %s: %s", fid, exc)
            else:
                if not info["enabled"]:
                    info["enabled"] = True
                kept.append(fid)

        entry = {
            "old_level": old_level,
            "new_level": level,
            "features_shed": shed,
            "features_kept": kept,
            "timestamp": time.time(),
        }
        self._history.append(entry)
        logger.info("Degradation level %d → %d: shed %d features", old_level, level, len(shed))
        return entry

    async def restore(self) -> dict[str, Any]:
        """Restore all features to enabled."""
        return await self.degrade(0)

    def is_enabled(self, feature_id: str) -> bool:
        """Check if a feature is currently enabled."""
        info = self._features.get(feature_id)
        return info["enabled"] if info else False

    async def status(self) -> dict[str, Any]:
        """Return degradation status."""
        enabled = sum(1 for f in self._features.values() if f["enabled"])
        return {
            "degradation_level": self._degradation_level,
            "total_features": len(self._features),
            "enabled": enabled,
            "disabled": len(self._features) - enabled,
            "features": {
                fid: {"enabled": f["enabled"], "priority": f["priority"]}
                for fid, f in self._features.items()
            },
        }


# ---------------------------------------------------------------------------
# AegisWiring — top-level conflict-free wiring orchestrator
# ---------------------------------------------------------------------------

class AegisWiring:
    """Orchestrates all conflict-free wiring subsystems: message bus, deadlock
    detection, resource mediation, health monitoring, and graceful degradation.

    Usage::

        wiring = AegisWiring()
        wiring.health.register("engine_a")
        await wiring.bus.publish("engine_a", "engine_b", {"cmd": "sync"})
        report = await wiring.system_report()
    """

    def __init__(self, max_queue_size: int = 10_000) -> None:
        self.bus = MessageBus(max_queue_size=max_queue_size)
        self.deadlock = DeadlockDetector()
        self.resources = ResourceMediator()
        self.health = HealthMonitor()
        self.degrader = GracefulDegrader()

    async def system_report(self) -> dict[str, Any]:
        """Comprehensive system-wide health and status report."""
        health = await self.health.overall_health()
        degradation = await self.degrader.status()
        utilization = await self.resources.utilization()

        # Check for deadlocks
        deadlock_cycles = self.deadlock.detect()

        return {
            "timestamp": time.time(),
            "message_bus": self.bus.stats,
            "health": health,
            "degradation": degradation,
            "resource_utilization": utilization,
            "deadlocks": {
                "current_cycles": len(deadlock_cycles),
                "total_detected": self.deadlock.deadlocks_detected,
                "cycles": deadlock_cycles,
            },
        }

    async def auto_heal(self) -> dict[str, Any]:
        """Automated healing pass: resolve deadlocks, check heartbeats, adjust degradation.

        1. Detect and resolve deadlocks.
        2. Check heartbeats for stale components.
        3. Adjust degradation level based on overall health.
        """
        actions: list[str] = []

        # 1. Deadlocks
        resolutions = await self.deadlock.detect_and_resolve()
        if resolutions:
            actions.append(f"Resolved {len(resolutions)} deadlock(s)")

        # 2. Heartbeats
        stale = await self.health.check_heartbeats()
        if stale:
            actions.append(f"Found {len(stale)} stale component(s): {stale}")

        # 3. Adaptive degradation
        health = await self.health.overall_health()
        if health["status"] == "critical":
            await self.degrader.degrade(7)
            actions.append("Escalated degradation to level 7")
        elif health["status"] == "degraded":
            if self.degrader._degradation_level < 4:
                await self.degrader.degrade(4)
                actions.append("Set degradation to level 4")
        elif health["status"] == "healthy":
            if self.degrader._degradation_level > 0:
                await self.degrader.restore()
                actions.append("Restored all features")

        # 4. Expired lock cleanup
        expired_locks = await self.deadlock.check_timeouts()
        for lock in expired_locks:
            self.deadlock.release(lock.holder, lock.resource_id)
            actions.append(f"Released expired lock {lock.resource_id} from {lock.holder}")

        return {
            "actions_taken": len(actions),
            "details": actions,
            "timestamp": time.time(),
        }
