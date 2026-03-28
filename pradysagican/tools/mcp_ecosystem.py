"""
PHASE 20: MCP TOOL ECOSYSTEM
============================
Pre-configured registry for 16+ MCP-compatible tool integrations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from pradysagican.agents.advanced_capabilities import ToolDefinition, ToolType


@dataclass
class MCPServerDefinition:
    server_name: str
    endpoint: str
    transport: str = "stdio"
    auth_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


def build_default_mcp_servers() -> List[MCPServerDefinition]:
    return [
        MCPServerDefinition("web-browser", "mcp://browser", metadata={"capability": "web_navigation"}),
        MCPServerDefinition("code-runner", "mcp://code", metadata={"capability": "code_execution"}),
        MCPServerDefinition("filesystem", "mcp://fs", metadata={"capability": "file_ops"}),
        MCPServerDefinition("sql-database", "mcp://db", metadata={"capability": "database_query"}),
        MCPServerDefinition("http-client", "mcp://http", metadata={"capability": "api_calls"}),
        MCPServerDefinition("data-analyzer", "mcp://data", metadata={"capability": "analytics"}),
        MCPServerDefinition("image-tool", "mcp://image", metadata={"capability": "image_processing"}),
        MCPServerDefinition("doc-parser", "mcp://docs", metadata={"capability": "document_processing"}),
        MCPServerDefinition("calendar", "mcp://calendar", metadata={"capability": "scheduling"}),
        MCPServerDefinition("email", "mcp://email", metadata={"capability": "email"}),
        MCPServerDefinition("slack", "mcp://slack", metadata={"capability": "slack"}),
        MCPServerDefinition("github", "mcp://github", metadata={"capability": "repo_ops"}),
        MCPServerDefinition("search", "mcp://search", metadata={"capability": "web_search"}),
        MCPServerDefinition("weather", "mcp://weather", metadata={"capability": "weather"}),
        MCPServerDefinition("news", "mcp://news", metadata={"capability": "news"}),
        MCPServerDefinition("translate", "mcp://translate", metadata={"capability": "translation"}),
    ]


def build_default_mcp_tools() -> List[ToolDefinition]:
    return [
        ToolDefinition(
            name="browse_web",
            description="Navigate and extract structured information from web pages.",
            tool_type=ToolType.WEB_BROWSING,
            parameters={"url": "string", "instruction": "string"},
            required_params=["url"],
            mcp_server="web-browser",
        ),
        ToolDefinition(
            name="run_code",
            description="Execute sandboxed code snippets with isolated runtime.",
            tool_type=ToolType.CODE_EXECUTION,
            parameters={"language": "string", "code": "string"},
            required_params=["language", "code"],
            mcp_server="code-runner",
        ),
        ToolDefinition(
            name="read_file",
            description="Read files from workspace.",
            tool_type=ToolType.FILE_OPERATION,
            parameters={"path": "string"},
            required_params=["path"],
            mcp_server="filesystem",
        ),
        ToolDefinition(
            name="query_database",
            description="Execute parameterized SQL queries.",
            tool_type=ToolType.DATABASE,
            parameters={"query": "string"},
            required_params=["query"],
            mcp_server="sql-database",
        ),
        ToolDefinition(
            name="call_api",
            description="Call external HTTP APIs with method and payload.",
            tool_type=ToolType.API_CALL,
            parameters={"url": "string", "method": "string", "payload": "object"},
            required_params=["url", "method"],
            mcp_server="http-client",
        ),
        ToolDefinition(
            name="analyze_data",
            description="Perform statistical analysis on structured data.",
            tool_type=ToolType.DATA_ANALYSIS,
            parameters={"dataset": "object", "analysis_type": "string"},
            required_params=["dataset"],
            mcp_server="data-analyzer",
        ),
        ToolDefinition(
            name="process_image",
            description="Run OCR, tagging, or transformation on images.",
            tool_type=ToolType.IMAGE_PROCESSING,
            parameters={"image_path": "string", "operation": "string"},
            required_params=["image_path"],
            mcp_server="image-tool",
        ),
        ToolDefinition(
            name="parse_document",
            description="Extract structured sections from documents.",
            tool_type=ToolType.FILE_OPERATION,
            parameters={"path": "string", "format": "string"},
            required_params=["path"],
            mcp_server="doc-parser",
        ),
        ToolDefinition(
            name="schedule_event",
            description="Create or update calendar events.",
            tool_type=ToolType.API_CALL,
            parameters={"title": "string", "datetime": "string"},
            required_params=["title", "datetime"],
            mcp_server="calendar",
        ),
        ToolDefinition(
            name="send_email",
            description="Send transactional or workflow emails.",
            tool_type=ToolType.API_CALL,
            parameters={"to": "string", "subject": "string", "body": "string"},
            required_params=["to", "subject", "body"],
            mcp_server="email",
        ),
        ToolDefinition(
            name="post_slack_message",
            description="Post updates to Slack channels.",
            tool_type=ToolType.API_CALL,
            parameters={"channel": "string", "message": "string"},
            required_params=["channel", "message"],
            mcp_server="slack",
        ),
        ToolDefinition(
            name="github_action",
            description="Run GitHub repository operations.",
            tool_type=ToolType.API_CALL,
            parameters={"repo": "string", "operation": "string"},
            required_params=["repo", "operation"],
            mcp_server="github",
        ),
        ToolDefinition(
            name="search_web",
            description="Perform web search and return summarized links.",
            tool_type=ToolType.SEARCH,
            parameters={"query": "string"},
            required_params=["query"],
            mcp_server="search",
        ),
        ToolDefinition(
            name="get_weather",
            description="Get weather forecast for a location.",
            tool_type=ToolType.API_CALL,
            parameters={"location": "string"},
            required_params=["location"],
            mcp_server="weather",
        ),
        ToolDefinition(
            name="get_news",
            description="Fetch latest news on a topic.",
            tool_type=ToolType.SEARCH,
            parameters={"topic": "string"},
            required_params=["topic"],
            mcp_server="news",
        ),
        ToolDefinition(
            name="translate_text",
            description="Translate text between languages.",
            tool_type=ToolType.API_CALL,
            parameters={"text": "string", "target_language": "string"},
            required_params=["text", "target_language"],
            mcp_server="translate",
        ),
    ]

