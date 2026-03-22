"""
UnifiedCognitiveBus — The Master Wire of PRADYSAGICAN
=====================================================
Solves the #1 weakness: modules are islands. This bus connects:
- Core engines (consciousness, reasoning, memory, world_model)
- Prometheus, Atlas, Aegis
- All agents (stark_core, orchestrator, strategist, ethics, learner, inventor)
- All capabilities (empathy, intuition, curiosity, etc.)
- Safety (dual_mode, guardrails)
- Tools (nexus, registry, automation)

No module should ever call another module directly. Everything goes through the bus.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

import numpy as np

logger = logging.getLogger(__name__)


# ── Signal Types ─────────────────────────────────────────────────────────────

class SignalType(str, Enum):
    """All possible signal types on the cognitive bus."""
    PERCEPTION = "perception"
    REASONING = "reasoning"
    MEMORY_STORE = "memory_store"
    MEMORY_RECALL = "memory_recall"
    EMOTION = "emotion"
    DECISION = "decision"
    ACTION = "action"
    SAFETY_CHECK = "safety_check"
    TOOL_USE = "tool_use"
    INTROSPECTION = "introspection"
    LEARNING = "learning"
    INVENTION = "invention"
    CRISIS = "crisis"
    BROADCAST = "broadcast"


# ── Cognitive Signal ─────────────────────────────────────────────────────────

@dataclass
class CognitiveSignal:
    """A typed message on the cognitive bus.

    Every inter-module communication is a CognitiveSignal. Signals carry
    a typed payload with priority, TTL, and optional request-response
    correlation for synchronous exchanges.
    """
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    signal_type: SignalType = SignalType.BROADCAST
    source: str = ""
    target: str = "*"  # "*" = broadcast to all
    payload: dict[str, Any] = field(default_factory=dict)
    priority: int = 5  # 0 (highest) to 9 (lowest)
    timestamp: float = field(default_factory=time.time)
    requires_response: bool = False
    correlation_id: str | None = None
    ttl_seconds: float = 30.0

    @property
    def is_broadcast(self) -> bool:
        return self.target == "*"

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl_seconds


# ── Signal Result ────────────────────────────────────────────────────────────

@dataclass
class SignalResult:
    """Response from a module after processing a signal."""
    signal_id: str
    module_name: str
    success: bool
    payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


# ── Module Info ──────────────────────────────────────────────────────────────

@dataclass
class ModuleInfo:
    """Metadata about a registered module."""
    name: str
    handler: Callable[[CognitiveSignal], Awaitable[SignalResult]]
    capabilities: list[SignalType] = field(default_factory=list)
    registered_at: float = field(default_factory=time.time)
    signals_processed: int = 0
    signals_failed: int = 0
    total_latency_ms: float = 0.0
    last_active: float | None = None
    enabled: bool = True

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.signals_processed, 1)

    @property
    def error_rate(self) -> float:
        total = self.signals_processed + self.signals_failed
        return self.signals_failed / total if total > 0 else 0.0


# ── Module Registry ──────────────────────────────────────────────────────────

class ModuleRegistry:
    """Tracks all registered modules on the cognitive bus.

    Each module declares which SignalTypes it can handle. The registry
    provides capability-based routing: when a signal is sent, only
    modules that declared the matching capability will receive it.
    """

    def __init__(self) -> None:
        self._modules: dict[str, ModuleInfo] = {}

    def register(
        self,
        name: str,
        handler: Callable[[CognitiveSignal], Awaitable[SignalResult]],
        capabilities: list[SignalType] | None = None,
    ) -> ModuleInfo:
        """Register a module with its handler and capabilities."""
        info = ModuleInfo(
            name=name,
            handler=handler,
            capabilities=capabilities or list(SignalType),
        )
        self._modules[name] = info
        logger.info("Module registered: %s (capabilities: %d)", name, len(info.capabilities))
        return info

    def unregister(self, name: str) -> bool:
        """Remove a module from the registry."""
        if name in self._modules:
            del self._modules[name]
            logger.info("Module unregistered: %s", name)
            return True
        return False

    def is_registered(self, name: str) -> bool:
        return name in self._modules

    def get(self, name: str) -> ModuleInfo | None:
        return self._modules.get(name)

    def list_modules(self) -> list[str]:
        """Return all registered module names."""
        return list(self._modules.keys())

    def get_capabilities(self, name: str) -> list[SignalType]:
        """Return what signal types a module can handle."""
        info = self._modules.get(name)
        return list(info.capabilities) if info else []

    def find_by_capability(self, signal_type: SignalType) -> list[ModuleInfo]:
        """Find all modules that can handle a given signal type."""
        return [
            m for m in self._modules.values()
            if m.enabled and signal_type in m.capabilities
        ]

    def all_modules(self) -> list[ModuleInfo]:
        return list(self._modules.values())

    @property
    def count(self) -> int:
        return len(self._modules)


# ── Cognitive Pipeline ───────────────────────────────────────────────────────

class CognitivePipeline:
    """Chain modules into named processing pipelines.

    A pipeline defines a sequence of modules. When executed, the initial
    signal is passed to the first module; its output payload becomes
    the input for the next module, and so on. Each step can transform,
    enrich, or filter the payload.

    Built-in pipelines cover the most common cognitive flows:
    - perceive_and_respond: perception → reasoning → memory → ethics → action
    - deep_think: extended deliberation with strategic planning
    - crisis_response: fast-path for emergencies
    - learn_and_evolve: experience → memory → self-improvement
    - create_and_invent: creativity → invention → safety check
    """

    def __init__(self, registry: ModuleRegistry) -> None:
        self._registry = registry
        self._pipelines: dict[str, list[str]] = {}
        self._execution_log: list[dict[str, Any]] = []
        self._install_defaults()

    def _install_defaults(self) -> None:
        """Install the five built-in pipelines."""
        self._pipelines["perceive_and_respond"] = [
            "consciousness", "reasoning", "memory", "ethics", "action",
        ]
        self._pipelines["deep_think"] = [
            "consciousness", "reasoning", "world_model", "strategist",
            "reasoning", "ethics",
        ]
        self._pipelines["crisis_response"] = [
            "consciousness", "ethics", "guardian", "orchestrator",
        ]
        self._pipelines["learn_and_evolve"] = [
            "learner", "memory", "prometheus", "consciousness",
        ]
        self._pipelines["create_and_invent"] = [
            "curiosity", "imagination", "inventor", "ethics", "memory",
        ]

    def create_pipeline(self, name: str, steps: list[str]) -> None:
        """Define or overwrite a named pipeline."""
        self._pipelines[name] = list(steps)
        logger.info("Pipeline '%s' created with %d steps: %s", name, len(steps), " → ".join(steps))

    def get_pipeline(self, name: str) -> list[str] | None:
        return self._pipelines.get(name)

    def list_pipelines(self) -> dict[str, list[str]]:
        return dict(self._pipelines)

    async def execute_pipeline(
        self,
        name: str,
        initial_signal: CognitiveSignal,
    ) -> list[SignalResult]:
        """Execute a signal through every step of a named pipeline.

        Each module in the pipeline receives the signal with payload
        updated by the previous module's output. If a module is not
        registered, the step is skipped with a warning. If a module
        fails, execution continues (degraded mode) unless the signal
        is a CRISIS type, which aborts on first failure.
        """
        steps = self._pipelines.get(name)
        if not steps:
            return [SignalResult(
                signal_id=initial_signal.id,
                module_name="pipeline",
                success=False,
                error=f"Pipeline '{name}' not found",
            )]

        results: list[SignalResult] = []
        current_payload = dict(initial_signal.payload)
        pipeline_start = time.monotonic()

        for step_name in steps:
            module = self._registry.get(step_name)
            if module is None or not module.enabled:
                logger.debug("Pipeline '%s': skipping unregistered/disabled module '%s'", name, step_name)
                results.append(SignalResult(
                    signal_id=initial_signal.id,
                    module_name=step_name,
                    success=False,
                    error=f"Module '{step_name}' not registered or disabled",
                ))
                continue

            # Build signal for this step
            step_signal = CognitiveSignal(
                id=initial_signal.id,
                signal_type=initial_signal.signal_type,
                source=initial_signal.source,
                target=step_name,
                payload=current_payload,
                priority=initial_signal.priority,
                correlation_id=initial_signal.correlation_id,
                ttl_seconds=initial_signal.ttl_seconds,
            )

            start = time.monotonic()
            try:
                result = await module.handler(step_signal)
                latency = (time.monotonic() - start) * 1000
                result.latency_ms = round(latency, 3)
                module.signals_processed += 1
                module.total_latency_ms += latency
                module.last_active = time.time()

                # Merge result payload into the flow
                if result.success and result.payload:
                    current_payload.update(result.payload)

                results.append(result)

            except Exception as exc:
                latency = (time.monotonic() - start) * 1000
                module.signals_failed += 1
                error_result = SignalResult(
                    signal_id=initial_signal.id,
                    module_name=step_name,
                    success=False,
                    error=str(exc),
                    latency_ms=round(latency, 3),
                )
                results.append(error_result)

                # Abort pipeline on crisis failure
                if initial_signal.signal_type == SignalType.CRISIS:
                    logger.error("Pipeline '%s' aborted at '%s': %s", name, step_name, exc)
                    break

        total_ms = round((time.monotonic() - pipeline_start) * 1000, 3)
        self._execution_log.append({
            "pipeline": name,
            "steps": len(steps),
            "completed": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "total_ms": total_ms,
            "timestamp": time.time(),
        })

        return results

    @property
    def execution_log(self) -> list[dict[str, Any]]:
        return list(self._execution_log)


# ── Unified Cognitive Bus ────────────────────────────────────────────────────

class UnifiedCognitiveBus:
    """The Master Wire — connects ALL 30+ PRADYSAGICAN modules.

    Architecture:
    - Every module registers with a handler function and declared capabilities.
    - Modules never call each other directly; all communication is via
      typed CognitiveSignal messages routed through the bus.
    - Each module has an isolated asyncio.Queue for backpressure.
    - Named pipelines chain modules into cognitive processing flows.
    - Built-in metrics track signal throughput, latency, and error rates.
    - Health checks verify module responsiveness.

    This solves weaknesses W1 (modules are islands) and W10 (modules can't
    compose dynamically) from the competitive analysis.
    """

    def __init__(self, queue_maxsize: int = 1000) -> None:
        self.registry = ModuleRegistry()
        self.pipeline = CognitivePipeline(self.registry)
        self._queues: dict[str, asyncio.Queue[CognitiveSignal]] = {}
        self._queue_maxsize = queue_maxsize
        self._pending_responses: dict[str, asyncio.Event] = {}
        self._response_store: dict[str, SignalResult] = {}
        self._signal_log: list[dict[str, Any]] = []
        self._total_sent: int = 0
        self._total_delivered: int = 0
        self._total_errors: int = 0

    # ── Module Management ────────────────────────────────────────────────

    def register_module(
        self,
        name: str,
        handler: Callable[[CognitiveSignal], Awaitable[SignalResult]],
        capabilities: list[SignalType] | None = None,
    ) -> ModuleInfo:
        """Register a module on the bus with an isolated message queue."""
        info = self.registry.register(name, handler, capabilities)
        self._queues[name] = asyncio.Queue(maxsize=self._queue_maxsize)
        logger.info("Bus: module '%s' registered with queue", name)
        return info

    def unregister_module(self, name: str) -> bool:
        """Remove a module and its queue."""
        self._queues.pop(name, None)
        return self.registry.unregister(name)

    # ── Signal Routing ───────────────────────────────────────────────────

    async def send(self, signal: CognitiveSignal) -> SignalResult:
        """Route a signal to its target module.

        If target is a specific module name, delivers directly.
        If target is "*", broadcasts to all. Returns the result
        from the target module (or first responder on broadcast).
        """
        self._total_sent += 1

        if signal.is_expired:
            return SignalResult(
                signal_id=signal.id,
                module_name=signal.target,
                success=False,
                error="Signal expired (TTL exceeded)",
            )

        if signal.is_broadcast:
            return await self._broadcast_internal(signal)

        module = self.registry.get(signal.target)
        if module is None or not module.enabled:
            self._total_errors += 1
            return SignalResult(
                signal_id=signal.id,
                module_name=signal.target,
                success=False,
                error=f"Target module '{signal.target}' not found or disabled",
            )

        return await self._deliver(signal, module)

    async def broadcast(self, signal: CognitiveSignal) -> list[SignalResult]:
        """Send a signal to ALL registered modules.

        Returns results from every module that processed the signal.
        Modules that can't handle the signal type are skipped.
        """
        signal.target = "*"
        self._total_sent += 1

        results: list[SignalResult] = []
        capable = self.registry.find_by_capability(signal.signal_type)

        for module in capable:
            targeted = CognitiveSignal(
                id=signal.id,
                signal_type=signal.signal_type,
                source=signal.source,
                target=module.name,
                payload=dict(signal.payload),
                priority=signal.priority,
                correlation_id=signal.correlation_id,
                ttl_seconds=signal.ttl_seconds,
            )
            result = await self._deliver(targeted, module)
            results.append(result)

        return results

    async def _broadcast_internal(self, signal: CognitiveSignal) -> SignalResult:
        """Internal broadcast that returns the first successful result."""
        results = await self.broadcast(signal)
        successes = [r for r in results if r.success]
        if successes:
            return successes[0]
        if results:
            return results[0]
        return SignalResult(
            signal_id=signal.id,
            module_name="*",
            success=False,
            error="No modules processed the broadcast",
        )

    async def _deliver(self, signal: CognitiveSignal, module: ModuleInfo) -> SignalResult:
        """Deliver a signal to a specific module and track metrics."""
        start = time.monotonic()
        try:
            # Enqueue for backpressure awareness
            queue = self._queues.get(module.name)
            if queue is not None:
                try:
                    queue.put_nowait(signal)
                except asyncio.QueueFull:
                    self._total_errors += 1
                    return SignalResult(
                        signal_id=signal.id,
                        module_name=module.name,
                        success=False,
                        error=f"Queue full for module '{module.name}'",
                    )

            result = await module.handler(signal)
            latency = (time.monotonic() - start) * 1000
            result.latency_ms = round(latency, 3)

            module.signals_processed += 1
            module.total_latency_ms += latency
            module.last_active = time.time()
            self._total_delivered += 1

            # Drain from queue
            if queue is not None and not queue.empty():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass

            # Store response for request-response pattern
            if signal.requires_response and signal.correlation_id:
                self._response_store[signal.correlation_id] = result
                event = self._pending_responses.get(signal.correlation_id)
                if event:
                    event.set()

            self._log_signal(signal, result)
            return result

        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            module.signals_failed += 1
            self._total_errors += 1
            error_result = SignalResult(
                signal_id=signal.id,
                module_name=module.name,
                success=False,
                error=str(exc),
                latency_ms=round(latency, 3),
            )
            self._log_signal(signal, error_result)
            return error_result

    # ── Request-Response ─────────────────────────────────────────────────

    async def request_response(
        self,
        signal: CognitiveSignal,
        timeout: float = 5.0,
    ) -> SignalResult:
        """Send a signal and wait for a response (synchronous exchange).

        Uses asyncio.Event to wait for the target module's response,
        correlated by correlation_id.
        """
        correlation_id = signal.correlation_id or uuid.uuid4().hex[:12]
        signal.correlation_id = correlation_id
        signal.requires_response = True

        event = asyncio.Event()
        self._pending_responses[correlation_id] = event

        # Send the signal
        send_result = await self.send(signal)

        # If send itself returned a result (direct delivery), return it
        if send_result.success or correlation_id in self._response_store:
            response = self._response_store.pop(correlation_id, send_result)
            self._pending_responses.pop(correlation_id, None)
            return response

        # Wait for async response
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            response = self._response_store.pop(correlation_id, send_result)
        except asyncio.TimeoutError:
            response = SignalResult(
                signal_id=signal.id,
                module_name=signal.target,
                success=False,
                error=f"Request-response timeout after {timeout}s",
            )
        finally:
            self._pending_responses.pop(correlation_id, None)

        return response

    # ── Pipeline Execution ───────────────────────────────────────────────

    async def execute_pipeline(
        self,
        pipeline_name: str,
        initial_payload: dict[str, Any],
        signal_type: SignalType = SignalType.REASONING,
        source: str = "bus",
        priority: int = 5,
    ) -> list[SignalResult]:
        """Run a full cognitive pipeline with an initial payload."""
        signal = CognitiveSignal(
            signal_type=signal_type,
            source=source,
            payload=initial_payload,
            priority=priority,
        )
        return await self.pipeline.execute_pipeline(pipeline_name, signal)

    # ── Metrics & Health ─────────────────────────────────────────────────

    def get_signal_stats(self) -> dict[str, Any]:
        """Signal throughput and latency metrics."""
        per_module: dict[str, dict[str, Any]] = {}
        for module in self.registry.all_modules():
            per_module[module.name] = {
                "processed": module.signals_processed,
                "failed": module.signals_failed,
                "avg_latency_ms": round(module.avg_latency_ms, 3),
                "error_rate": round(module.error_rate, 4),
                "last_active": module.last_active,
            }

        return {
            "total_sent": self._total_sent,
            "total_delivered": self._total_delivered,
            "total_errors": self._total_errors,
            "delivery_rate": round(
                self._total_delivered / max(self._total_sent, 1), 4
            ),
            "modules_registered": self.registry.count,
            "per_module": per_module,
            "pipelines_available": list(self.pipeline.list_pipelines().keys()),
            "pipeline_executions": len(self.pipeline.execution_log),
        }

    async def health_check(self) -> dict[str, Any]:
        """Verify all modules are responsive by sending a lightweight probe.

        Sends a BROADCAST-type ping to each module and checks response time.
        """
        results: dict[str, dict[str, Any]] = {}
        all_healthy = True

        for module in self.registry.all_modules():
            if not module.enabled:
                results[module.name] = {"status": "disabled"}
                continue

            probe = CognitiveSignal(
                signal_type=SignalType.INTROSPECTION,
                source="health_check",
                target=module.name,
                payload={"probe": True},
                priority=0,
                ttl_seconds=5.0,
            )

            start = time.monotonic()
            try:
                result = await asyncio.wait_for(
                    module.handler(probe),
                    timeout=3.0,
                )
                latency = (time.monotonic() - start) * 1000
                results[module.name] = {
                    "status": "healthy" if result.success else "degraded",
                    "latency_ms": round(latency, 3),
                    "error_rate": round(module.error_rate, 4),
                }
                if not result.success:
                    all_healthy = False
            except (asyncio.TimeoutError, Exception) as exc:
                latency = (time.monotonic() - start) * 1000
                results[module.name] = {
                    "status": "unhealthy",
                    "latency_ms": round(latency, 3),
                    "error": str(exc),
                }
                all_healthy = False

        return {
            "overall": "healthy" if all_healthy else "degraded",
            "modules": results,
            "timestamp": time.time(),
        }

    # ── Internal Logging ─────────────────────────────────────────────────

    def _log_signal(self, signal: CognitiveSignal, result: SignalResult) -> None:
        """Record signal for audit trail (bounded buffer)."""
        self._signal_log.append({
            "signal_id": signal.id,
            "type": signal.signal_type.value,
            "source": signal.source,
            "target": signal.target,
            "priority": signal.priority,
            "success": result.success,
            "latency_ms": result.latency_ms,
            "timestamp": time.time(),
        })
        # Keep bounded
        if len(self._signal_log) > 10000:
            self._signal_log = self._signal_log[-5000:]

    @property
    def signal_log(self) -> list[dict[str, Any]]:
        return list(self._signal_log)
