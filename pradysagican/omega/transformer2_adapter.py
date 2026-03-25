"""Transformer²-inspired task-adaptive SVD component routing scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class TaskEmbedder:
    """Task-type embedding placeholder."""

    def embed(self, task: str) -> list[float]:
        # Tiny deterministic pseudo-embedding.
        length = max(1, len(task))
        return [round((sum(ord(c) for c in task) % 997) / 997.0, 6), round((length % 127) / 127.0, 6)]


@dataclass
class ComponentLibrary:
    """Stores task-specific component sets."""

    components: dict[str, list[str]] = field(default_factory=dict)

    def register(self, task_type: str, component_ids: list[str]) -> None:
        self.components[task_type] = component_ids

    def for_task(self, task_type: str) -> list[str]:
        return self.components.get(task_type, [])


class SVDTaskAdapter:
    """Maps task embedding to component IDs."""

    def __init__(self, library: ComponentLibrary | None = None) -> None:
        self._library = library or ComponentLibrary()
        if not self._library.components:
            self._library.register("code", ["svd_code_1", "svd_code_2"])
            self._library.register("math", ["svd_math_1", "svd_math_2"])
            self._library.register("science", ["svd_science_1"])
            self._library.register("language", ["svd_lang_1"])

    def select(self, task_type: str) -> list[str]:
        return self._library.for_task(task_type)


class InferenceTimeWeightSwitch:
    """Tracks active component set used at inference."""

    def __init__(self) -> None:
        self.active_components: list[str] = []

    def switch(self, component_ids: list[str]) -> dict[str, Any]:
        self.active_components = list(component_ids)
        return {"switched": True, "active_components": self.active_components}

