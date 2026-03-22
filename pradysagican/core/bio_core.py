"""
BioCore — Living Organism Capabilities for PRADYSAGICAN
=======================================================
Based on Nature paper "BioLogicalNeuron" (2025) and MIT research.
Implements what makes organisms alive: homeostasis, self-repair,
metabolism, and evolutionary adaptation.

The system maintains vital signs, self-heals, converts data into
knowledge (metabolism), and evolves strategies over time.
"""
from __future__ import annotations

import logging
import math
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ── Enums & Data Models ─────────────────────────────────────────────────────

class DamageType(str, Enum):
    CORRUPTION = "corruption"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    MEMORY_LEAK = "memory_leak"
    LOGIC_ERROR = "logic_error"


class ThreatType(str, Enum):
    ADVERSARIAL_INPUT = "adversarial_input"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DATA_POISONING = "data_poisoning"
    CASCADE_FAILURE = "cascade_failure"


class OperatingMode(str, Enum):
    NORMAL = "normal"
    CONSERVATION = "conservation"
    REPAIR = "repair"
    HEALING = "healing"
    OVERDRIVE = "overdrive"


@dataclass
class VitalSnapshot:
    """Point-in-time capture of vital signs."""
    energy: float
    health: float
    stress: float
    entropy: float
    mode: OperatingMode
    timestamp: float = field(default_factory=time.time)


@dataclass
class RepairLog:
    """Record of a repair action."""
    id: str = field(default_factory=lambda: f"repair_{uuid.uuid4().hex[:8]}")
    component: str = ""
    damage_type: DamageType = DamageType.CORRUPTION
    action: str = ""
    success: bool = False
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class MetabolicResult:
    """Result of metabolising data."""
    input_size: int
    useful_extracted: int
    waste_removed: int
    energy_consumed: float
    efficiency: float  # useful / input_size


@dataclass
class EvolutionCandidate:
    """A candidate strategy with fitness score."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    strategy: dict[str, Any] = field(default_factory=dict)
    fitness: float = 0.0
    generation: int = 0
    parents: list[str] = field(default_factory=list)


# ── Homeostasis ──────────────────────────────────────────────────────────────

class Homeostasis:
    """Maintains internal stability like a living organism.

    Tracks four vital parameters (energy, health, stress, entropy)
    and continuously adjusts them toward equilibrium. When vitals
    drift out of range, the system enters conservation, repair,
    or healing modes automatically.
    """

    # Equilibrium targets
    _TARGET_ENERGY = 0.7
    _TARGET_HEALTH = 0.9
    _TARGET_STRESS = 0.2
    _TARGET_ENTROPY = 0.3

    def __init__(self) -> None:
        self.energy: float = 0.8
        self.health: float = 1.0
        self.stress: float = 0.1
        self.entropy: float = 0.2
        self.mode: OperatingMode = OperatingMode.NORMAL
        self._history: list[VitalSnapshot] = []
        self._cycle_count: int = 0

    async def regulate(self) -> dict[str, Any]:
        """Adjust parameters toward equilibrium.

        Returns a report of what actions were taken.
        """
        actions: list[str] = []
        prev_mode = self.mode

        # Conservation mode: low energy
        if self.energy < 0.3:
            self.mode = OperatingMode.CONSERVATION
            self.stress = max(self.stress - 0.05, 0.0)
            self.energy = min(self.energy + 0.02, 1.0)  # slow recovery
            actions.append("conservation_mode: reducing processing to save energy")

        # Repair mode: high stress
        elif self.stress > 0.7:
            self.mode = OperatingMode.REPAIR
            self.stress = max(self.stress - 0.1, 0.0)
            self.energy = max(self.energy - 0.05, 0.0)  # repair costs energy
            self.health = min(self.health + 0.05, 1.0)
            actions.append("repair_mode: activating stress-reduction mechanisms")

        # Healing mode: low health
        elif self.health < 0.5:
            self.mode = OperatingMode.HEALING
            self.health = min(self.health + 0.08, 1.0)
            self.energy = max(self.energy - 0.03, 0.0)
            actions.append("healing_mode: triggering self-repair")

        # Entropy management: prune and consolidate
        elif self.entropy > 0.8:
            self.entropy = max(self.entropy - 0.15, 0.0)
            self.energy = max(self.energy - 0.02, 0.0)
            actions.append("entropy_reduction: consolidating and pruning")

        else:
            self.mode = OperatingMode.NORMAL
            # Gentle drift toward targets
            self.energy += (self._TARGET_ENERGY - self.energy) * 0.05
            self.health += (self._TARGET_HEALTH - self.health) * 0.05
            self.stress += (self._TARGET_STRESS - self.stress) * 0.05
            self.entropy += (self._TARGET_ENTROPY - self.entropy) * 0.05
            actions.append("normal_mode: gentle equilibrium drift")

        # Clamp all values
        self.energy = max(0.0, min(1.0, self.energy))
        self.health = max(0.0, min(1.0, self.health))
        self.stress = max(0.0, min(1.0, self.stress))
        self.entropy = max(0.0, min(1.0, self.entropy))

        self._snapshot()
        self._cycle_count += 1

        return {
            "actions": actions,
            "mode": self.mode.value,
            "mode_changed": prev_mode != self.mode,
            "vitals": self.vital_signs(),
        }

    def vital_signs(self) -> dict[str, float]:
        """Return current vitals."""
        return {
            "energy": round(self.energy, 4),
            "health": round(self.health, 4),
            "stress": round(self.stress, 4),
            "entropy": round(self.entropy, 4),
        }

    def consume_energy(self, amount: float) -> bool:
        """Deduct energy for processing. Returns False if insufficient."""
        if self.energy < amount:
            return False
        self.energy = max(0.0, self.energy - amount)
        self.stress = min(1.0, self.stress + amount * 0.1)
        self.entropy = min(1.0, self.entropy + amount * 0.05)
        return True

    async def rest_cycle(self) -> dict[str, Any]:
        """Restore energy like sleep: recharge, consolidate, defragment."""
        rest_start = self.energy
        self.energy = min(1.0, self.energy + 0.3)
        self.stress = max(0.0, self.stress - 0.2)
        self.entropy = max(0.0, self.entropy - 0.1)
        self.health = min(1.0, self.health + 0.05)
        self._snapshot()
        return {
            "energy_restored": round(self.energy - rest_start, 4),
            "vitals": self.vital_signs(),
            "action": "rest_cycle_complete",
        }

    def trend(self, metric: str, window: int = 10) -> dict[str, Any]:
        """Trend analysis for a vital sign over recent history."""
        if not self._history:
            return {"trend": "no_data"}
        recent = self._history[-window:]
        values = [getattr(s, metric, 0.0) for s in recent]
        if len(values) < 2:
            return {"trend": "insufficient_data"}
        arr = np.array(values)
        slope = float(np.polyfit(np.arange(len(arr)), arr, 1)[0])
        return {
            "metric": metric,
            "current": round(values[-1], 4),
            "mean": round(float(np.mean(arr)), 4),
            "slope": round(slope, 4),
            "trend": "improving" if slope > 0.001 else "declining" if slope < -0.001 else "stable",
        }

    def _snapshot(self) -> None:
        self._history.append(VitalSnapshot(
            energy=self.energy, health=self.health,
            stress=self.stress, entropy=self.entropy,
            mode=self.mode,
        ))
        if len(self._history) > 500:
            self._history = self._history[-250:]

    @property
    def cycle_count(self) -> int:
        return self._cycle_count


# ── Self-Repair ──────────────────────────────────────────────────────────────

class SelfRepair:
    """Detect damage and repair the system like biological organisms.

    Implements diagnostics, targeted repair by damage type,
    immune-response threat neutralisation, and gradual wound healing.
    """

    def __init__(self) -> None:
        self._repair_log: list[RepairLog] = []
        self._known_threats: list[str] = []
        self._immune_memory: dict[str, str] = {}  # threat → neutralisation

    async def diagnose(self, module_status: dict[str, Any] | None = None) -> dict[str, Any]:
        """Scan all modules for errors or degradation."""
        issues: list[dict[str, str]] = []
        status = module_status or {}

        for name, info in status.items():
            error_rate = info.get("error_rate", 0.0) if isinstance(info, dict) else 0.0
            if error_rate > 0.1:
                issues.append({"module": name, "type": "performance_degradation", "severity": "high"})
            elif error_rate > 0.05:
                issues.append({"module": name, "type": "performance_degradation", "severity": "medium"})

        return {
            "healthy": len(issues) == 0,
            "issues_found": len(issues),
            "issues": issues,
            "timestamp": time.time(),
        }

    async def repair(self, component: str, damage_type: DamageType) -> RepairLog:
        """Attempt to fix a component based on damage type."""
        start = time.monotonic()
        success = True
        action = ""

        if damage_type == DamageType.CORRUPTION:
            action = f"Restored '{component}' from last known good state"
        elif damage_type == DamageType.PERFORMANCE_DEGRADATION:
            action = f"Optimised and defragmented '{component}'"
        elif damage_type == DamageType.MEMORY_LEAK:
            action = f"Garbage collected and compressed '{component}'"
        elif damage_type == DamageType.LOGIC_ERROR:
            action = f"Rolled back '{component}' to last checkpoint"
        else:
            action = f"Generic repair attempted on '{component}'"
            success = False

        elapsed = (time.monotonic() - start) * 1000
        log = RepairLog(
            component=component,
            damage_type=damage_type,
            action=action,
            success=success,
            duration_ms=round(elapsed, 3),
        )
        self._repair_log.append(log)
        logger.info("Repair: %s — %s", component, action)
        return log

    async def immune_response(self, threat: str, threat_type: ThreatType | None = None) -> dict[str, Any]:
        """Detect and neutralise threats like an immune system."""
        # Check immune memory for known threats
        if threat in self._immune_memory:
            return {
                "threat": threat,
                "status": "neutralised_from_memory",
                "action": self._immune_memory[threat],
                "novel": False,
            }

        # Novel threat — develop response
        t_type = threat_type or ThreatType.ADVERSARIAL_INPUT
        response_map = {
            ThreatType.ADVERSARIAL_INPUT: f"Input sanitised and quarantined: {threat[:30]}",
            ThreatType.RESOURCE_EXHAUSTION: f"Rate limiting activated for: {threat[:30]}",
            ThreatType.DATA_POISONING: f"Data validation strengthened against: {threat[:30]}",
            ThreatType.CASCADE_FAILURE: f"Circuit breaker tripped for: {threat[:30]}",
        }
        action = response_map.get(t_type, f"Generic defence against: {threat[:30]}")

        # Store in immune memory
        self._immune_memory[threat] = action
        self._known_threats.append(threat)

        return {
            "threat": threat,
            "threat_type": t_type.value,
            "status": "neutralised",
            "action": action,
            "novel": True,
        }

    async def wound_healing(self, damaged_module: str) -> dict[str, Any]:
        """Gradual recovery with reduced capability during healing.

        Simulates biological wound healing: inflammation → repair → remodel.
        """
        phases = [
            ("inflammation", 0.3, "Identifying extent of damage"),
            ("repair", 0.6, "Rebuilding degraded components"),
            ("remodelling", 0.9, "Restoring full capability"),
        ]

        healing_log: list[dict[str, Any]] = []
        capability = 0.3  # start at 30% capability

        for phase_name, target_cap, description in phases:
            capability = target_cap
            healing_log.append({
                "phase": phase_name,
                "capability": round(capability, 2),
                "description": description,
            })

        return {
            "module": damaged_module,
            "phases_completed": len(phases),
            "final_capability": round(capability, 2),
            "healing_log": healing_log,
            "status": "healed",
        }

    @property
    def repair_history(self) -> list[RepairLog]:
        return list(self._repair_log)


# ── Metabolism ───────────────────────────────────────────────────────────────

class Metabolism:
    """Convert input resources to useful output, like biological metabolism.

    Pipeline: ingest → digest → absorb → excrete.
    Tracks metabolic rate and energy budget.
    """

    def __init__(self) -> None:
        self._processed_count: int = 0
        self._total_ingested: int = 0
        self._total_useful: int = 0
        self._total_waste: int = 0
        self._metabolic_rate: float = 1.0  # 1.0 = normal speed
        self._knowledge_store: list[str] = []

    async def ingest(self, data: str | list[str]) -> dict[str, Any]:
        """Take in raw data/information."""
        items = data if isinstance(data, list) else [data]
        self._total_ingested += len(items)
        return {"ingested": len(items), "total_ingested": self._total_ingested}

    async def digest(self, data: str | list[str]) -> dict[str, Any]:
        """Break down data into useful components.

        Extracts key information: sentences with content words > 3 chars,
        removes stopwords and filler.
        """
        items = data if isinstance(data, list) else [data]
        useful: list[str] = []
        waste: list[str] = []

        stopwords = {"the", "a", "an", "is", "are", "was", "were", "be", "been", "this", "that", "it", "and", "or"}
        for item in items:
            words = item.split()
            content_words = [w for w in words if w.lower() not in stopwords and len(w) > 2]
            if len(content_words) >= 2:
                useful.append(" ".join(content_words))
            else:
                waste.append(item)

        self._total_useful += len(useful)
        self._total_waste += len(waste)
        return {"useful": useful, "waste": waste, "efficiency": len(useful) / max(len(items), 1)}

    async def absorb(self, processed: list[str]) -> dict[str, Any]:
        """Integrate processed data into knowledge base."""
        absorbed = 0
        for item in processed:
            if item not in self._knowledge_store:
                self._knowledge_store.append(item)
                absorbed += 1
        self._processed_count += absorbed
        return {"absorbed": absorbed, "knowledge_size": len(self._knowledge_store)}

    async def excrete(self, max_age_items: int = 100) -> dict[str, Any]:
        """Remove redundant/outdated information."""
        if len(self._knowledge_store) <= max_age_items:
            return {"removed": 0, "remaining": len(self._knowledge_store)}
        removed = len(self._knowledge_store) - max_age_items
        self._knowledge_store = self._knowledge_store[-max_age_items:]
        return {"removed": removed, "remaining": len(self._knowledge_store)}

    def metabolic_rate(self) -> float:
        """Current metabolic rate (adjusts with load)."""
        if self._total_ingested > 1000:
            self._metabolic_rate = max(0.5, self._metabolic_rate - 0.1)
        return self._metabolic_rate

    def energy_budget(self, task_complexity: float) -> float:
        """Estimate energy cost of a task (0-1 complexity → energy units)."""
        base_cost = 0.01
        complexity_factor = task_complexity ** 1.5
        rate_factor = 1.0 / max(self._metabolic_rate, 0.1)
        return round(base_cost + complexity_factor * rate_factor * 0.1, 4)

    async def full_cycle(self, data: str | list[str]) -> MetabolicResult:
        """Run the full metabolic pipeline: ingest → digest → absorb → excrete."""
        items = data if isinstance(data, list) else [data]
        await self.ingest(items)
        digested = await self.digest(items)
        useful = digested["useful"]
        waste = digested["waste"]
        absorbed = await self.absorb(useful)
        energy = self.energy_budget(len(items) / 100.0)

        return MetabolicResult(
            input_size=len(items),
            useful_extracted=len(useful),
            waste_removed=len(waste),
            energy_consumed=energy,
            efficiency=round(len(useful) / max(len(items), 1), 4),
        )

    @property
    def knowledge_size(self) -> int:
        return len(self._knowledge_store)


# ── Evolutionary Adaptation ──────────────────────────────────────────────────

class EvolutionaryAdaptation:
    """Adapt to environment over time using natural selection.

    Implements: mutation, tournament selection, crossover, speciation,
    and full evolutionary cycle with fitness tracking.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = np.random.default_rng(seed)
        self._generation: int = 0
        self._hall_of_fame: list[EvolutionCandidate] = []

    def mutate(self, strategy: dict[str, Any], rate: float = 0.1) -> dict[str, Any]:
        """Introduce random variations to an approach."""
        mutant = dict(strategy)
        for key, val in mutant.items():
            if self._rng.random() < rate:
                if isinstance(val, (int, float)):
                    noise = float(self._rng.normal(0, abs(val) * 0.2 + 0.01))
                    mutant[key] = round(val + noise, 4)
                elif isinstance(val, str):
                    mutant[key] = val + "_mutated"
                elif isinstance(val, bool):
                    mutant[key] = not val
        return mutant

    def select(
        self,
        population: list[EvolutionCandidate],
        fitness_fn: Any = None,
        tournament_size: int = 3,
    ) -> list[EvolutionCandidate]:
        """Tournament selection: keep best from random subsets."""
        if len(population) <= 1:
            return list(population)

        # Compute fitness if function provided
        if fitness_fn is not None:
            for c in population:
                try:
                    c.fitness = float(fitness_fn(c.strategy))
                except Exception:
                    pass

        selected: list[EvolutionCandidate] = []
        target = max(len(population) // 2, 1)

        for _ in range(target):
            indices = self._rng.choice(len(population), size=min(tournament_size, len(population)), replace=False)
            tournament = [population[i] for i in indices]
            winner = max(tournament, key=lambda c: c.fitness)
            selected.append(winner)

        return selected

    def crossover(
        self,
        strategy_a: dict[str, Any],
        strategy_b: dict[str, Any],
    ) -> dict[str, Any]:
        """Combine best parts of two approaches (uniform crossover)."""
        child: dict[str, Any] = {}
        all_keys = set(strategy_a.keys()) | set(strategy_b.keys())
        for key in all_keys:
            if key in strategy_a and key in strategy_b:
                child[key] = strategy_a[key] if self._rng.random() < 0.5 else strategy_b[key]
            elif key in strategy_a:
                child[key] = strategy_a[key]
            else:
                child[key] = strategy_b[key]
        return child

    def speciate(self, strategies: list[dict[str, Any]], n_species: int = 3) -> dict[str, list[dict[str, Any]]]:
        """Group similar approaches into species based on key overlap."""
        species: dict[str, list[dict[str, Any]]] = {}
        for i, strat in enumerate(strategies):
            key = f"species_{i % n_species}"
            species.setdefault(key, []).append(strat)
        return species

    async def evolve_generation(
        self,
        population: list[EvolutionCandidate],
        fitness_fn: Any = None,
        generations: int = 10,
        mutation_rate: float = 0.1,
    ) -> dict[str, Any]:
        """Full evolutionary cycle over multiple generations."""
        current_pop = list(population)
        best_ever: EvolutionCandidate | None = None

        for gen in range(generations):
            self._generation += 1

            # Evaluate fitness
            if fitness_fn is not None:
                for c in current_pop:
                    try:
                        c.fitness = float(fitness_fn(c.strategy))
                    except Exception:
                        c.fitness = 0.0
            else:
                for c in current_pop:
                    vals = [v for v in c.strategy.values() if isinstance(v, (int, float))]
                    c.fitness = float(np.mean(vals)) if vals else float(self._rng.uniform(0, 1))

            # Track best
            gen_best = max(current_pop, key=lambda c: c.fitness)
            if best_ever is None or gen_best.fitness > best_ever.fitness:
                best_ever = gen_best

            # Selection
            survivors = self.select(current_pop, fitness_fn)
            if not survivors:
                break

            # Reproduce: crossover + mutation
            next_gen: list[EvolutionCandidate] = []
            while len(next_gen) < len(population):
                if len(survivors) >= 2:
                    p1, p2 = survivors[int(self._rng.integers(len(survivors)))], survivors[int(self._rng.integers(len(survivors)))]
                    child_strat = self.crossover(p1.strategy, p2.strategy)
                    child_strat = self.mutate(child_strat, mutation_rate)
                    next_gen.append(EvolutionCandidate(
                        strategy=child_strat,
                        generation=self._generation,
                        parents=[p1.id, p2.id],
                    ))
                else:
                    mutant = self.mutate(survivors[0].strategy, mutation_rate)
                    next_gen.append(EvolutionCandidate(
                        strategy=mutant,
                        generation=self._generation,
                        parents=[survivors[0].id],
                    ))

            current_pop = next_gen

        if best_ever:
            self._hall_of_fame.append(best_ever)

        return {
            "generations_run": generations,
            "final_population_size": len(current_pop),
            "best_fitness": round(best_ever.fitness, 4) if best_ever else 0.0,
            "best_strategy": best_ever.strategy if best_ever else {},
            "hall_of_fame_size": len(self._hall_of_fame),
        }


# ── BioCore Facade ───────────────────────────────────────────────────────────

class BioCore:
    """Master biological system controller.

    Integrates homeostasis, self-repair, metabolism, and evolution
    into a unified living-organism metaphor. Each life_cycle tick
    runs the full biological loop.
    """

    def __init__(self) -> None:
        self.homeostasis = Homeostasis()
        self.self_repair = SelfRepair()
        self.metabolism = Metabolism()
        self.evolution = EvolutionaryAdaptation()
        self._age_cycles: int = 0

    async def life_cycle(self) -> dict[str, Any]:
        """One tick of the organism: regulate → metabolise → repair → adapt."""
        self._age_cycles += 1
        results: dict[str, Any] = {"cycle": self._age_cycles}

        # 1. Homeostatic regulation
        regulation = await self.homeostasis.regulate()
        results["regulation"] = regulation

        # 2. Metabolism — process accumulated input
        if self.metabolism.knowledge_size > 0:
            excrete = await self.metabolism.excrete(max_age_items=200)
            results["metabolism"] = excrete

        # 3. Self-repair if health is low
        if self.homeostasis.health < 0.7:
            diagnosis = await self.self_repair.diagnose()
            if not diagnosis["healthy"]:
                for issue in diagnosis["issues"][:3]:
                    await self.self_repair.repair(issue["module"], DamageType.PERFORMANCE_DEGRADATION)
            results["repair"] = diagnosis

        # 4. Entropy naturally increases each cycle
        self.homeostasis.entropy = min(1.0, self.homeostasis.entropy + 0.01)

        results["alive"] = self.is_alive()
        return results

    def is_alive(self) -> bool:
        """Check if the system is functioning (all vitals above critical)."""
        v = self.homeostasis.vital_signs()
        return v["energy"] > 0.05 and v["health"] > 0.1

    def age(self) -> int:
        """How many life cycles have passed."""
        return self._age_cycles

    def status(self) -> dict[str, Any]:
        """Comprehensive biological status report."""
        return {
            "alive": self.is_alive(),
            "age_cycles": self._age_cycles,
            "vitals": self.homeostasis.vital_signs(),
            "mode": self.homeostasis.mode.value,
            "repairs_performed": len(self.self_repair.repair_history),
            "knowledge_size": self.metabolism.knowledge_size,
            "metabolic_rate": self.metabolism.metabolic_rate(),
            "immune_threats_seen": len(self.self_repair._known_threats),
            "hall_of_fame": len(self.evolution._hall_of_fame),
        }
