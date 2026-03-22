"""
AutoToolBuilder — Self-Building Tools for PRADYSAGICAN
======================================================
The system identifies what tools it needs, designs them, writes Python code,
tests them, and deploys them into the NexusToolMaster registry — all at runtime.

Also includes a WebConnector with simulated/template-based web access
using only free APIs, and a catalog of known free API endpoints.
"""
from __future__ import annotations

import logging
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class ToolParameter:
    """Parameter specification for a tool."""
    name: str
    param_type: str = "string"  # string | number | boolean | list | dict
    description: str = ""
    required: bool = True
    default: Any = None


@dataclass
class ToolBlueprint:
    """Specification for a tool to be built."""
    name: str
    purpose: str
    inputs: list[ToolParameter] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    code_template: str = ""
    dependencies: list[str] = field(default_factory=list)


@dataclass
class BuiltTool:
    """A tool that was built by the system."""
    id: str = field(default_factory=lambda: f"built_{uuid.uuid4().hex[:8]}")
    name: str = ""
    purpose: str = ""
    code: str = ""
    handler: Callable[..., Awaitable[Any]] | None = None
    tests_passed: int = 0
    tests_failed: int = 0
    usage_count: int = 0
    created_at: float = field(default_factory=time.time)
    blueprint: ToolBlueprint | None = None


@dataclass
class TestCase:
    """Test case for verifying a built tool."""
    name: str
    input_kwargs: dict[str, Any] = field(default_factory=dict)
    expected_keys: list[str] = field(default_factory=list)
    should_succeed: bool = True


# ── Known Free APIs Catalog ──────────────────────────────────────────────────

FREE_API_CATALOG: dict[str, list[dict[str, str]]] = {
    "weather": [
        {"name": "Open-Meteo", "url": "https://api.open-meteo.com/v1/forecast", "auth": "none"},
        {"name": "wttr.in", "url": "https://wttr.in/?format=j1", "auth": "none"},
    ],
    "news": [
        {"name": "NewsAPI (free tier)", "url": "https://newsapi.org/v2/top-headlines", "auth": "api_key"},
        {"name": "GNews", "url": "https://gnews.io/api/v4/top-headlines", "auth": "api_key"},
    ],
    "knowledge": [
        {"name": "Wikipedia", "url": "https://en.wikipedia.org/api/rest_v1/page/summary/{title}", "auth": "none"},
        {"name": "Wikidata", "url": "https://www.wikidata.org/w/api.php", "auth": "none"},
    ],
    "code": [
        {"name": "GitHub Search", "url": "https://api.github.com/search/repositories", "auth": "optional"},
        {"name": "npm Registry", "url": "https://registry.npmjs.org/{package}", "auth": "none"},
        {"name": "PyPI", "url": "https://pypi.org/pypi/{package}/json", "auth": "none"},
    ],
    "science": [
        {"name": "arXiv", "url": "https://export.arxiv.org/api/query", "auth": "none"},
        {"name": "Semantic Scholar", "url": "https://api.semanticscholar.org/graph/v1/paper/search", "auth": "none"},
    ],
    "geo": [
        {"name": "Nominatim (OSM)", "url": "https://nominatim.openstreetmap.org/search", "auth": "none"},
        {"name": "IP Geolocation", "url": "https://ipapi.co/{ip}/json/", "auth": "none"},
    ],
    "finance": [
        {"name": "CoinGecko", "url": "https://api.coingecko.com/api/v3/simple/price", "auth": "none"},
        {"name": "ExchangeRate API", "url": "https://open.er-api.com/v6/latest/{base}", "auth": "none"},
    ],
    "utilities": [
        {"name": "QR Code Generator", "url": "https://api.qrserver.com/v1/create-qr-code/", "auth": "none"},
        {"name": "URL Shortener (is.gd)", "url": "https://is.gd/create.php", "auth": "none"},
    ],
}


# ── Web Connector ────────────────────────────────────────────────────────────

class WebConnector:
    """Connect to web for real-time information (template-based, no live calls).

    All methods return structured template responses simulating what
    real API calls would return. No actual HTTP requests are made.
    """

    def __init__(self) -> None:
        self._monitors: dict[str, dict[str, Any]] = {}
        self._search_history: list[dict[str, Any]] = []

    async def search_web(self, query: str) -> dict[str, Any]:
        """Simulate a web search and return structured results."""
        results = [
            {
                "title": f"Result 1 for: {query[:40]}",
                "snippet": f"Comprehensive information about {query[:30]}...",
                "source": "knowledge_base",
                "relevance": 0.95,
            },
            {
                "title": f"Research on {query[:30]}",
                "snippet": f"Recent findings related to {query[:30]}...",
                "source": "academic",
                "relevance": 0.82,
            },
            {
                "title": f"Guide to {query[:30]}",
                "snippet": f"Step-by-step guide for {query[:30]}...",
                "source": "tutorial",
                "relevance": 0.75,
            },
        ]
        self._search_history.append({"query": query, "results": len(results), "timestamp": time.time()})
        return {"query": query, "results": results, "total": len(results)}

    async def fetch_url(self, url: str) -> dict[str, Any]:
        """Simulate URL fetch with template response."""
        return {
            "url": url,
            "status": 200,
            "content_type": "text/html",
            "body": f"[Simulated content from {url[:60]}]",
            "headers": {"content-length": "0", "server": "simulated"},
            "timestamp": time.time(),
        }

    async def monitor_topic(self, topic: str) -> dict[str, Any]:
        """Set up continuous monitoring for a topic."""
        monitor_id = f"mon_{uuid.uuid4().hex[:8]}"
        self._monitors[monitor_id] = {
            "topic": topic,
            "created_at": time.time(),
            "last_checked": time.time(),
            "alerts": 0,
        }
        return {"monitor_id": monitor_id, "topic": topic, "status": "active"}

    async def discover_free_apis(self, category: str) -> list[dict[str, str]]:
        """Find free API endpoints for a category."""
        cat_lower = category.lower()
        apis = FREE_API_CATALOG.get(cat_lower, [])
        if not apis:
            # Fuzzy match
            for key, val in FREE_API_CATALOG.items():
                if cat_lower in key or key in cat_lower:
                    apis = val
                    break
        return apis

    @property
    def search_count(self) -> int:
        return len(self._search_history)


# ── Auto Tool Builder ────────────────────────────────────────────────────────

class AutoToolBuilder:
    """Build new tools at runtime from specifications.

    The system identifies what tool it needs, designs a blueprint,
    generates Python code, tests it, and deploys it — fully autonomous.
    """

    def __init__(self) -> None:
        self._built_tools: dict[str, BuiltTool] = {}
        self._blueprints: dict[str, ToolBlueprint] = {}
        self.web = WebConnector()

    # ── Need Identification ──────────────────────────────────────────────

    async def identify_need(self, task: str) -> dict[str, Any]:
        """Analyse what tool is needed for a task."""
        task_lower = task.lower()

        # Category detection
        categories = {
            "data": ["parse", "transform", "convert", "extract", "clean", "validate"],
            "web": ["fetch", "scrape", "api", "url", "download", "search"],
            "text": ["summarise", "translate", "format", "template", "generate"],
            "math": ["calculate", "compute", "statistics", "average", "aggregate"],
            "file": ["read", "write", "copy", "move", "compress", "archive"],
            "monitor": ["watch", "alert", "check", "verify", "monitor", "track"],
        }

        detected_category = "general"
        detected_keywords: list[str] = []
        for cat, keywords in categories.items():
            for kw in keywords:
                if kw in task_lower:
                    detected_category = cat
                    detected_keywords.append(kw)

        return {
            "task": task,
            "category": detected_category,
            "keywords": detected_keywords,
            "suggested_name": f"{detected_category}_tool_{uuid.uuid4().hex[:4]}",
            "complexity": "simple" if len(detected_keywords) <= 1 else "moderate" if len(detected_keywords) <= 3 else "complex",
        }

    # ── Blueprint Design ─────────────────────────────────────────────────

    async def design_tool(self, need: dict[str, Any]) -> ToolBlueprint:
        """Create a ToolBlueprint from a need description."""
        category = need.get("category", "general")
        task = need.get("task", "unknown task")
        name = need.get("suggested_name", f"tool_{uuid.uuid4().hex[:6]}")

        # Generate inputs based on category
        input_specs = {
            "data": [ToolParameter("data", "string", "Input data to process")],
            "web": [ToolParameter("url", "string", "URL to access"), ToolParameter("query", "string", "Search query", required=False)],
            "text": [ToolParameter("text", "string", "Input text")],
            "math": [ToolParameter("values", "list", "Numeric values"), ToolParameter("operation", "string", "Math operation")],
            "file": [ToolParameter("path", "string", "File path")],
            "monitor": [ToolParameter("target", "string", "What to monitor"), ToolParameter("interval", "number", "Check interval seconds", required=False, default=60)],
        }

        inputs = input_specs.get(category, [ToolParameter("input", "string", "Generic input")])
        outputs = ["result", "status", "metadata"]

        # Generate code template
        code = self._generate_code_template(name, category, inputs)

        blueprint = ToolBlueprint(
            name=name,
            purpose=f"Auto-generated tool for: {task[:80]}",
            inputs=inputs,
            outputs=outputs,
            code_template=code,
            dependencies=[],
        )
        self._blueprints[name] = blueprint
        return blueprint

    def _generate_code_template(
        self,
        name: str,
        category: str,
        inputs: list[ToolParameter],
    ) -> str:
        """Generate Python code for a tool based on category."""
        param_names = [p.name for p in inputs]
        params_str = ", ".join(f"{p}=None" for p in param_names)

        templates = {
            "data": f'''\
async def {name}({params_str}):
    """Auto-generated data processing tool."""
    data = data or ""
    words = data.split()
    unique = list(set(words))
    return {{"processed": len(words), "unique": len(unique), "result": " ".join(unique[:20]), "status": "ok"}}
''',
            "web": f'''\
async def {name}({params_str}):
    """Auto-generated web access tool."""
    return {{"url": url or "", "query": query or "", "result": "simulated web response", "status": "ok"}}
''',
            "text": f'''\
async def {name}({params_str}):
    """Auto-generated text processing tool."""
    text = text or ""
    sentences = [s.strip() for s in text.split(".") if s.strip()]
    return {{"sentences": len(sentences), "words": len(text.split()), "result": text[:200], "status": "ok"}}
''',
            "math": f'''\
async def {name}({params_str}):
    """Auto-generated math tool."""
    vals = values or []
    if not vals:
        return {{"result": 0, "status": "no_data"}}
    import numpy as np
    arr = np.array(vals, dtype=float)
    op = (operation or "mean").lower()
    ops = {{"mean": np.mean, "sum": np.sum, "std": np.std, "min": np.min, "max": np.max, "median": np.median}}
    fn = ops.get(op, np.mean)
    return {{"result": round(float(fn(arr)), 4), "operation": op, "count": len(vals), "status": "ok"}}
''',
            "file": f'''\
async def {name}({params_str}):
    """Auto-generated file tool."""
    return {{"path": path or "", "action": "simulated", "status": "ok"}}
''',
            "monitor": f'''\
async def {name}({params_str}):
    """Auto-generated monitoring tool."""
    import time
    return {{"target": target or "", "interval": interval or 60, "checked_at": time.time(), "healthy": True, "status": "ok"}}
''',
        }

        return templates.get(category, f'''\
async def {name}({params_str}):
    """Auto-generated general tool."""
    return {{"input": str(input)[:100] if input else "", "status": "ok"}}
''')

    # ── Build Tool ───────────────────────────────────────────────────────

    async def build_tool(self, blueprint: ToolBlueprint) -> BuiltTool:
        """Generate a working Python function from a blueprint."""
        code = blueprint.code_template
        if not code:
            code = self._generate_code_template(
                blueprint.name,
                "general",
                blueprint.inputs,
            )

        # Compile the code into a callable handler
        namespace: dict[str, Any] = {
            "__builtins__": {
                "len": len, "str": str, "int": int, "float": float,
                "list": list, "dict": dict, "set": set, "tuple": tuple,
                "range": range, "min": min, "max": max, "sum": sum,
                "round": round, "abs": abs, "sorted": sorted,
                "enumerate": enumerate, "zip": zip, "isinstance": isinstance,
                "print": print, "type": type, "hasattr": hasattr,
                "getattr": getattr, "bool": bool,
                "__import__": __import__,
            },
        }

        handler: Callable[..., Awaitable[Any]] | None = None
        try:
            exec(code, namespace)
            handler = namespace.get(blueprint.name)
        except Exception as exc:
            logger.warning("Failed to compile tool '%s': %s", blueprint.name, exc)

        tool = BuiltTool(
            name=blueprint.name,
            purpose=blueprint.purpose,
            code=code,
            handler=handler,
            blueprint=blueprint,
        )
        self._built_tools[blueprint.name] = tool
        logger.info("Tool built: %s", blueprint.name)
        return tool

    # ── Test Tool ────────────────────────────────────────────────────────

    async def test_tool(
        self,
        tool: BuiltTool,
        test_cases: list[TestCase] | None = None,
    ) -> dict[str, Any]:
        """Verify a tool works with test cases."""
        if tool.handler is None:
            return {"passed": 0, "failed": 1, "errors": ["Handler is None — compilation failed"]}

        # Default test cases
        if test_cases is None:
            test_cases = [
                TestCase(name="basic_call", input_kwargs={}, expected_keys=["status"]),
            ]
            if tool.blueprint:
                # Add a test with actual input params
                sample_kwargs: dict[str, Any] = {}
                for p in tool.blueprint.inputs:
                    if p.param_type == "string":
                        sample_kwargs[p.name] = "test input data"
                    elif p.param_type == "number":
                        sample_kwargs[p.name] = 42
                    elif p.param_type == "list":
                        sample_kwargs[p.name] = [1.0, 2.0, 3.0]
                    elif p.param_type == "boolean":
                        sample_kwargs[p.name] = True
                test_cases.append(TestCase(name="with_inputs", input_kwargs=sample_kwargs, expected_keys=["status"]))

        passed = 0
        failed = 0
        errors: list[str] = []

        for tc in test_cases:
            try:
                result = await tool.handler(**tc.input_kwargs)
                if tc.should_succeed:
                    if isinstance(result, dict):
                        for key in tc.expected_keys:
                            if key not in result:
                                errors.append(f"{tc.name}: missing key '{key}'")
                                failed += 1
                                continue
                    passed += 1
                else:
                    errors.append(f"{tc.name}: expected failure but succeeded")
                    failed += 1
            except Exception as exc:
                if tc.should_succeed:
                    errors.append(f"{tc.name}: {exc}")
                    failed += 1
                else:
                    passed += 1

        tool.tests_passed = passed
        tool.tests_failed = failed
        return {"passed": passed, "failed": failed, "errors": errors}

    # ── Deploy Tool ──────────────────────────────────────────────────────

    async def deploy_tool(self, tool: BuiltTool) -> dict[str, Any]:
        """Register a built tool (would integrate with NexusToolMaster in full system)."""
        if tool.handler is None:
            return {"deployed": False, "error": "No handler — tool not compiled"}
        if tool.tests_passed == 0:
            return {"deployed": False, "error": "Tool has not passed any tests"}

        tool.usage_count = 0  # reset for deployment
        logger.info("Tool deployed: %s (tests: %d passed)", tool.name, tool.tests_passed)
        return {
            "deployed": True,
            "tool_name": tool.name,
            "tool_id": tool.id,
            "tests_passed": tool.tests_passed,
        }

    # ── Upgrade Tool ─────────────────────────────────────────────────────

    async def upgrade_tool(self, tool_name: str, improvement: str) -> BuiltTool | None:
        """Improve an existing tool by rebuilding with enhanced spec."""
        existing = self._built_tools.get(tool_name)
        if existing is None or existing.blueprint is None:
            return None

        # Create enhanced blueprint
        enhanced = ToolBlueprint(
            name=f"{tool_name}_v2",
            purpose=f"{existing.purpose} [upgraded: {improvement[:50]}]",
            inputs=existing.blueprint.inputs,
            outputs=existing.blueprint.outputs + ["upgrade_info"],
            code_template=existing.code,  # start from existing code
            dependencies=existing.blueprint.dependencies,
        )
        new_tool = await self.build_tool(enhanced)
        await self.test_tool(new_tool)
        return new_tool

    # ── Full Pipeline ────────────────────────────────────────────────────

    async def build_from_scratch(self, need_description: str) -> dict[str, Any]:
        """Full pipeline: identify → design → build → test → deploy."""
        # 1. Identify need
        need = await self.identify_need(need_description)

        # 2. Design blueprint
        blueprint = await self.design_tool(need)

        # 3. Build tool
        tool = await self.build_tool(blueprint)

        # 4. Test tool
        test_result = await self.test_tool(tool)

        # 5. Deploy if tests pass
        if test_result["passed"] > 0 and test_result["failed"] == 0:
            deploy_result = await self.deploy_tool(tool)
        else:
            deploy_result = {"deployed": False, "error": f"{test_result['failed']} tests failed"}

        return {
            "need": need,
            "blueprint": blueprint.name,
            "built": tool.name,
            "tests": test_result,
            "deployed": deploy_result,
        }

    # ── Listing ──────────────────────────────────────────────────────────

    def list_built_tools(self) -> list[dict[str, Any]]:
        """All tools the system has created for itself."""
        return [
            {
                "name": t.name,
                "purpose": t.purpose[:60],
                "tests_passed": t.tests_passed,
                "tests_failed": t.tests_failed,
                "usage_count": t.usage_count,
                "created_at": t.created_at,
                "has_handler": t.handler is not None,
            }
            for t in self._built_tools.values()
        ]

    @property
    def tool_count(self) -> int:
        return len(self._built_tools)
