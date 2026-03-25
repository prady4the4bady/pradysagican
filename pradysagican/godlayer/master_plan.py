"""Master implementation planning layer for full God-layer rollout."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pradysagican.godlayer.registry import INVENTED_TOOL_SPECS


@dataclass(frozen=True)
class CapabilityPlanItem:
    """Single capability item in the rollout master plan."""

    capability_id: int
    name: str
    tier: int
    status: str = "planned"
    dependencies: tuple[int, ...] = field(default_factory=tuple)


@dataclass
class GodLayerMasterPlanner:
    """Maintains full 500-capability rollout plan integrated with runtime."""

    total_capabilities: int = 500
    _items: list[CapabilityPlanItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self._items:
            return

        # Seed with implemented invented specs from the registry.
        for idx, spec in enumerate(INVENTED_TOOL_SPECS, start=1):
            self._items.append(
                CapabilityPlanItem(
                    capability_id=idx,
                    name=spec.tool_name,
                    tier=self._infer_tier(idx),
                    status="prototype" if spec.maturity == "prototype" else "planned",
                    dependencies=self._base_dependencies(idx),
                )
            )

        # Fill to full 500 as planned capabilities for roadmap completeness.
        for idx in range(len(self._items) + 1, self.total_capabilities + 1):
            self._items.append(
                CapabilityPlanItem(
                    capability_id=idx,
                    name=f"GodLayerCapability{idx:03d}",
                    tier=self._infer_tier(idx),
                    status="planned",
                    dependencies=self._base_dependencies(idx),
                )
            )

    @staticmethod
    def _infer_tier(capability_id: int) -> int:
        if capability_id <= 100:
            return 1
        if capability_id <= 200:
            return 2
        if capability_id <= 300:
            return 3
        if capability_id <= 400:
            return 4
        return 5

    @staticmethod
    def _base_dependencies(capability_id: int) -> tuple[int, ...]:
        if capability_id <= 5:
            return ()
        # Keep dependency graph simple and acyclic: each capability depends on the previous checkpoint.
        checkpoint = ((capability_id - 1) // 5) * 5
        return (checkpoint,) if checkpoint > 0 else ()

    def items(self) -> list[CapabilityPlanItem]:
        return list(self._items)

    def by_tier(self, tier: int) -> list[CapabilityPlanItem]:
        return [item for item in self._items if item.tier == tier]

    def next_batch(self, tier: int, limit: int = 10) -> list[CapabilityPlanItem]:
        planned = [item for item in self.by_tier(tier) if item.status in {"planned", "prototype"}]
        return planned[: max(1, limit)]

    def summary(self) -> dict[str, Any]:
        by_tier: dict[int, int] = {}
        by_status: dict[str, int] = {}
        for item in self._items:
            by_tier[item.tier] = by_tier.get(item.tier, 0) + 1
            by_status[item.status] = by_status.get(item.status, 0) + 1
        return {
            "total_capabilities": len(self._items),
            "target_capabilities": self.total_capabilities,
            "coverage_complete": len(self._items) == self.total_capabilities,
            "by_tier": by_tier,
            "by_status": by_status,
        }

    def execution_frame(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "next_tier_1_batch": [item.capability_id for item in self.next_batch(tier=1, limit=10)],
            "next_tier_2_batch": [item.capability_id for item in self.next_batch(tier=2, limit=10)],
        }

