"""Tool systems: registry, automation, computer use, nexus."""
from pradysagican.tools.registry import ToolRegistry
from pradysagican.tools.automation import AutomationEngine
from pradysagican.tools.nexus import NexusToolMaster, ToolCapability, Tool, ToolComposer, DynamicToolFactory, MCPToolAdapter
from pradysagican.tools.mcp_client import MCPClient, MCPToolDefinition
from pradysagican.tools.web_crawler import WebCrawlerTool
from pradysagican.tools.code_executor_e2b import E2BCodeExecutor
from pradysagican.tools.dom_extractor import DOMExtractor
from pradysagican.tools.shell_executor import ShellExecutor, ShellHistoryManager
__all__ = [
    "ToolRegistry", "AutomationEngine",
    "NexusToolMaster", "ToolCapability", "Tool", "ToolComposer", "DynamicToolFactory", "MCPToolAdapter",
    "MCPClient", "MCPToolDefinition", "WebCrawlerTool", "E2BCodeExecutor", "DOMExtractor",
    "ShellExecutor", "ShellHistoryManager",
]
