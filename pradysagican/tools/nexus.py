"""
Nexus Tool Master — PRADYSAGICAN v2.0
Universal tool management with 40+ capability categories, dynamic tool creation,
tool composition (chaining), MCP-compatible protocol, and performance benchmarking.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

import numpy as np

logger = logging.getLogger(__name__)


# ── Tool Capability Taxonomy (40+ categories) ───────────────────────────────

class ToolCapability(str, Enum):
    # File & Storage
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_SEARCH = "file_search"
    FILE_TRANSFORM = "file_transform"
    ARCHIVE = "archive"

    # Code
    CODE_EXECUTE = "code_execute"
    CODE_ANALYSE = "code_analyse"
    CODE_GENERATE = "code_generate"
    CODE_REFACTOR = "code_refactor"
    CODE_TEST = "code_test"
    CODE_DEBUG = "code_debug"

    # Web & Network
    WEB_FETCH = "web_fetch"
    WEB_SCRAPE = "web_scrape"
    WEB_SEARCH = "web_search"
    API_CALL = "api_call"
    WEBHOOK = "webhook"

    # Data & Analytics
    DATA_QUERY = "data_query"
    DATA_TRANSFORM = "data_transform"
    DATA_VISUALISE = "data_visualise"
    DATA_VALIDATE = "data_validate"
    STATISTICS = "statistics"
    ML_INFERENCE = "ml_inference"

    # Media
    IMAGE_PROCESS = "image_process"
    AUDIO_PROCESS = "audio_process"
    VIDEO_PROCESS = "video_process"
    DOCUMENT_PARSE = "document_parse"
    TEXT_PROCESS = "text_process"

    # System
    SHELL_EXECUTE = "shell_execute"
    PROCESS_MANAGE = "process_manage"
    CRON_SCHEDULE = "cron_schedule"
    ENV_MANAGE = "env_manage"

    # Communication
    EMAIL_SEND = "email_send"
    CHAT_MESSAGE = "chat_message"
    NOTIFICATION = "notification"

    # Security
    ENCRYPT = "encrypt"
    DECRYPT = "decrypt"
    AUTH_VERIFY = "auth_verify"
    AUDIT_LOG = "audit_log"

    # Hardware
    HARDWARE_DETECT = "hardware_detect"
    RESOURCE_MONITOR = "resource_monitor"

    # Meta
    TOOL_CREATE = "tool_create"
    TOOL_COMPOSE = "tool_compose"
    TOOL_BENCHMARK = "tool_benchmark"


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class ToolParameter:
    """A single parameter for a tool."""
    name: str
    param_type: str  # "string" | "number" | "boolean" | "array" | "object"
    description: str = ""
    required: bool = True
    default: Any = None


@dataclass
class Tool:
    """A registered tool with handler, metadata, and performance stats."""
    id: str
    name: str
    description: str
    capabilities: list[ToolCapability]
    handler: Callable[..., Awaitable[Any]]
    parameters: list[ToolParameter] = field(default_factory=list)
    version: str = "1.0.0"
    enabled: bool = True
    # Performance tracking
    invocation_count: int = 0
    total_latency_ms: float = 0.0
    error_count: int = 0
    last_invoked: float | None = None

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.invocation_count, 1)

    @property
    def success_rate(self) -> float:
        total = self.invocation_count
        return (total - self.error_count) / total if total > 0 else 1.0


@dataclass
class ToolResult:
    """Result from a tool execution."""
    tool_id: str
    tool_name: str
    success: bool
    result: Any = None
    error: str | None = None
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class CompositionStep:
    """A step in a tool composition pipeline."""
    tool_name: str
    params: dict[str, Any] = field(default_factory=dict)
    transform_output: Callable[[Any], dict[str, Any]] | None = None
    on_error: str = "stop"  # "stop" | "skip" | "retry"
    max_retries: int = 1


@dataclass
class ToolBenchmark:
    """Performance benchmark result for a tool."""
    tool_name: str
    iterations: int
    mean_latency_ms: float
    std_latency_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    error_rate: float
    throughput_per_sec: float


# ── MCP Protocol Adapter ────────────────────────────────────────────────────

class MCPToolAdapter:
    """Model Context Protocol compatible tool interface.

    Converts Tool objects to/from MCP JSON-Schema format for interoperability
    with Claude, GPT, and other MCP-compatible systems.
    """

    @staticmethod
    def to_mcp_schema(tool: Tool) -> dict[str, Any]:
        """Convert a Tool to MCP-compatible JSON schema."""
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param in tool.parameters:
            properties[param.name] = {
                "type": param.param_type,
                "description": param.description,
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.required:
                required.append(param.name)

        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    @staticmethod
    def from_mcp_schema(
        schema: dict[str, Any],
        handler: Callable[..., Awaitable[Any]],
        capabilities: list[ToolCapability] | None = None,
    ) -> Tool:
        """Create a Tool from an MCP JSON schema."""
        params: list[ToolParameter] = []
        input_schema = schema.get("input_schema", {})
        required_fields = set(input_schema.get("required", []))

        for name, prop in input_schema.get("properties", {}).items():
            params.append(ToolParameter(
                name=name,
                param_type=prop.get("type", "string"),
                description=prop.get("description", ""),
                required=name in required_fields,
                default=prop.get("default"),
            ))

        return Tool(
            id=f"mcp_{uuid.uuid4().hex[:8]}",
            name=schema.get("name", "unknown"),
            description=schema.get("description", ""),
            capabilities=capabilities or [ToolCapability.API_CALL],
            handler=handler,
            parameters=params,
        )


# ── Tool Composer ────────────────────────────────────────────────────────────

class ToolComposer:
    """Chain multiple tools into a pipeline with data flow between steps."""

    def __init__(self) -> None:
        self._pipelines: dict[str, list[CompositionStep]] = {}

    def create_pipeline(
        self,
        name: str,
        steps: list[CompositionStep],
    ) -> str:
        """Register a named pipeline."""
        pipeline_id = f"pipe_{uuid.uuid4().hex[:8]}"
        self._pipelines[pipeline_id] = steps
        logger.info("Pipeline created: %s (%d steps)", name, len(steps))
        return pipeline_id

    async def execute_pipeline(
        self,
        pipeline_id: str,
        registry: dict[str, Tool],
        initial_input: dict[str, Any] | None = None,
    ) -> list[ToolResult]:
        """Execute a pipeline, passing output of each step to the next."""
        steps = self._pipelines.get(pipeline_id, [])
        if not steps:
            return [ToolResult(tool_id="", tool_name="pipeline", success=False, error="Pipeline not found")]

        results: list[ToolResult] = []
        current_input = initial_input or {}

        for step in steps:
            tool = registry.get(step.tool_name)
            if not tool or not tool.enabled:
                if step.on_error == "skip":
                    continue
                results.append(ToolResult(
                    tool_id="", tool_name=step.tool_name,
                    success=False, error=f"Tool '{step.tool_name}' not found or disabled",
                ))
                if step.on_error == "stop":
                    break
                continue

            # Merge step params with pipeline data flow
            merged_params = {**current_input, **step.params}

            start = time.monotonic()
            retries = 0
            success = False
            result_val = None
            error_msg = None

            while retries <= step.max_retries:
                try:
                    result_val = await tool.handler(**merged_params)
                    success = True
                    break
                except Exception as e:
                    error_msg = str(e)
                    retries += 1

            latency = (time.monotonic() - start) * 1000
            tool_result = ToolResult(
                tool_id=tool.id,
                tool_name=tool.name,
                success=success,
                result=result_val,
                error=error_msg if not success else None,
                latency_ms=round(latency, 2),
            )
            results.append(tool_result)

            # Transform output for next step
            if success and step.transform_output and result_val is not None:
                current_input = step.transform_output(result_val)
            elif success and isinstance(result_val, dict):
                current_input = result_val
            else:
                current_input = {"_prev_result": result_val}

            if not success and step.on_error == "stop":
                break

        return results

    @property
    def pipelines(self) -> dict[str, int]:
        return {pid: len(steps) for pid, steps in self._pipelines.items()}


# ── Dynamic Tool Factory ────────────────────────────────────────────────────

class DynamicToolFactory:
    """Create new tools at runtime from specifications.

    Enables the system to invent and register tools on the fly.
    """

    def __init__(self) -> None:
        self._templates: dict[str, dict[str, Any]] = {}

    async def create_tool(
        self,
        name: str,
        description: str,
        capabilities: list[ToolCapability],
        code_body: str | None = None,
        parameter_specs: list[dict[str, Any]] | None = None,
    ) -> Tool:
        """Dynamically create a tool.

        If code_body is provided, wraps it in an async handler.
        Otherwise creates a pass-through handler.
        """
        params = []
        if parameter_specs:
            for spec in parameter_specs:
                params.append(ToolParameter(
                    name=spec.get("name", "input"),
                    param_type=spec.get("type", "string"),
                    description=spec.get("description", ""),
                    required=spec.get("required", True),
                    default=spec.get("default"),
                ))

        if code_body:
            # Create handler from code (sandboxed — exec in limited namespace)
            namespace: dict[str, Any] = {"__builtins__": {"len": len, "str": str, "int": int, "float": float, "list": list, "dict": dict, "range": range, "min": min, "max": max, "sum": sum, "round": round, "abs": abs, "sorted": sorted, "enumerate": enumerate, "zip": zip}}
            try:
                exec(f"async def _handler(**kwargs):\n{_indent(code_body)}", namespace)
                handler = namespace["_handler"]
            except Exception as e:
                logger.warning("Failed to compile dynamic tool '%s': %s", name, e)
                handler = _default_handler
        else:
            handler = _default_handler

        tool = Tool(
            id=f"dyn_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            capabilities=capabilities,
            handler=handler,
            parameters=params,
            version="dynamic",
        )
        logger.info("Dynamic tool created: %s (%d capabilities)", name, len(capabilities))
        return tool

    def register_template(self, template_name: str, spec: dict[str, Any]) -> None:
        """Save a tool template for reuse."""
        self._templates[template_name] = spec

    async def create_from_template(self, template_name: str, overrides: dict[str, Any] | None = None) -> Tool | None:
        """Create a tool from a saved template."""
        spec = self._templates.get(template_name)
        if not spec:
            return None
        merged = {**spec, **(overrides or {})}
        return await self.create_tool(
            name=merged.get("name", template_name),
            description=merged.get("description", ""),
            capabilities=[ToolCapability(c) for c in merged.get("capabilities", ["api_call"])],
            code_body=merged.get("code_body"),
            parameter_specs=merged.get("parameters"),
        )


def _indent(code: str, spaces: int = 4) -> str:
    """Indent every line of code."""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in code.splitlines())


async def _default_handler(**kwargs: Any) -> dict[str, Any]:
    """Default pass-through handler for dynamically created tools."""
    return {"status": "ok", "input": kwargs}


# ── Nexus Tool Master (Façade) ──────────────────────────────────────────────

class NexusToolMaster:
    """Universal Tool Mastery — top-level façade.

    Integrates tool registry, composition, dynamic creation,
    MCP protocol, and performance benchmarking.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._composer = ToolComposer()
        self._factory = DynamicToolFactory()
        self._mcp = MCPToolAdapter()
        self._execution_log: list[ToolResult] = []

    # ── Registration ─────────────────────────────────────────────────────

    def register(self, tool: Tool) -> None:
        """Register a tool in the master registry."""
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s (id=%s)", tool.name, tool.id)

    def register_handler(
        self,
        name: str,
        description: str,
        handler: Callable[..., Awaitable[Any]],
        capabilities: list[ToolCapability] | None = None,
        parameters: list[ToolParameter] | None = None,
    ) -> Tool:
        """Convenience: register from a handler function."""
        tool = Tool(
            id=f"tool_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            capabilities=capabilities or [ToolCapability.API_CALL],
            handler=handler,
            parameters=parameters or [],
        )
        self.register(tool)
        return tool

    # ── Execution ────────────────────────────────────────────────────────

    async def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name, tracking performance."""
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(tool_id="", tool_name=name, success=False, error=f"Tool not found: {name}")
        if not tool.enabled:
            return ToolResult(tool_id=tool.id, tool_name=name, success=False, error=f"Tool disabled: {name}")

        start = time.monotonic()
        try:
            result = await tool.handler(**kwargs)
            latency = (time.monotonic() - start) * 1000
            tool.invocation_count += 1
            tool.total_latency_ms += latency
            tool.last_invoked = time.time()
            tr = ToolResult(tool_id=tool.id, tool_name=name, success=True, result=result, latency_ms=round(latency, 2))
        except Exception as e:
            latency = (time.monotonic() - start) * 1000
            tool.invocation_count += 1
            tool.total_latency_ms += latency
            tool.error_count += 1
            tr = ToolResult(tool_id=tool.id, tool_name=name, success=False, error=str(e), latency_ms=round(latency, 2))

        self._execution_log.append(tr)
        return tr

    # ── Discovery ────────────────────────────────────────────────────────

    def discover(self, capability: ToolCapability | str) -> list[Tool]:
        """Find tools matching a capability."""
        cap_val = capability.value if isinstance(capability, ToolCapability) else capability
        return [t for t in self._tools.values() if any(c.value == cap_val for c in t.capabilities)]

    def search(self, query: str) -> list[Tool]:
        """Keyword search across tool names and descriptions."""
        q = query.lower()
        return [
            t for t in self._tools.values()
            if q in t.name.lower() or q in t.description.lower()
        ]

    def list_tools(self, capability: ToolCapability | None = None) -> list[dict[str, Any]]:
        """List all registered tools, optionally filtered by capability."""
        tools = self._tools.values()
        if capability:
            tools = [t for t in tools if capability in t.capabilities]
        return [
            {
                "name": t.name,
                "description": t.description,
                "capabilities": [c.value for c in t.capabilities],
                "enabled": t.enabled,
                "invocations": t.invocation_count,
                "avg_latency_ms": round(t.avg_latency_ms, 2),
                "success_rate": round(t.success_rate, 3),
            }
            for t in tools
        ]

    # ── Composition ──────────────────────────────────────────────────────

    async def compose_and_run(
        self,
        steps: list[CompositionStep],
        initial_input: dict[str, Any] | None = None,
    ) -> list[ToolResult]:
        """Create and immediately run a pipeline."""
        pid = self._composer.create_pipeline("adhoc", steps)
        return await self._composer.execute_pipeline(pid, self._tools, initial_input)

    # ── Dynamic Creation ─────────────────────────────────────────────────

    async def create_tool(
        self,
        name: str,
        description: str,
        capabilities: list[ToolCapability],
        code_body: str | None = None,
        parameter_specs: list[dict[str, Any]] | None = None,
    ) -> Tool:
        """Dynamically create and register a new tool."""
        tool = await self._factory.create_tool(name, description, capabilities, code_body, parameter_specs)
        self.register(tool)
        return tool

    # ── MCP Protocol ─────────────────────────────────────────────────────

    def export_mcp_schemas(self) -> list[dict[str, Any]]:
        """Export all tools as MCP-compatible JSON schemas."""
        return [self._mcp.to_mcp_schema(t) for t in self._tools.values()]

    async def import_mcp_tool(
        self,
        schema: dict[str, Any],
        handler: Callable[..., Awaitable[Any]],
        capabilities: list[ToolCapability] | None = None,
    ) -> Tool:
        """Import a tool from an MCP schema and register it."""
        tool = self._mcp.from_mcp_schema(schema, handler, capabilities)
        self.register(tool)
        return tool

    # ── Benchmarking ─────────────────────────────────────────────────────

    async def benchmark(
        self,
        tool_name: str,
        iterations: int = 50,
        test_params: dict[str, Any] | None = None,
    ) -> ToolBenchmark:
        """Benchmark a tool's performance over multiple iterations."""
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolBenchmark(
                tool_name=tool_name, iterations=0,
                mean_latency_ms=0, std_latency_ms=0,
                p50_ms=0, p95_ms=0, p99_ms=0,
                error_rate=1.0, throughput_per_sec=0,
            )

        latencies: list[float] = []
        errors = 0
        params = test_params or {}

        total_start = time.monotonic()
        for _ in range(iterations):
            start = time.monotonic()
            try:
                await tool.handler(**params)
            except Exception:
                errors += 1
            latencies.append((time.monotonic() - start) * 1000)
        total_elapsed = time.monotonic() - total_start

        arr = np.array(latencies)
        return ToolBenchmark(
            tool_name=tool_name,
            iterations=iterations,
            mean_latency_ms=round(float(np.mean(arr)), 3),
            std_latency_ms=round(float(np.std(arr)), 3),
            p50_ms=round(float(np.percentile(arr, 50)), 3),
            p95_ms=round(float(np.percentile(arr, 95)), 3),
            p99_ms=round(float(np.percentile(arr, 99)), 3),
            error_rate=round(errors / iterations, 4),
            throughput_per_sec=round(iterations / max(total_elapsed, 0.001), 2),
        )

    # ── Stats ────────────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Overall Nexus system statistics."""
        return {
            "total_tools": len(self._tools),
            "enabled_tools": sum(1 for t in self._tools.values() if t.enabled),
            "total_invocations": sum(t.invocation_count for t in self._tools.values()),
            "total_errors": sum(t.error_count for t in self._tools.values()),
            "pipelines": len(self._composer.pipelines),
            "execution_log_size": len(self._execution_log),
            "capabilities_covered": len(set(
                c for t in self._tools.values() for c in t.capabilities
            )),
        }

    @property
    def composer(self) -> ToolComposer:
        return self._composer

    @property
    def factory(self) -> DynamicToolFactory:
        return self._factory
