from __future__ import annotations

import pytest

from kuksa_mcp_server.server import create_server


@pytest.fixture
def server():
    return create_server()


def test_tools_are_registered(server):
    """Verify all expected tools are registered with correct names."""
    tools = server._tool_manager.list_tools()
    names = {t.name for t in tools}
    expected = {"get_signal", "get_signals", "set_signal", "list_signals", "count_signals", "server_info"}
    assert expected.issubset(names), f"Missing tools: {expected - names}"


def test_tool_has_description(server):
    """Each tool should have a non-empty description."""
    for tool in server._tool_manager.list_tools():
        assert tool.description, f"Tool '{tool.name}' has no description"


def test_tool_input_schemas(server):
    """Verify tool input schemas include expected parameters."""
    tools = {t.name: t for t in server._tool_manager.list_tools()}
    assert "path" in tools["get_signal"].parameters.get("properties", {})
    assert "paths" in tools["get_signals"].parameters.get("properties", {})
    assert "path" in tools["set_signal"].parameters.get("properties", {})
    assert "branch" in tools["list_signals"].parameters.get("properties", {})
