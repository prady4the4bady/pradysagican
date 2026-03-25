"""Upgrade manager to report feature status and rollout state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from pradysagican.config import load_config
from pradysagican.upgrades.catalog import FEATURES_51, OMEGA_PART2_FEATURES, UpgradeFeature
from pradysagican.godlayer.registry import inventory_summary


@dataclass
class UpgradeFeatureStatus:
    feature_id: str
    name: str
    workstream: str
    benchmark_link: str
    status: str


class UpgradeManager:
    """Reports progress against the unified upgrade tracker and exposes rollout controls."""

    def __init__(self) -> None:
        self._cfg = load_config()

    @staticmethod
    def _range_ids(prefix: str, start: int, end: int) -> set[str]:
        return {f"{prefix}{i:02d}" for i in range(start, end + 1)}

    def _status_for_core(self, f: UpgradeFeature) -> str:
        done_ids = {
            "F01", "F03", "F06", "F07", "F08", "F10", "F14", "F17", "F18",
            "F21", "F24", "F27", "F29", "F31", "F37", "F38", "F41", "F42",
            "F46", "F48",
        }
        in_progress_ids = {
            "F02", "F04", "F12", "F15", "F16", "F22", "F30", "F32", "F33", "F34",
            "F35", "F36", "F39", "F40", "F43", "F44", "F45", "F47", "F49", "F50", "F51",
        }
        if f.feature_id in done_ids:
            return "done"
        if f.feature_id in in_progress_ids:
            return "in_progress"
        return "planned"

    def _status_for_omega(self, f: UpgradeFeature) -> str:
        done_ids = self._range_ids("O", 1, 75)
        in_progress_ids: set[str] = set()
        if f.feature_id in done_ids:
            return "done"
        if f.feature_id in in_progress_ids:
            return "in_progress"
        return "planned"

    def feature_tracker(self) -> list[UpgradeFeatureStatus]:
        return [
            UpgradeFeatureStatus(
                feature_id=f.feature_id,
                name=f.name,
                workstream=f.workstream,
                benchmark_link=f.benchmark_link,
                status=self._status_for_core(f),
            )
            for f in FEATURES_51
        ]

    def omega_feature_tracker(self) -> list[UpgradeFeatureStatus]:
        return [
            UpgradeFeatureStatus(
                feature_id=f.feature_id,
                name=f.name,
                workstream=f.workstream,
                benchmark_link=f.benchmark_link,
                status=self._status_for_omega(f),
            )
            for f in OMEGA_PART2_FEATURES
        ]

    def summary(self) -> dict[str, Any]:
        tracker = self.feature_tracker()
        omega_tracker = self.omega_feature_tracker()
        done = sum(1 for t in tracker if t.status == "done")
        in_progress = sum(1 for t in tracker if t.status == "in_progress")
        planned = sum(1 for t in tracker if t.status == "planned")
        omega_done = sum(1 for t in omega_tracker if t.status == "done")
        omega_in_progress = sum(1 for t in omega_tracker if t.status == "in_progress")
        omega_planned = sum(1 for t in omega_tracker if t.status == "planned")
        return {
            "rollout_stage": self._cfg.upgrades.rollout_stage,
            "benchmark_mode": self._cfg.benchmark_governance.mode,
            "kill_switch_new_paths": self._cfg.upgrades.kill_switch_new_paths,
            "counts": {
                "done": done,
                "in_progress": in_progress,
                "planned": planned,
                "total": len(tracker),
            },
            "omega_counts": {
                "done": omega_done,
                "in_progress": omega_in_progress,
                "planned": omega_planned,
                "total": len(omega_tracker),
            },
            "godlayer_inventory": inventory_summary(),
        }

    def as_dict(self) -> dict[str, Any]:
        tracker = [asdict(t) for t in self.feature_tracker()]
        omega_tracker = [asdict(t) for t in self.omega_feature_tracker()]
        return {"summary": self.summary(), "features": tracker, "omega_features": omega_tracker}
