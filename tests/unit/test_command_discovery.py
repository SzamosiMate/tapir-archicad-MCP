import pytest
from mcp.server.mcpserver.exceptions import ToolError

from tapir_archicad_mcp.tools.custom import command_discovery
from tapir_archicad_mcp.tools.custom.command_discovery import PAGE_BYTES, archicad_list_commands
from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG


def test_group_directory_partitions_the_catalogue():
    directory = archicad_list_commands(list_groups=True)
    assert sum(entry.command_count for entry in directory.groups) == len(TOOL_DISCOVERY_CATALOG)
    assert {"custom_data", "design_options", "project_data", "solid_ops"} <= {entry.group for entry in directory.groups}


def test_unknown_group_is_an_actionable_error():
    with pytest.raises(ToolError, match="Unknown catalogue groups: absent"):
        archicad_list_commands(groups=["absent"])


def test_search_can_page_through_ranked_results():
    first = archicad_list_commands(keywords=["elements"])
    assert first.remaining > 0
    assert len(first.matches) == 12
    second = archicad_list_commands(keywords=["elements"], query_id=first.query_id)
    assert first.remaining - second.remaining == len(second.matches)
    assert {match.name for match in first.matches}.isdisjoint(match.name for match in second.matches)


def test_chain_lists_group_ids_and_browses_multiple_groups():
    directory = archicad_list_commands(list_groups=True)
    assert {"keynotes", "teamwork"} <= {entry.group for entry in directory.groups}
    page = archicad_list_commands(groups=["KEYNOTES", "teamwork"])
    assert set(page.names.splitlines()) == {
        name for name in TOOL_DISCOVERY_CATALOG if name.startswith(("keynotes_", "teamwork_"))
    }
    assert page.remaining == 0


def test_chain_returns_an_exact_name_once_per_detail_upgrade():
    name = "elements_get_selected_elements"
    compact = archicad_list_commands(keywords=[name], detail="compact")
    assert compact.names == name
    full = archicad_list_commands(keywords=[name], query_id=compact.query_id)
    assert [row.name for row in full.matches] == [name]
    assert archicad_list_commands(keywords=[name], query_id=full.query_id).matches == []
    assert archicad_list_commands(keywords=[name], query_id=full.query_id, detail="compact").names == ""
    replay = archicad_list_commands(keywords=[name], query_id=compact.query_id)
    assert replay.model_dump(exclude={"query_id"}) == full.model_dump(exclude={"query_id"})
    assert len(compact.query_id) == len(full.query_id) == 12


def test_chain_deduplicates_batches_and_refined_queries():
    name = "navigator_publish_publisher_set"
    first = archicad_list_commands(keywords=[name, name, "drawing"])
    names = [row.name for row in first.matches]
    assert names.count(name) == 1
    second = archicad_list_commands(groups=["navigator"], keywords=["publishing", "drawing"], query_id=first.query_id)
    assert second.matches
    assert set(names).isdisjoint(row.name for row in second.matches)
    assert all(row.name.startswith("navigator_") for row in second.matches)


def test_chain_reports_missing_and_outside_scope_exact_names():
    results = archicad_list_commands(
        groups=["issues"], keywords=["elements_get_selected_elements", " ", "issues_imaginary_tool"]
    )
    assert [(match.keyword_index, match.status) for match in results.exact_matches] == [
        (0, "outside_groups"),
        (2, "missing"),
    ]


def test_chain_pages_follow_one_order_without_gaps_or_duplicates():
    expected = [name for name in TOOL_DISCOVERY_CATALOG if name.startswith("elements_")]
    page = archicad_list_commands(groups=["elements"], detail="full")
    found = []
    while True:
        assert len(page.model_dump_json().encode()) <= PAGE_BYTES
        found.extend(row.name for row in page.matches)
        assert 0 < len(found) <= len(expected)
        if not page.remaining:
            break
        page = archicad_list_commands(groups=["elements"], detail="full", query_id=page.query_id)
    assert found == expected


def test_chain_rejects_malformed_tokens():
    with pytest.raises(ToolError, match="Invalid or expired query_id"):
        archicad_list_commands(query_id="invalid")


def test_query_ids_expire_when_idle(monkeypatch):
    monkeypatch.setattr(command_discovery, "_continuations", command_discovery.QueryContinuations())
    now = 100.0
    monkeypatch.setattr(command_discovery, "monotonic", lambda: now)
    first = archicad_list_commands(keywords=["elements"])
    now += command_discovery.QUERY_TTL_SECONDS
    with pytest.raises(ToolError, match="Invalid or expired query_id"):
        archicad_list_commands(keywords=["elements"], query_id=first.query_id)


def test_continuation_store_evicts_the_least_recently_used_id(monkeypatch):
    monkeypatch.setattr(command_discovery, "_continuations", command_discovery.QueryContinuations())
    monkeypatch.setattr(command_discovery, "MAX_QUERY_STATES", 2)
    arguments = {"keywords": ["elements_get_selected_elements"]}
    oldest = archicad_list_commands(**arguments)
    other = archicad_list_commands(**arguments)
    assert archicad_list_commands(**arguments, query_id=oldest.query_id).matches == []
    archicad_list_commands(**arguments)
    with pytest.raises(ToolError, match="Invalid or expired query_id"):
        archicad_list_commands(**arguments, query_id=other.query_id)
    assert archicad_list_commands(**arguments, query_id=oldest.query_id).matches == []
