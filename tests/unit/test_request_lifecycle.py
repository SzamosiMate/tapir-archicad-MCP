from __future__ import annotations

import logging

import pytest

from tapir_archicad_mcp.request_lifecycle import DispatchLifecycle


def test_start_and_end_are_logged_with_the_same_request_id(caplog):
    with caplog.at_level(logging.INFO):
        with DispatchLifecycle("elements_create_walls", 19723) as lifecycle:
            pass

    start, end = [r.message for r in caplog.records]
    assert start == f"[{lifecycle.request_id}] Request start: 'elements_create_walls' on port 19723"
    assert end == f"[{lifecycle.request_id}] Request end: 'elements_create_walls' on port 19723 - ok"


def test_end_reports_the_exception_type_and_does_not_swallow_it(caplog):
    with caplog.at_level(logging.INFO):
        with pytest.raises(ValueError):
            with DispatchLifecycle("elements_delete_elements", 19723):
                raise ValueError("boom")

    assert "failed with ValueError" in caplog.records[-1].message


def test_overlapping_requests_get_distinct_ids_and_stay_pairable(caplog):
    with caplog.at_level(logging.INFO):
        with DispatchLifecycle("a", 19723) as outer, DispatchLifecycle("b", 19724) as inner:
            pass

    assert outer.request_id != inner.request_id
    messages = [r.message for r in caplog.records]
    assert sum(outer.request_id in m for m in messages) == 2
    assert sum(inner.request_id in m for m in messages) == 2
