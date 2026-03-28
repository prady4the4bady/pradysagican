"""PHASE 20 tests: MCP tool ecosystem."""

from pradysagican.agents.advanced_capabilities import AdvancedAgentCapabilities
from pradysagican.tools.mcp_ecosystem import build_default_mcp_servers, build_default_mcp_tools


def test_default_mcp_servers_count() -> None:
    servers = build_default_mcp_servers()
    assert len(servers) >= 16
    names = {s.server_name for s in servers}
    assert "github" in names
    assert "web-browser" in names


def test_default_mcp_tools_count_and_mapping() -> None:
    tools = build_default_mcp_tools()
    assert len(tools) >= 16
    assert all(t.mcp_server is not None for t in tools)


def test_register_toolset_into_advanced_capabilities() -> None:
    agent = AdvancedAgentCapabilities()
    tools = build_default_mcp_tools()
    added = agent.register_toolset(tools)
    assert added == len(tools)
    assert len(agent.tool_manager.get_all_tools()) >= 16
    status = agent.tool_manager.mcp_servers
    assert "github" in status
    assert "search" in status
