"""
Atlas — Hardware-Adaptive Runtime — PRADYSAGICAN
Detects hardware capabilities at startup and dynamically adapts scheduling,
memory allocation, and model optimization to available resources.

Uses os/platform/subprocess for hardware detection with graceful fallbacks.
"""
from __future__ import annotations

import asyncio
import logging
import math
import os
import platform
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class DeviceType(str, Enum):
    CPU = "cpu"
    GPU = "gpu"
    TPU = "tpu"
    UNKNOWN = "unknown"


class SchedulePolicy(str, Enum):
    FIFO = "fifo"
    PRIORITY = "priority"
    FAIR_SHARE = "fair_share"
    THERMAL_AWARE = "thermal_aware"


@dataclass
class HardwareProfile:
    """Snapshot of detected hardware capabilities."""
    cpu_count: int = 1
    cpu_freq_mhz: float = 0.0
    cpu_arch: str = "unknown"
    total_memory_mb: float = 0.0
    available_memory_mb: float = 0.0
    os_name: str = "unknown"
    os_version: str = ""
    python_version: str = ""
    gpu_available: bool = False
    gpu_name: str = ""
    gpu_memory_mb: float = 0.0
    device_type: DeviceType = DeviceType.CPU
    hostname: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class ResourceSnapshot:
    """Point-in-time resource utilisation measurement."""
    cpu_percent: float = 0.0  # 0-100
    memory_used_mb: float = 0.0
    memory_percent: float = 0.0  # 0-100
    io_wait_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class TaskSlot:
    """A scheduled task with resource requirements."""
    task_id: str
    name: str
    priority: int = 5  # 1 (highest) to 10 (lowest)
    cpu_weight: float = 1.0  # relative CPU share
    memory_mb: float = 0.0  # estimated memory requirement
    submitted_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    status: str = "pending"  # pending, running, completed, failed


# ---------------------------------------------------------------------------
# Hardware detection helpers
# ---------------------------------------------------------------------------

def _safe_shell(cmd: list[str], default: str = "") -> str:
    """Run a shell command and return stdout, or *default* on failure."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else default
    except Exception:
        return default


def _detect_cpu_freq() -> float:
    """Attempt to read CPU frequency in MHz."""
    # Linux: /proc/cpuinfo
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("cpu MHz"):
                    return float(line.split(":")[1].strip())
    except Exception:
        pass
    # macOS
    raw = _safe_shell(["sysctl", "-n", "hw.cpufrequency"])
    if raw:
        try:
            return float(raw) / 1e6
        except ValueError:
            pass
    return 0.0


def _detect_memory_mb() -> tuple[float, float]:
    """Return (total_mb, available_mb)."""
    # Linux: /proc/meminfo
    try:
        info: dict[str, float] = {}
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    val = float(parts[1])  # kB
                    info[key] = val
        total = info.get("MemTotal", 0) / 1024
        avail = info.get("MemAvailable", info.get("MemFree", 0)) / 1024
        return total, avail
    except Exception:
        pass
    # macOS fallback
    raw = _safe_shell(["sysctl", "-n", "hw.memsize"])
    if raw:
        try:
            total = float(raw) / (1024 * 1024)
            return total, total * 0.5  # rough estimate
        except ValueError:
            pass
    return 0.0, 0.0


def _detect_gpu() -> tuple[bool, str, float]:
    """Attempt to detect GPU via nvidia-smi."""
    raw = _safe_shell(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    if raw:
        parts = raw.split(",")
        name = parts[0].strip() if parts else "GPU"
        mem = float(parts[1].strip()) if len(parts) > 1 else 0.0
        return True, name, mem
    return False, "", 0.0


# ---------------------------------------------------------------------------
# ResourceMonitor — continuous resource tracking
# ---------------------------------------------------------------------------

class ResourceMonitor:
    """Tracks system resource utilisation over time.

    Reads /proc/stat and /proc/meminfo on Linux; falls back to safe estimates
    on other platforms. Maintains a sliding window of snapshots for analysis.
    """

    def __init__(self, window_size: int = 120) -> None:
        self._history: list[ResourceSnapshot] = []
        self._window_size = window_size
        self._prev_cpu_times: tuple[float, float] | None = None  # (idle, total)

    def _read_cpu_percent(self) -> float:
        """Read aggregate CPU usage from /proc/stat (Linux only)."""
        try:
            with open("/proc/stat") as f:
                line = f.readline()
            parts = line.split()
            if parts[0] != "cpu":
                return 0.0
            times = [float(x) for x in parts[1:]]
            idle = times[3] if len(times) > 3 else 0.0
            total = sum(times)

            if self._prev_cpu_times is None:
                self._prev_cpu_times = (idle, total)
                return 0.0

            prev_idle, prev_total = self._prev_cpu_times
            self._prev_cpu_times = (idle, total)
            d_idle = idle - prev_idle
            d_total = total - prev_total
            if d_total == 0:
                return 0.0
            return max(0.0, min(100.0, (1.0 - d_idle / d_total) * 100))
        except Exception:
            return 0.0

    async def snapshot(self) -> ResourceSnapshot:
        """Take a point-in-time resource measurement."""
        cpu_pct = self._read_cpu_percent()
        total_mb, avail_mb = _detect_memory_mb()
        used_mb = total_mb - avail_mb
        mem_pct = (used_mb / max(total_mb, 1)) * 100

        snap = ResourceSnapshot(
            cpu_percent=round(cpu_pct, 1),
            memory_used_mb=round(used_mb, 1),
            memory_percent=round(mem_pct, 1),
        )
        self._history.append(snap)

        # Trim to window
        if len(self._history) > self._window_size:
            self._history = self._history[-self._window_size:]

        return snap

    async def stats(self, last_n: int = 30) -> dict[str, Any]:
        """Aggregate statistics over recent snapshots."""
        recent = self._history[-last_n:]
        if not recent:
            return {"error": "no data"}
        cpu_vals = [s.cpu_percent for s in recent]
        mem_vals = [s.memory_percent for s in recent]
        return {
            "cpu_avg": round(float(np.mean(cpu_vals)), 1),
            "cpu_max": round(max(cpu_vals), 1),
            "cpu_std": round(float(np.std(cpu_vals)), 1),
            "mem_avg": round(float(np.mean(mem_vals)), 1),
            "mem_max": round(max(mem_vals), 1),
            "points": len(recent),
        }

    async def is_overloaded(self, cpu_threshold: float = 90.0, mem_threshold: float = 90.0) -> bool:
        """Return True if recent resource usage exceeds thresholds."""
        if len(self._history) < 3:
            return False
        recent = self._history[-5:]
        avg_cpu = float(np.mean([s.cpu_percent for s in recent]))
        avg_mem = float(np.mean([s.memory_percent for s in recent]))
        return avg_cpu > cpu_threshold or avg_mem > mem_threshold

    @property
    def history(self) -> list[ResourceSnapshot]:
        return list(self._history)


# ---------------------------------------------------------------------------
# AdaptiveScheduler — priority + thermal-aware task scheduling
# ---------------------------------------------------------------------------

class AdaptiveScheduler:
    """Schedules tasks based on priority, resource availability, and thermal state.

    Supports FIFO, priority, fair-share, and thermal-aware scheduling policies.
    """

    def __init__(
        self,
        max_concurrent: int = 0,
        policy: SchedulePolicy = SchedulePolicy.PRIORITY,
    ) -> None:
        if max_concurrent <= 0:
            max_concurrent = max(os.cpu_count() or 2, 2)
        self._max_concurrent = max_concurrent
        self._policy = policy
        self._queue: list[TaskSlot] = []
        self._running: list[TaskSlot] = []
        self._completed: list[TaskSlot] = []
        self._task_counter: int = 0

    async def submit(self, name: str, priority: int = 5, cpu_weight: float = 1.0, memory_mb: float = 0.0) -> TaskSlot:
        """Submit a task for scheduling."""
        self._task_counter += 1
        slot = TaskSlot(
            task_id=f"task_{self._task_counter}_{int(time.time())}",
            name=name,
            priority=max(1, min(10, priority)),
            cpu_weight=cpu_weight,
            memory_mb=memory_mb,
        )
        self._queue.append(slot)
        logger.debug("Submitted task %s (priority=%d)", name, priority)
        return slot

    async def schedule_next(self, monitor: ResourceMonitor | None = None) -> TaskSlot | None:
        """Pick the next task to run based on current policy.

        Respects max_concurrent limit and optionally checks resource monitor
        to throttle under high load.
        """
        if len(self._running) >= self._max_concurrent:
            return None
        if not self._queue:
            return None

        # Throttle if overloaded
        if monitor is not None and await monitor.is_overloaded():
            logger.warning("System overloaded — deferring scheduling")
            return None

        # Sort queue by policy
        if self._policy == SchedulePolicy.PRIORITY:
            self._queue.sort(key=lambda t: t.priority)
        elif self._policy == SchedulePolicy.FAIR_SHARE:
            # Weighted lottery: lower priority number = more tickets
            weights = [11 - t.priority for t in self._queue]
            total_w = sum(weights)
            probs = [w / max(total_w, 1e-12) for w in weights]
            idx = int(np.random.choice(len(self._queue), p=probs))
            # Move chosen to front
            chosen = self._queue.pop(idx)
            self._queue.insert(0, chosen)
        elif self._policy == SchedulePolicy.THERMAL_AWARE:
            # Prefer lighter tasks when system is warm
            if monitor and len(monitor.history) > 0:
                last_cpu = monitor.history[-1].cpu_percent
                if last_cpu > 70:
                    self._queue.sort(key=lambda t: t.cpu_weight)
                else:
                    self._queue.sort(key=lambda t: t.priority)
            else:
                self._queue.sort(key=lambda t: t.priority)
        # FIFO: already in submission order

        task = self._queue.pop(0)
        task.status = "running"
        task.started_at = time.time()
        self._running.append(task)
        return task

    async def complete_task(self, task_id: str, success: bool = True) -> TaskSlot | None:
        """Mark a running task as completed."""
        for i, t in enumerate(self._running):
            if t.task_id == task_id:
                t.status = "completed" if success else "failed"
                t.completed_at = time.time()
                self._completed.append(t)
                self._running.pop(i)
                return t
        return None

    async def drain(self) -> list[TaskSlot]:
        """Schedule and complete all queued tasks (for testing)."""
        completed: list[TaskSlot] = []
        while self._queue:
            task = await self.schedule_next()
            if task is None:
                # Force-complete a running task to free a slot
                if self._running:
                    await self.complete_task(self._running[0].task_id)
                else:
                    break
            else:
                await self.complete_task(task.task_id)
                completed.append(task)
        return completed

    async def stats(self) -> dict[str, Any]:
        """Return scheduler statistics."""
        durations = [
            (t.completed_at - t.started_at) * 1000
            for t in self._completed
            if t.started_at > 0 and t.completed_at > 0
        ]
        return {
            "policy": self._policy.value,
            "max_concurrent": self._max_concurrent,
            "queued": len(self._queue),
            "running": len(self._running),
            "completed": len(self._completed),
            "total_submitted": self._task_counter,
            "avg_duration_ms": round(float(np.mean(durations)), 2) if durations else 0.0,
        }


# ---------------------------------------------------------------------------
# ModelOptimizer — adapts computation to hardware constraints
# ---------------------------------------------------------------------------

class ModelOptimizer:
    """Adapts model/computation parameters to fit hardware capabilities.

    Implements batch-size tuning, precision selection, and memory-budget
    optimisation strategies.
    """

    def __init__(self, profile: HardwareProfile | None = None) -> None:
        self._profile = profile or HardwareProfile()
        self._optimization_log: list[dict[str, Any]] = []

    async def recommend_batch_size(
        self,
        model_memory_mb: float,
        sample_memory_mb: float,
    ) -> dict[str, Any]:
        """Compute optimal batch size given memory constraints.

        Leaves 20% memory headroom for OS/other processes.
        """
        available = self._profile.available_memory_mb * 0.8
        remaining = available - model_memory_mb
        if remaining <= 0:
            return {"batch_size": 1, "fits_in_memory": False,
                    "available_mb": available, "model_mb": model_memory_mb}
        batch_size = max(1, int(remaining / max(sample_memory_mb, 0.01)))
        # Cap at reasonable maximum
        batch_size = min(batch_size, 4096)
        rec = {
            "batch_size": batch_size,
            "fits_in_memory": True,
            "available_mb": round(available, 1),
            "model_mb": model_memory_mb,
            "per_sample_mb": sample_memory_mb,
            "utilization_pct": round((model_memory_mb + batch_size * sample_memory_mb) / available * 100, 1),
        }
        self._optimization_log.append(rec)
        return rec

    async def recommend_precision(self) -> dict[str, Any]:
        """Recommend numerical precision based on hardware."""
        has_gpu = self._profile.gpu_available
        gpu_mem = self._profile.gpu_memory_mb
        cpu_arch = self._profile.cpu_arch.lower()

        if has_gpu and gpu_mem >= 16000:
            precision = "float32"
            reason = "Sufficient GPU memory for full precision"
        elif has_gpu and gpu_mem >= 8000:
            precision = "float16"
            reason = "Mixed precision recommended for moderate GPU memory"
        elif has_gpu:
            precision = "bfloat16" if "ampere" in self._profile.gpu_name.lower() else "float16"
            reason = "Lower precision required for limited GPU memory"
        elif "arm" in cpu_arch or "aarch64" in cpu_arch:
            precision = "float32"
            reason = "ARM CPU — float32 for compatibility"
        else:
            precision = "float32"
            reason = "CPU-only — standard precision"

        return {"precision": precision, "reason": reason, "device": self._profile.device_type.value}

    async def memory_budget(self, components: list[dict[str, float]]) -> dict[str, Any]:
        """Allocate memory budget across components.

        Each component dict should have 'name' and 'min_mb' (and optionally 'ideal_mb').
        """
        available = self._profile.available_memory_mb * 0.8
        total_min = sum(c.get("min_mb", 0) for c in components)

        if total_min > available:
            return {
                "feasible": False,
                "available_mb": round(available, 1),
                "required_mb": round(total_min, 1),
                "deficit_mb": round(total_min - available, 1),
            }

        surplus = available - total_min
        total_ideal = sum(c.get("ideal_mb", c.get("min_mb", 0)) for c in components) - total_min

        allocations = []
        for c in components:
            min_mb = c.get("min_mb", 0)
            ideal_mb = c.get("ideal_mb", min_mb)
            extra_wanted = ideal_mb - min_mb
            # Proportional surplus allocation
            extra_share = (extra_wanted / max(total_ideal, 1e-12)) * surplus if total_ideal > 0 else 0
            allocated = min_mb + min(extra_share, extra_wanted)
            allocations.append({
                "name": c.get("name", "unnamed"),
                "allocated_mb": round(allocated, 1),
                "min_mb": min_mb,
                "ideal_mb": ideal_mb,
            })

        return {
            "feasible": True,
            "available_mb": round(available, 1),
            "allocated_mb": round(sum(a["allocated_mb"] for a in allocations), 1),
            "components": allocations,
        }

    async def optimization_report(self) -> dict[str, Any]:
        """Summary of all optimisation decisions."""
        precision = await self.recommend_precision()
        return {
            "hardware": {
                "cpu_count": self._profile.cpu_count,
                "cpu_arch": self._profile.cpu_arch,
                "total_memory_mb": self._profile.total_memory_mb,
                "gpu_available": self._profile.gpu_available,
                "gpu_name": self._profile.gpu_name,
            },
            "recommended_precision": precision["precision"],
            "optimizations_performed": len(self._optimization_log),
        }


# ---------------------------------------------------------------------------
# AtlasRuntime — top-level hardware-adaptive orchestrator
# ---------------------------------------------------------------------------

class AtlasRuntime:
    """Top-level runtime that detects hardware and provides adaptive scheduling,
    resource monitoring, and model optimisation.

    Usage::

        runtime = AtlasRuntime()
        await runtime.initialize()
        report = await runtime.status()
    """

    def __init__(self) -> None:
        self.profile: HardwareProfile = HardwareProfile()
        self.monitor: ResourceMonitor = ResourceMonitor()
        self.scheduler: AdaptiveScheduler = AdaptiveScheduler()
        self.optimizer: ModelOptimizer = ModelOptimizer()
        self._initialized: bool = False

    async def initialize(self) -> HardwareProfile:
        """Detect hardware and configure subsystems accordingly."""
        # CPU
        self.profile.cpu_count = os.cpu_count() or 1
        self.profile.cpu_freq_mhz = _detect_cpu_freq()
        self.profile.cpu_arch = platform.machine() or "unknown"

        # Memory
        total, avail = _detect_memory_mb()
        self.profile.total_memory_mb = total
        self.profile.available_memory_mb = avail

        # OS
        self.profile.os_name = platform.system() or "unknown"
        self.profile.os_version = platform.release() or ""
        self.profile.python_version = platform.python_version()
        self.profile.hostname = platform.node() or ""

        # GPU
        gpu_avail, gpu_name, gpu_mem = _detect_gpu()
        self.profile.gpu_available = gpu_avail
        self.profile.gpu_name = gpu_name
        self.profile.gpu_memory_mb = gpu_mem
        self.profile.device_type = DeviceType.GPU if gpu_avail else DeviceType.CPU

        self.profile.timestamp = time.time()

        # Configure scheduler concurrency based on CPU count
        max_conc = max(2, self.profile.cpu_count)
        policy = SchedulePolicy.THERMAL_AWARE if self.profile.cpu_count >= 4 else SchedulePolicy.PRIORITY
        self.scheduler = AdaptiveScheduler(max_concurrent=max_conc, policy=policy)

        # Configure optimizer with detected profile
        self.optimizer = ModelOptimizer(profile=self.profile)

        self._initialized = True
        logger.info(
            "Atlas initialized: %s %s, %d CPUs, %.0f MB RAM, GPU=%s",
            self.profile.os_name, self.profile.cpu_arch,
            self.profile.cpu_count, self.profile.total_memory_mb,
            self.profile.gpu_name or "none",
        )
        return self.profile

    async def status(self) -> dict[str, Any]:
        """Comprehensive runtime status."""
        snap = await self.monitor.snapshot()
        sched = await self.scheduler.stats()
        return {
            "initialized": self._initialized,
            "hardware": {
                "cpu_count": self.profile.cpu_count,
                "cpu_arch": self.profile.cpu_arch,
                "total_memory_mb": self.profile.total_memory_mb,
                "gpu": self.profile.gpu_name or "none",
                "device": self.profile.device_type.value,
            },
            "resources": {
                "cpu_percent": snap.cpu_percent,
                "memory_percent": snap.memory_percent,
            },
            "scheduler": sched,
        }

    async def auto_configure(self) -> dict[str, Any]:
        """Auto-configure all subsystems based on detected hardware.

        Returns a configuration summary.
        """
        if not self._initialized:
            await self.initialize()

        precision = await self.optimizer.recommend_precision()
        batch_rec = await self.optimizer.recommend_batch_size(
            model_memory_mb=500, sample_memory_mb=2,
        )
        overloaded = await self.monitor.is_overloaded()

        config = {
            "precision": precision["precision"],
            "max_batch_size": batch_rec["batch_size"],
            "scheduler_policy": self.scheduler._policy.value,
            "max_concurrent_tasks": self.scheduler._max_concurrent,
            "system_overloaded": overloaded,
        }
        logger.info("Atlas auto-configured: %s", config)
        return config
