from __future__ import annotations

import logging

import pytest

from tapir_archicad_mcp.request_lifecycle import DispatchLifecycle


def test_start_and_end_are_logged_with_the_same_request_id(caplog):
    with caplog.at_level(logging.INFO):
        with DispatchLifecycle("elements_create_walls") as lifecycle:
            lifecycle.bind_port(19723)

    start, end = [r.message for r in caplog.records]
    assert start == f"[{lifecycle.request_id}] Dispatch start: 'elements_create_walls'"
    assert end == f"[{lifecycle.request_id}] Dispatch end: 'elements_create_walls' on port 19723 - ok"


def test_end_reports_the_exception_type_and_does_not_swallow_it(caplog):
    with caplog.at_level(logging.INFO):
        with pytest.raises(ValueError):
            with DispatchLifecycle("elements_delete_elements"):
                raise ValueError("boom")

    assert "failed with ValueError" in caplog.records[-1].message


def test_overlapping_calls_get_distinct_request_ids(caplog):
    with caplog.at_level(logging.INFO):
        with DispatchLifecycle("a") as outer, DispatchLifecycle("b") as inner:
            pass

    assert outer.request_id != inner.request_id
    messages = [r.message for r in caplog.records]
    # Interleaved lines can still be paired up by their id.
    assert sum(outer.request_id in m for m in messages) == 2
    assert sum(inner.request_id in m for m in messages) == 2


def test_port_is_omitted_until_it_is_known(caplog):
    with caplog.at_level(logging.INFO):
        with DispatchLifecycle("archicad_list_commands"):
            pass

    assert "on port" not in caplog.records[0].message
    assert "on port" not in caplog.records[1].message
