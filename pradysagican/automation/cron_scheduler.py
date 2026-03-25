"""Cron-style task scheduler using APScheduler with JSON persistence."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from pradysagican.config import load_config


class CronScheduler:
    """Feature-flagged cron scheduler for autonomous recurring jobs."""

    def __init__(self) -> None:
        cfg = load_config()
        self._enabled = cfg.upgrades.enable_cron_scheduler and not cfg.upgrades.kill_switch_new_paths
        self._available = False
        self._scheduler = None
        self._jobs_file = Path(os.getenv("PRADY_CRON_JOBS_FILE", "./data/cron_jobs.json"))
        self._jobs_file.parent.mkdir(parents=True, exist_ok=True)
        if self._enabled:
            try:
                from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-not-found]
                self._scheduler = AsyncIOScheduler()
                self._available = True
            except Exception:
                self._available = False

    @property
    def enabled(self) -> bool:
        return self._enabled and self._available and self._scheduler is not None

    def start(self) -> bool:
        if not self.enabled:
            return False
        self._scheduler.start()
        return True

    def shutdown(self) -> None:
        if self.enabled:
            self._scheduler.shutdown(wait=False)

    def add_cron(
        self,
        job_id: str,
        cron_expr: str,
        func: Callable[..., Any],
        args: tuple[Any, ...] | None = None,
    ) -> bool:
        """Add cron job from standard 5-field expression."""
        if not self.enabled or self._scheduler is None:
            return False

        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError("cron_expr must have 5 fields: minute hour day month day_of_week")
        minute, hour, day, month, day_of_week = parts
        self._scheduler.add_job(
            func,
            trigger="cron",
            id=job_id,
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            args=args or (),
            replace_existing=True,
        )
        self._persist_jobs()
        return True

    def list_jobs(self) -> list[dict[str, Any]]:
        if not self.enabled or self._scheduler is None:
            return []
        out: list[dict[str, Any]] = []
        for job in self._scheduler.get_jobs():
            out.append(
                {
                    "id": job.id,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                    "trigger": str(job.trigger),
                }
            )
        return out

    def _persist_jobs(self) -> None:
        data = self.list_jobs()
        with self._jobs_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=True, indent=2)

