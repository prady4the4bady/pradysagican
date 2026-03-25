"""System Manifest — The master wiring document for PRADYSAGICAN.

Auto-discovers all modules, maps connections between them, and provides
health checks, dependency graphs, and architecture summaries.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # pradysagican/


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class ModuleInfo:
    """Metadata for a single module."""
    name: str
    path: str
    version: str = "1.0.0"
    classes: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    signals_produced: list[str] = field(default_factory=list)
    signals_consumed: list[str] = field(default_factory=list)
    health_status: str = "unknown"  # "healthy", "degraded", "error", "unknown"
    line_count: int = 0


@dataclass
class ConnectionInfo:
    """A wire between two modules."""
    source: str
    target: str
    signal_type: str
    direction: str = "unidirectional"  # or "bidirectional"
    description: str = ""
    pipeline: str = ""  # which pipeline this belongs to


# ── Connection Definitions ───────────────────────────────────────────────────
# 10 major pipelines mapping how modules communicate.

_PIPELINE_DEFINITIONS: dict[str, list[dict[str, str]]] = {
    "perception": [
        {"source": "automation.gateway", "target": "core.consciousness", "signal": "input_event", "desc": "Raw input enters the system"},
        {"source": "core.consciousness", "target": "core.reasoning", "signal": "attention_focus", "desc": "Consciousness directs reasoning focus"},
    ],
    "memory": [
        {"source": "core.reasoning", "target": "core.memory", "signal": "store_request", "desc": "Reasoning stores conclusions"},
        {"source": "core.memory", "target": "core.neuro_symbolic", "signal": "knowledge_update", "desc": "Memory feeds knowledge base"},
    ],
    "decision": [
        {"source": "core.reasoning", "target": "agents.ethics", "signal": "ethics_check", "desc": "Reasoning seeks ethical validation"},
        {"source": "agents.ethics", "target": "agents.strategist", "signal": "approved_action", "desc": "Ethics-cleared actions reach strategy"},
        {"source": "agents.strategist", "target": "agents.orchestrator", "signal": "strategic_plan", "desc": "Strategy dispatches through orchestrator"},
    ],
    "action": [
        {"source": "agents.orchestrator", "target": "tools.nexus", "signal": "tool_request", "desc": "Orchestrator invokes tools"},
        {"source": "tools.nexus", "target": "automation.gateway", "signal": "action_result", "desc": "Tool results return through gateway"},
    ],
    "evolution": [
        {"source": "core.prometheus", "target": "agents.learner", "signal": "performance_data", "desc": "Prometheus feeds learning signals"},
        {"source": "agents.learner", "target": "agents.inventor", "signal": "improvement_hypothesis", "desc": "Learner proposes innovations"},
        {"source": "agents.inventor", "target": "core.memory", "signal": "invention_record", "desc": "Inventions stored in memory"},
    ],
    "safety": [
        {"source": "safety.guardrails", "target": "safety.dual_mode", "signal": "safety_check", "desc": "Guardrails validate through dual-mode"},
        {"source": "safety.dual_mode", "target": "safety.sovereign_lock", "signal": "mode_request", "desc": "Sovereign access requires lock auth"},
        {"source": "safety.sovereign_lock", "target": "agents.ethics", "signal": "clearance_result", "desc": "Lock clearance flows to ethics"},
    ],
    "biological": [
        {"source": "core.bio_core", "target": "core.atlas", "signal": "vital_signs", "desc": "Bio-core reports vitals to runtime"},
        {"source": "core.atlas", "target": "core.aegis", "signal": "health_alert", "desc": "Runtime alerts wiring layer"},
        {"source": "core.aegis", "target": "core.prometheus", "signal": "circuit_status", "desc": "Wiring status reaches monitoring"},
    ],
    "prediction": [
        {"source": "core.prediction_engine", "target": "core.neuro_symbolic", "signal": "prediction_evidence", "desc": "Predictions feed symbolic reasoning"},
        {"source": "core.neuro_symbolic", "target": "core.hallucination_shield", "signal": "reasoning_output", "desc": "Reasoning outputs verified for hallucinations"},
    ],
    "temporal": [
        {"source": "core.temporal_cortex", "target": "core.cognitive_resilience", "signal": "temporal_context", "desc": "Temporal info feeds resilience"},
        {"source": "core.cognitive_resilience", "target": "core.cognitive_bus", "signal": "checkpoint_event", "desc": "Checkpoints broadcast on bus"},
    ],
    "collective": [
        {"source": "core.collective_intelligence", "target": "core.quantum_ready", "signal": "distributed_task", "desc": "Collective distributes quantum tasks"},
        {"source": "core.quantum_ready", "target": "core.memory", "signal": "quantum_result", "desc": "Quantum results stored in memory"},
    ],
}


# ── System Manifest ──────────────────────────────────────────────────────────

class SystemManifest:
    """The master wiring document — shows how all 50+ modules connect.

    Auto-discovers modules by scanning the package tree, catalogues
    their classes, and maps inter-module connections through 10 pipelines.
    """

    def __init__(self, auto_discover: bool = True) -> None:
        self._modules: dict[str, ModuleInfo] = {}
        self._connections: list[ConnectionInfo] = []
        self._pipelines: dict[str, list[ConnectionInfo]] = {}
        self._discovered_at: float = time.time()

        if auto_discover:
            self._discover_modules()
            self._map_connections()

    # ── Module Discovery ──────────────────────────────────────────────────

    def _discover_modules(self) -> None:
        """Scan pradysagican/ for all .py files, import and catalog."""
        for dirpath, _dirnames, filenames in os.walk(_PACKAGE_ROOT):
            rel_dir = Path(dirpath).relative_to(_PACKAGE_ROOT)
            for fname in sorted(filenames):
                if not fname.endswith(".py") or fname == "__init__.py":
                    continue
                if "__pycache__" in dirpath or "/tests/" in dirpath:
                    continue

                stem = fname[:-3]
                parts = list(rel_dir.parts) + [stem]
                dotted = ".".join(parts)  # e.g. "core.consciousness"
                full_module = f"pradysagican.{dotted}"
                file_path = os.path.join(dirpath, fname)

                # Count lines
                try:
                    with open(file_path, encoding="utf-8", errors="replace") as fh:
                        line_count = sum(1 for _ in fh)
                except OSError:
                    line_count = 0

                # Attempt import to discover classes
                classes: list[str] = []
                try:
                    mod = importlib.import_module(full_module)
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name, None)
                        if inspect.isclass(attr) and attr.__module__ == full_module:
                            classes.append(attr_name)
                except Exception as exc:
                    logger.debug("Could not import %s: %s", full_module, exc)

                info = ModuleInfo(
                    name=dotted,
                    path=file_path,
                    classes=sorted(classes),
                    line_count=line_count,
                    health_status="healthy" if classes else "unknown",
                )
                self._modules[dotted] = info

        logger.info("Discovered %d modules", len(self._modules))

    # ── Connection Mapping ────────────────────────────────────────────────

    def _map_connections(self) -> None:
        """Define how modules talk to each other through 10 pipelines."""
        for pipeline_name, wires in _PIPELINE_DEFINITIONS.items():
            pipeline_conns: list[ConnectionInfo] = []
            for wire in wires:
                conn = ConnectionInfo(
                    source=wire["source"],
                    target=wire["target"],
                    signal_type=wire["signal"],
                    direction="unidirectional",
                    description=wire["desc"],
                    pipeline=pipeline_name,
                )
                self._connections.append(conn)
                pipeline_conns.append(conn)

                # Mark signals on modules
                src_mod = self._modules.get(wire["source"])
                tgt_mod = self._modules.get(wire["target"])
                if src_mod and wire["signal"] not in src_mod.signals_produced:
                    src_mod.signals_produced.append(wire["signal"])
                if tgt_mod and wire["signal"] not in tgt_mod.signals_consumed:
                    tgt_mod.signals_consumed.append(wire["signal"])

                # Record dependencies
                if tgt_mod and wire["source"] not in tgt_mod.dependencies:
                    tgt_mod.dependencies.append(wire["source"])

            self._pipelines[pipeline_name] = pipeline_conns

        logger.info("Mapped %d connections across %d pipelines", len(self._connections), len(self._pipelines))

    # ── Queries ───────────────────────────────────────────────────────────

    def get_module(self, name: str) -> ModuleInfo | None:
        """Look up a module by dotted name (e.g. 'core.consciousness')."""
        return self._modules.get(name)

    def get_connections(self, module_name: str) -> list[ConnectionInfo]:
        """All connections involving a specific module (as source or target)."""
        return [
            c for c in self._connections
            if c.source == module_name or c.target == module_name
        ]

    def get_all_connections(self) -> list[ConnectionInfo]:
        """Every connection in the system."""
        return list(self._connections)

    def get_pipeline(self, pipeline_name: str) -> list[ConnectionInfo]:
        """Get connections in a specific pipeline."""
        return list(self._pipelines.get(pipeline_name, []))

    def list_pipelines(self) -> list[str]:
        """Names of all defined pipelines."""
        return list(self._pipelines.keys())

    def list_modules(self) -> list[str]:
        """Names of all discovered modules."""
        return sorted(self._modules.keys())

    # ── Dependency Graph ──────────────────────────────────────────────────

    def dependency_graph(self) -> dict[str, list[str]]:
        """Full dependency tree: module → [dependencies]."""
        return {
            name: list(mod.dependencies)
            for name, mod in sorted(self._modules.items())
        }

    # ── Health Check ──────────────────────────────────────────────────────

    def health_check_all(self) -> dict[str, str]:
        """Status of every module (re-checks importability)."""
        results: dict[str, str] = {}
        for name, mod in self._modules.items():
            full_module = f"pradysagican.{name}"
            try:
                importlib.import_module(full_module)
                mod.health_status = "healthy"
            except Exception:
                mod.health_status = "error"
            results[name] = mod.health_status
        return results

    # ── Architecture Summary ──────────────────────────────────────────────

    def get_architecture_summary(self) -> dict[str, Any]:
        """High-level stats about the entire system."""
        total_classes = sum(len(m.classes) for m in self._modules.values())
        total_lines = sum(m.line_count for m in self._modules.values())
        healthy = sum(1 for m in self._modules.values() if m.health_status == "healthy")

        # Try to get feature count from FeatureRegistry
        feature_total = 0
        try:
            from pradysagican.core.feature_registry import FeatureRegistry
            reg = FeatureRegistry()
            feature_total = reg.total_features()
        except Exception:
            pass

        return {
            "total_modules": len(self._modules),
            "total_classes": total_classes,
            "total_lines": total_lines,
            "total_connections": len(self._connections),
            "total_pipelines": len(self._pipelines),
            "healthy_modules": healthy,
            "total_features": feature_total,
            "pipeline_names": list(self._pipelines.keys()),
            "discovered_at": self._discovered_at,
        }

    # ── Validation ────────────────────────────────────────────────────────

    def validate_wiring(self) -> list[str]:
        """Find broken connections (source or target module missing)."""
        issues: list[str] = []
        for conn in self._connections:
            if conn.source not in self._modules:
                issues.append(
                    f"Missing source module '{conn.source}' in pipeline '{conn.pipeline}' "
                    f"(signal: {conn.signal_type})"
                )
            if conn.target not in self._modules:
                issues.append(
                    f"Missing target module '{conn.target}' in pipeline '{conn.pipeline}' "
                    f"(signal: {conn.signal_type})"
                )
        if not issues:
            logger.info("Wiring validation passed — all connections intact")
        else:
            logger.warning("Wiring validation found %d issues", len(issues))
        return issues

    # ── Export ─────────────────────────────────────────────────────────────

    def export_manifest(self) -> dict[str, Any]:
        """Complete JSON-serializable manifest."""
        return {
            "version": "1.0.0",
            "generated_at": time.time(),
            "architecture": self.get_architecture_summary(),
            "modules": {
                name: {
                    "path": mod.path,
                    "version": mod.version,
                    "classes": mod.classes,
                    "dependencies": mod.dependencies,
                    "signals_produced": mod.signals_produced,
                    "signals_consumed": mod.signals_consumed,
                    "health_status": mod.health_status,
                    "line_count": mod.line_count,
                }
                for name, mod in sorted(self._modules.items())
            },
            "connections": [
                {
                    "source": c.source,
                    "target": c.target,
                    "signal_type": c.signal_type,
                    "direction": c.direction,
                    "description": c.description,
                    "pipeline": c.pipeline,
                }
                for c in self._connections
            ],
            "pipelines": {
                name: [
                    {"source": c.source, "target": c.target, "signal": c.signal_type}
                    for c in conns
                ]
                for name, conns in self._pipelines.items()
            },
            "wiring_issues": self.validate_wiring(),
        }

    @property
    def module_count(self) -> int:
        return len(self._modules)

    @property
    def connection_count(self) -> int:
        return len(self._connections)
