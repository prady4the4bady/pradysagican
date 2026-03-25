"""OMEGA-2 root architecture scaffold for God-layer orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from pradysagican.godlayer.kernel import GodLayerKernel


@dataclass(frozen=True)
class CoreBus:
    """Single OMEGA-2 bus definition."""

    bus_id: str
    name: str
    cadence: str
    systems: tuple[str, ...]


@dataclass(frozen=True)
class OperatingWindow:
    """Hour window in the 24-hour cycle."""

    name: str
    start_hour: int
    end_hour: int
    primary_bus: str

    def contains(self, hour: int) -> bool:
        h = hour % 24
        if self.start_hour < self.end_hour:
            return self.start_hour <= h < self.end_hour
        return h >= self.start_hour or h < self.end_hour


@dataclass
class GodLayerOmega2Runtime:
    """Practical root runtime for the proposed 5-bus architecture."""

    kernel: GodLayerKernel = field(default_factory=GodLayerKernel)

    BUSES: tuple[CoreBus, ...] = (
        CoreBus("BUS-0", "Survival", "100Hz", ("MAXWELL", "ABC", "FORTRESS")),
        CoreBus("BUS-1", "Cognition", "10Hz", ("PSYCHE", "LOGOS", "CHRONOS", "ATLAS")),
        CoreBus("BUS-2", "Evolution", "nightly", ("OUROBOROS", "ARENA", "SICA", "DRQ")),
        CoreBus("BUS-3", "Discovery", "opportunistic", ("ARCHIMEDES", "EINSTEIN", "SOCRATES", "MORPHEUS")),
        CoreBus("BUS-4", "Interaction", "on-demand", ("ORACLE", "EMPATHY", "MIDAS", "MNEMOSYNE")),
    )

    WINDOWS: tuple[OperatingWindow, ...] = (
        OperatingWindow("evolution", 0, 8, "BUS-2"),
        OperatingWindow("active", 8, 22, "BUS-4"),
        OperatingWindow("consolidation", 22, 24, "BUS-1"),
    )

    def architecture_summary(self) -> dict[str, Any]:
        return {
            "buses": [
                {
                    "bus_id": b.bus_id,
                    "name": b.name,
                    "cadence": b.cadence,
                    "systems": list(b.systems),
                }
                for b in self.BUSES
            ],
            "windows": [
                {
                    "name": w.name,
                    "start_hour": w.start_hour,
                    "end_hour": w.end_hour,
                    "primary_bus": w.primary_bus,
                }
                for w in self.WINDOWS
            ],
        }

    def current_window(self, local_hour: int | None = None) -> dict[str, Any]:
        hour = datetime.now().hour if local_hour is None else local_hour % 24
        for window in self.WINDOWS:
            if window.contains(hour):
                return {
                    "hour": hour,
                    "window": window.name,
                    "primary_bus": window.primary_bus,
                }
        return {"hour": hour, "window": "unknown", "primary_bus": "BUS-1"}

    def run_bus_once(self, bus_id: str, local_hour: int | None = None) -> dict[str, Any]:
        hour = datetime.now().hour if local_hour is None else local_hour % 24

        if bus_id == "BUS-0":
            return self.kernel.run_immune_check(
                anomaly_signature="periodic_safety_probe",
                detector_signals=[False, True, True],
                complexity=0.3,
                impact=0.3,
                uncertainty=0.2,
            )
        if bus_id == "BUS-1":
            return self.kernel.metacognitive_scan(
                reasoning_text="initial check for coherence and drift",
                confidence_outcomes=[(0.7, True), (0.6, True), (0.4, False)],
                task_type="planning",
                elapsed_seconds=12.0,
                uncertainty=0.4,
                impact=0.5,
                deadline_pressure=0.3,
            )
        if bus_id == "BUS-2":
            return self.kernel.run_somnium_cycle(
                events=[{"event": "nightly evolution pass"}, {"event": "regression triage"}],
                awake_hours=6.0 if hour < 8 else 12.0,
                local_hour=hour,
                idle_minutes=50,
            )
        if bus_id == "BUS-3":
            return self.kernel.project_future(
                current_scores={"GPQA": 55.0, "SWE-Bench": 35.0, "TauBench": 40.0},
                daily_improvement=0.12,
                days=30,
                intent="discover highest-leverage improvements",
            )
        if bus_id == "BUS-4":
            alignment = self.kernel.goal_alignment(
                action="serve user request with safe optimization",
                option_scores={"safe_fast": 0.81, "safe_deep": 0.84},
            )
            decision = self.kernel.quantum_decide({"safe_fast": 0.76, "safe_deep": 0.92})
            return {"alignment": alignment, "decision": decision}

        return {"error": f"unknown bus: {bus_id}"}

    def run_cycle_tick(self, local_hour: int | None = None) -> dict[str, Any]:
        window = self.current_window(local_hour)
        primary = window["primary_bus"]
        outputs: dict[str, Any] = {primary: self.run_bus_once(primary, local_hour=window["hour"])}

        # Background buses expected by the daily model.
        if window["window"] == "active":
            outputs["BUS-1"] = self.run_bus_once("BUS-1", local_hour=window["hour"])
        if window["window"] == "consolidation":
            outputs["BUS-3"] = self.run_bus_once("BUS-3", local_hour=window["hour"])

        return {
            "window": window,
            "outputs": outputs,
            "kernel_inventory": self.kernel.inventory(),
        }

    def status(self, local_hour: int | None = None) -> dict[str, Any]:
        return {
            "architecture": self.architecture_summary(),
            "cycle": self.run_cycle_tick(local_hour=local_hour),
            "kernel_status": self.kernel.status(),
        }

