"""Model Context Protocol client wrapper for integrating external MCP servers."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MCPToolDefinition:
    name: str
    description: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)


class MCPClient:
    """Thin MCP client with safe fallback when SDK is unavailable."""

    def __init__(self) -> None:
        self._sdk_available = False
        self._client = None
        try:
            # SDK package name may be `mcp`; import lazily and fallback safely.
            import mcp  # type: ignore[import-not-found,unused-ignore]
            self._sdk_available = True
            self._client = mcp
        except Exception as exc:  # pragma: no cover
            logger.warning("MCP SDK unavailable; running in stub mode: %s", exc)
        self._registered: dict[str, MCPToolDefinition] = {}

    def register_tool(self, tool: MCPToolDefinition) -> None:
        self._registered[tool.name] = tool

    def list_tools(self) -> list[MCPToolDefinition]:
        return list(self._registered.values())

    async def invoke(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        args = arguments or {}
        if tool_name not in self._registered:
            return {"ok": False, "error": f"Unknown MCP tool: {tool_name}"}
        if not self._sdk_available or self._client is None:
            return {"ok": True, "mode": "stub", "tool": tool_name, "arguments": args}
        # Placeholder for real client call once server session wiring is added.
        return {"ok": True, "mode": "sdk", "tool": tool_name, "arguments": args}
