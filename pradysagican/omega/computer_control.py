"""Universal computer-control scaffolds for desktop/browser automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class MultimodalScreenReader:
    def analyze(self, screenshot_text: str) -> dict[str, Any]:
        return {"elements": [{"label": "submit", "type": "button"}], "raw": screenshot_text[:300]}


class AccessibilityTreeParser:
    def parse(self, tree: dict[str, Any]) -> list[dict[str, Any]]:
        return tree.get("nodes", []) if isinstance(tree, dict) else []


class ActionGrounder:
    def ground(self, intent: str, elements: list[dict[str, Any]]) -> dict[str, Any]:
        for el in elements:
            if intent.lower() in str(el).lower():
                return {"action": "click", "target": el}
        return {"action": "noop", "target": None}


class BrowserController:
    async def open(self, url: str) -> dict[str, Any]:
        return {"ok": True, "url": url, "mode": "playwright_stub"}


class DesktopController:
    async def click(self, x: int, y: int) -> dict[str, Any]:
        return {"ok": True, "x": x, "y": y, "mode": "desktop_stub"}


class TaskScheduledActions:
    def __init__(self) -> None:
        self._tasks: list[dict[str, Any]] = []

    def add(self, task: dict[str, Any]) -> None:
        self._tasks.append(task)

    def list(self) -> list[dict[str, Any]]:
        return list(self._tasks)


class ErrorRecoveryFlow:
    def recover(self, error: str, context: dict[str, Any]) -> dict[str, Any]:
        return {"replanned": True, "error": error, "context_keys": list(context.keys())}


@dataclass
class SelfOperatingComputer:
    screen_reader: MultimodalScreenReader = MultimodalScreenReader()
    tree_parser: AccessibilityTreeParser = AccessibilityTreeParser()
    grounder: ActionGrounder = ActionGrounder()
    browser: BrowserController = BrowserController()
    desktop: DesktopController = DesktopController()
    recovery: ErrorRecoveryFlow = ErrorRecoveryFlow()

    async def execute_intent(self, intent: str, ui_snapshot: dict[str, Any]) -> dict[str, Any]:
        elements = self.tree_parser.parse(ui_snapshot)
        action = self.grounder.ground(intent, elements)
        if action.get("action") == "click" and action.get("target"):
            target = action["target"]
            return await self.desktop.click(int(target.get("x", 0)), int(target.get("y", 0)))
        return {"ok": True, "action": "noop", "reason": "no_target_found"}

