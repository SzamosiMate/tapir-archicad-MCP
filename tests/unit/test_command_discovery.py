import pytest
from mcp.server.mcpserver.exceptions import ToolError

from tapir_archicad_mcp.tools.custom.command_discovery import (
    list_command_names,
    list_grouped_commands,
    list_grouped_keyword_commands,
    list_keyword_commands,
)
from tapir_archicad_mcp.tools.custom.discovery_chain import PAGE_BYTES, chain_tool
from tapir_archicad_mcp.tools.custom.functions import archicad_list_commands


def test_name_list_matches_full_catalogue():
    assert list_command_names().splitlines() == [command.name for command in archicad_list_commands()]


def test_group_directory_partitions_the_catalogue():
    directory = list_grouped_commands()
    all_commands = []
    for entry in directory.groups:
        commands = list_grouped_commands(entry.group)
        assert len(commands) == entry.command_count
        assert all(command.name.startswith(f"{entry.group}_") for command in commands)
        all_commands.extend(command.name for command in commands)

    assert sorted(all_commands) == sorted(list_command_names().splitlines())
    assert {"custom_data", "design_options", "project_data", "solid_ops"} <= {entry.group for entry in directory.groups}


def test_grouped_keyword_routes_each_argument_combination():
    assert list_grouped_keyword_commands() == list_grouped_commands()
    assert list_grouped_keyword_commands(group=" DESIGN_OPTIONS ") == list_grouped_commands("design_options")
    assert list_grouped_keyword_commands(query="publisher set") == list_keyword_commands("publisher set")

    matches = list_grouped_keyword_commands(group="navigator", query="view settings")
    assert matches.matches
    assert all(command.name.startswith("navigator_") for command in matches.matches)


def test_exact_match_takes_precedence_and_respects_scope():
    matches = list_keyword_commands("  ELEMENTS_GET_SELECTED_ELEMENTS  ")
    assert matches.total_matches == 1
    assert [command.name for command in matches.matches] == ["elements_get_selected_elements"]

    matches = list_grouped_keyword_commands(group="issues", query="elements_get_selected_elements")
    assert all(command.name.startswith("issues_") for command in matches.matches)


def test_keyword_limits_broad_queries_and_returns_no_hits_for_unknown_terms():
    matches = list_keyword_commands("elements")
    assert matches.total_matches > len(matches.matches) == 12
    assert all(command.description for command in matches.matches)

    matches = list_keyword_commands("zzzzzzmissingzzzzzz")
    assert matches.total_matches == 0
    assert matches.matches == []
    assert list_keyword_commands("  ") == archicad_list_commands()


@pytest.mark.parametrize("query", ["", "something"])
def test_unknown_group_is_an_actionable_error(query):
    with pytest.raises(ToolError, match="Unknown command group 'missing'"):
        list_grouped_keyword_commands(group="missing", query=query)


def test_chain_lists_group_ids_and_browses_multiple_groups():
    discover = chain_tool(False)
    directory = discover(list_groups=True)
    assert {"keynotes", "teamwork"} <= {entry.group for entry in directory.groups}
    page = discover(groups=["KEYNOTES", "teamwork"])
    assert set(page.names.splitlines()) == {
        name for name in list_command_names().splitlines() if name.startswith(("keynotes_", "teamwork_"))
    }
    assert page.remaining == 0


def test_chain_returns_an_exact_name_once_per_detail_upgrade():
    discover = chain_tool(False)
    name = "elements_get_selected_elements"
    compact = discover(keywords=[name], detail="compact")
    assert compact.names == name
    full = discover(keywords=[name], query_id=compact.query_id)
    assert [row.name for row in full.matches] == [name]
    assert discover(keywords=[name], query_id=full.query_id).matches == []
    assert discover(keywords=[name], query_id=full.query_id, detail="compact").names == ""
    assert discover(keywords=[name], query_id=compact.query_id) == full


def test_chain_deduplicates_batches_and_refined_queries():
    discover = chain_tool(False)
    name = "navigator_publish_publisher_set"
    first = discover(keywords=[name, name, "drawing"])
    names = [row.name for row in first.matches]
    assert names.count(name) == 1
    second = discover(groups=["navigator"], keywords=["publishing", "drawing"], query_id=first.query_id)
    assert second.matches
    assert set(names).isdisjoint(row.name for row in second.matches)
    assert all(row.name.startswith("navigator_") for row in second.matches)


def test_chain_reports_missing_and_outside_scope_exact_names():
    discover = chain_tool(False)
    results = discover(groups=["issues"], keywords=["elements_get_selected_elements", "issues_imaginary_tool"])
    assert [(match.keyword_index, match.status) for match in results.exact_matches] == [
        (0, "outside_groups"),
        (1, "missing"),
    ]


def test_chain_pages_follow_one_order_without_gaps_or_duplicates():
    discover = chain_tool(False)
    expected = [name for name in list_command_names().splitlines() if name.startswith("elements_")]
    page = discover(groups=["elements"], detail="full")
    found = []
    while True:
        assert len(page.model_dump_json().encode()) <= PAGE_BYTES
        found.extend(row.name for row in page.matches)
        assert 0 < len(found) <= len(expected)
        if not page.remaining:
            break
        page = discover(groups=["elements"], detail="full", query_id=page.query_id)
    assert found == expected


def test_chain_rejects_malformed_tokens():
    discover = chain_tool(False)
    with pytest.raises(ToolError, match="Invalid query_id"):
        discover(query_id="invalid")
