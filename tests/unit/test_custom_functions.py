from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from multiconn_archicad.basic_types import APIResponseError, ProductInfo, SoloProjectID

from tapir_archicad_mcp.context import multi_conn_instance
from tapir_archicad_mcp.tools.custom import functions
from tapir_archicad_mcp.tools.custom.functions import list_active_archicads
from tapir_archicad_mcp.tools.custom.models import DiscoveryResult


def make_multi_conn(active: dict) -> SimpleNamespace:
    return SimpleNamespace(
        refresh=SimpleNamespace(all_ports=Mock()),
        connect=SimpleNamespace(all=Mock()),
        active=active,
    )


@pytest.fixture
def set_multi_conn():
    tokens = []

    def _set(multi_conn: SimpleNamespace) -> None:
        tokens.append(multi_conn_instance.set(multi_conn))

    yield _set

    for token in tokens:
        multi_conn_instance.reset(token)


def test_empty_discovery_returns_empty_result(set_multi_conn):
    set_multi_conn(make_multi_conn(active={}))

    result = list_active_archicads()

    assert isinstance(result, DiscoveryResult)
    assert result.active == []
    assert result.unavailable == []


def test_unresponsive_archicad_is_reported_not_crashing(set_multi_conn, monkeypatch):
    header = SimpleNamespace(
        product_info=APIResponseError(code=None, message="Request timed out."),
        archicad_id=None,
        archicad_location=None,
    )
    set_multi_conn(make_multi_conn(active={19723: header}))
    monkeypatch.setattr(functions, "is_header_fully_initialized", lambda h: False)

    result = list_active_archicads()

    assert result.active == []
    assert len(result.unavailable) == 1
    issue = result.unavailable[0]
    assert issue.port == 19723
    assert issue.issue == "archicad_unresponsive"
    assert issue.archicad_version is None
    assert "Request timed out." in issue.message


def test_tapir_unavailable_is_diagnosed(set_multi_conn, monkeypatch):
    header = SimpleNamespace(
        product_info=ProductInfo(version=28, build=3001, lang="INT"),
        archicad_id=APIResponseError(code=None, message="No response from Tapir."),
        archicad_location=None,
    )
    set_multi_conn(make_multi_conn(active={19724: header}))
    monkeypatch.setattr(functions, "is_header_fully_initialized", lambda h: False)

    result = list_active_archicads()

    assert result.active == []
    assert len(result.unavailable) == 1
    issue = result.unavailable[0]
    assert issue.port == 19724
    assert issue.issue == "tapir_unavailable"
    assert issue.archicad_version == "28"
    assert "No response from Tapir." in issue.message


def test_one_broken_instance_does_not_block_healthy_one(set_multi_conn, monkeypatch):
    broken = SimpleNamespace(
        product_info=APIResponseError(code=None, message="Modal dialog open."),
        archicad_id=None,
        archicad_location=None,
    )
    healthy_core = SimpleNamespace(
        post_tapir_command=Mock(return_value={"version": "1.5.3"})
    )
    healthy = SimpleNamespace(
        product_info=ProductInfo(version=28, build=3001, lang="INT"),
        archicad_id=SoloProjectID(projectPath="C:/projects/house.pln", projectName="house"),
        archicad_location=None,
        core=healthy_core,
    )
    set_multi_conn(make_multi_conn(active={19723: broken, 19724: healthy}))
    monkeypatch.setattr(functions, "is_header_fully_initialized", lambda h: h is healthy)

    result = list_active_archicads()

    assert len(result.active) == 1
    active = result.active[0]
    assert active.port == 19724
    assert active.project_name == "house"
    assert active.project_type == "solo"
    assert active.project_path == "C:/projects/house.pln"
    assert active.tapir_version == "1.5.3"

    assert len(result.unavailable) == 1
    assert result.unavailable[0].port == 19723


def test_tapir_version_query_failure_is_not_fatal(set_multi_conn, monkeypatch):
    core = SimpleNamespace(
        post_tapir_command=Mock(side_effect=RuntimeError("connection lost"))
    )
    header = SimpleNamespace(
        product_info=ProductInfo(version=28, build=3001, lang="INT"),
        archicad_id=SoloProjectID(projectPath="C:/projects/house.pln", projectName="house"),
        archicad_location=None,
        core=core,
    )
    set_multi_conn(make_multi_conn(active={19723: header}))
    monkeypatch.setattr(functions, "is_header_fully_initialized", lambda h: True)

    result = list_active_archicads()

    assert len(result.active) == 1
    assert result.active[0].tapir_version is None
