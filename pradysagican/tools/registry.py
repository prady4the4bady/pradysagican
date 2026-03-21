"""Universal Tool Registry — PRADYSAGICAN. MCP-compatible."""
from __future__ import annotations
import logging, asyncio
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)

@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., Awaitable[Any]]
    parameters: dict[str, Any] = field(default_factory=dict)
    category: str = "general"
    enabled: bool = True

class ToolRegistry:
    """Central registry for all tools. Supports dynamic discovery and composition."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, name: str, description: str, handler: Callable[..., Awaitable[Any]], parameters: dict | None = None, category: str = "general") -> None:
        self._tools[name] = ToolSpec(name=name, description=description, handler=handler, parameters=parameters or {}, category=category)
        logger.info("Tool registered: %s (%s)", name, category)

    async def execute(self, name: str, **kwargs: Any) -> Any:
        """Execute a registered tool."""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        if not tool.enabled:
            raise RuntimeError(f"Tool disabled: {name}")
        return await tool.handler(**kwargs)

    def discover(self, capability: str) -> list[ToolSpec]:
        """Find tools matching a capability description."""
        cap_lower = capability.lower()
        return [t for t in self._tools.values() if cap_lower in t.description.lower() or cap_lower in t.name.lower()]

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": t.name, "description": t.description, "category": t.category} for t in self._tools.values()]

    async def compose(self, tool_chain: list[tuple[str, dict]]) -> list[Any]:
        """Execute a pipeline of tools in sequence."""
        results = []
        for name, params in tool_chain:
            result = await self.execute(name, **params)
            results.append(result)
        return results
