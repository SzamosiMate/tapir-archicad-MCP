import sys
import time
import pytest
from unittest.mock import MagicMock

# ==========================================
# SPEED OPTIMIZATION: Mock search_index in sys.modules
# to prevent heavy ML imports (PyTorch/Faiss) from slowing down test startup
# ==========================================
mock_search_index = MagicMock()
mock_search_index.create_or_load_index = lambda: None
mock_search_index.search_tools = lambda query: []
sys.modules["tapir_archicad_mcp.tools.search_index"] = mock_search_index

from tapir_archicad_mcp.context import multi_conn_instance
from tapir_archicad_mcp.tools.custom.functions import archicad_call_tool
from tapir_archicad_mcp.tools.tool_registry import (
    TOOL_CALLABLE_REGISTRY,
    register_tool_for_dispatch,
)


@pytest.fixture
def fake_tool():
    """
    Registers a dispatchable fake tool for the duration of a test and
    removes it from the registry afterwards.
    """
    registered = []

    def _register(func, name: str) -> None:
        register_tool_for_dispatch(
            func, name=name, title=name, description="test tool"
        )
        registered.append(name)

    yield _register

    for name in registered:
        TOOL_CALLABLE_REGISTRY.pop(name, None)


def test_slow_tool_times_out(monkeypatch, fake_tool):
    """
    With TAPIR_MCP_TOOL_TIMEOUT_S set, a tool call exceeding the limit
    must fail with an actionable error instead of blocking forever.
    """
    monkeypatch.setenv("TAPIR_MCP_TOOL_TIMEOUT_S", "0.1")

    def slow_tool(port: int):
        time.sleep(1)
        return {"done": True}

    fake_tool(slow_tool, "test_slow_tool")

    with pytest.raises(ValueError, match="timed out"):
        archicad_call_tool("test_slow_tool", {"port": 19723})


def test_fast_tool_completes_within_timeout(monkeypatch, fake_tool):
    """
    A tool call finishing within the limit must return its result normally.
    """
    monkeypatch.setenv("TAPIR_MCP_TOOL_TIMEOUT_S", "5")

    def fast_tool(port: int):
        return "done"

    fake_tool(fast_tool, "test_fast_tool")

    result = archicad_call_tool("test_fast_tool", {"port": 19723})
    assert result == {"result": "done"}


def test_timeout_disabled_by_default(monkeypatch, fake_tool):
    """
    Without TAPIR_MCP_TOOL_TIMEOUT_S the previous behaviour is unchanged:
    calls are not raced against a timer.
    """
    monkeypatch.delenv("TAPIR_MCP_TOOL_TIMEOUT_S", raising=False)

    def slowish_tool(port: int):
        time.sleep(0.2)
        return "done"

    fake_tool(slowish_tool, "test_slowish_tool")

    result = archicad_call_tool("test_slowish_tool", {"port": 19723})
    assert result == {"result": "done"}


def test_context_variables_reach_the_tool(monkeypatch, fake_tool):
    """
    Tools read the MultiConn instance from a ContextVar. Running a call
    under a timeout must not lose that context.
    """
    monkeypatch.setenv("TAPIR_MCP_TOOL_TIMEOUT_S", "5")
    sentinel = object()

    def context_tool(port: int):
        return multi_conn_instance.get() is sentinel

    fake_tool(context_tool, "test_context_tool")

    token = multi_conn_instance.set(sentinel)
    try:
        result = archicad_call_tool("test_context_tool", {"port": 19723})
    finally:
        multi_conn_instance.reset(token)

    assert result == {"result": True}


def test_invalid_timeout_value_is_ignored(monkeypatch, fake_tool):
    """
    A malformed TAPIR_MCP_TOOL_TIMEOUT_S must not break tool execution;
    the timeout is simply treated as disabled.
    """
    monkeypatch.setenv("TAPIR_MCP_TOOL_TIMEOUT_S", "not-a-number")

    def fast_tool(port: int):
        return "done"

    fake_tool(fast_tool, "test_invalid_timeout_tool")

    result = archicad_call_tool("test_invalid_timeout_tool", {"port": 19723})
    assert result == {"result": "done"}
