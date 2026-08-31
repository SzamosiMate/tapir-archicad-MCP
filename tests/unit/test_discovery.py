from __future__ import annotations
from types import SimpleNamespace
from unittest.mock import Mock
from typing import Any
import pytest

from multiconn_archicad.basic_types import (
    APIResponseError,
    ProductInfo,
    SoloProjectID,
    TeamworkProjectID,
    TeamworkCredentials,
    UntitledProjectID,
    TapirInfo,
    Port,
)
from multiconn_archicad.constants import SUPPORTED_TAPIR_VERSION
from multiconn_archicad.errors import AddOnCommandUnavailable

from tapir_archicad_mcp.context import multi_conn_instance
from tapir_archicad_mcp.tools.custom.functions import (
    list_active_archicads,
    archicad_list_commands,
    archicad_get_command_schema,
    archicad_call_tool,
)
from tapir_archicad_mcp.tools.custom.models import (
    CommandOverview,
    CommandSchema,
    DiscoveryResult,
)
from tapir_archicad_mcp.tools.tool_registry import register_tool_for_dispatch


# ============================================================================
# Helpers & Fixtures
# ============================================================================


def make_header(
    project_id=SoloProjectID(projectName="House", projectPath="/p/house.pln"),
    version: str | None = SUPPORTED_TAPIR_VERSION,
    is_installed: bool = True,
    product_info=ProductInfo(version=28, buildNumber=3001, languageCode="INT"),
):
    if is_installed and version:
        tapir = TapirInfo(version=version, is_installed=True)
    else:
        tapir = TapirInfo.not_installed()

    return SimpleNamespace(
        product_info=product_info,
        archicad_id=project_id,
        tapir_info=tapir,
    )


@pytest.fixture
def set_multi_conn():
    tokens = []

    def _set(headers: dict[int, Any]) -> None:
        typed = {Port(p): h for p, h in headers.items()}
        mc = SimpleNamespace(
            refresh=SimpleNamespace(all_ports=Mock()),
            connect=SimpleNamespace(all=Mock()),
            open_port_headers=typed,
            open_ports=list(typed.keys()),
            active=typed,
        )
        tokens.append(multi_conn_instance.set(mc))

    yield _set

    for token in tokens:
        multi_conn_instance.reset(token)


# ============================================================================
# 1. Command & Schema Discovery Tests
# ============================================================================


def test_archicad_list_commands(fake_archicad):
    commands = archicad_list_commands()

    assert isinstance(commands, list)
    assert len(commands) > 0

    first_cmd = commands[0]
    assert isinstance(first_cmd, CommandOverview)
    assert first_cmd.name and first_cmd.description

    all_names = [cmd.name for cmd in commands]
    assert "elements_get_selected_elements" in all_names
    assert "elements_create_slabs" in all_names


def test_archicad_get_command_schema_valid(fake_archicad):
    schema_result = archicad_get_command_schema("elements_get_selected_elements")

    assert isinstance(schema_result, CommandSchema)
    assert schema_result.name == "elements_get_selected_elements"
    assert schema_result.input_schema["type"] == "object"
    assert "port" in schema_result.input_schema["properties"]
    assert "port" in schema_result.input_schema["required"]


def test_archicad_get_command_schema_invalid(fake_archicad):
    with pytest.raises(ValueError, match="not found. Please use 'archicad_list_commands'"):
        archicad_get_command_schema("made_up_command_name")


# ============================================================================
# 2. Instance Discovery & Version Checking Tests
# ============================================================================


def test_empty_instance_discovery(set_multi_conn):
    set_multi_conn({})
    result = list_active_archicads()
    assert isinstance(result, DiscoveryResult)
    assert result.active == [] and result.unavailable == []


@pytest.mark.parametrize(
    "project_id, expected_type, expected_path",
    [
        (SoloProjectID(projectName="House", projectPath="/p/h.pln"), "solo", "/p/h.pln"),
        (
            TeamworkProjectID(
                projectName="Tower",
                projectPath="P/Tower",
                serverAddress="https://bim.local",
                teamworkCredentials=TeamworkCredentials(username="user"),
            ),
            "teamwork",
            "teamwork://https://bim.local/P/Tower",
        ),
        (UntitledProjectID(), "untitled", None),
    ],
)
def test_healthy_instances_and_project_types(set_multi_conn, project_id, expected_type, expected_path):
    set_multi_conn({19723: make_header(project_id=project_id)})
    result = list_active_archicads()

    assert len(result.active) == 1
    inst = result.active[0]
    assert inst.port == 19723
    assert inst.project_type == expected_type
    assert inst.project_path == expected_path
    assert inst.warning is None


@pytest.mark.parametrize(
    "version, expected_warning_substring",
    [
        ("1.0.0", "older than supported"),
        ("99.0.0", "newer than supported"),
    ],
)
def test_tapir_version_warnings(set_multi_conn, version, expected_warning_substring):
    set_multi_conn({19723: make_header(version=version)})
    result = list_active_archicads()

    assert len(result.active) == 1
    assert result.active[0].warning is not None
    assert expected_warning_substring in result.active[0].warning


def test_unresponsive_instance_reported(set_multi_conn):
    header = make_header(product_info=APIResponseError(code=5003, message="Modal dialog open."))
    set_multi_conn({19723: header})
    result = list_active_archicads()

    assert result.active == []
    assert len(result.unavailable) == 1
    assert result.unavailable[0].reason == "unresponsive"
    assert "Modal dialog open." in result.unavailable[0].message


def test_missing_tapir_reported(set_multi_conn):
    header = make_header(is_installed=False, version=None)
    set_multi_conn({19724: header})
    result = list_active_archicads()

    assert result.active == []
    assert len(result.unavailable) == 1
    assert result.unavailable[0].reason == "missing_tapir"
    assert "https://github.com/ENZYME-APD/tapir-archicad-automation" in result.unavailable[0].message


def test_broken_instance_does_not_block_healthy_one(set_multi_conn):
    broken = make_header(product_info=APIResponseError(code=None, message="Timeout"))
    healthy = make_header()
    set_multi_conn({19723: broken, 19724: healthy})

    result = list_active_archicads()
    assert len(result.active) == 1 and result.active[0].port == 19724
    assert len(result.unavailable) == 1 and result.unavailable[0].reason == "unresponsive"


def test_call_tool_intercepts_addon_unavailable(set_multi_conn):
    mock_func = Mock(side_effect=AddOnCommandUnavailable("Unknown Add-On command."))
    register_tool_for_dispatch(mock_func, name="test_cmd", title="T", description="D")
    set_multi_conn({19723: make_header()})

    with pytest.raises(ValueError, match="not available in the installed Tapir Add-On"):
        archicad_call_tool("test_cmd", {"port": 19723})