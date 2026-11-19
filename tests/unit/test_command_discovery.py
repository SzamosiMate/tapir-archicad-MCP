import pytest
from mcp.server.mcpserver.exceptions import ToolError

from tapir_archicad_mcp.tools.custom import command_discovery
from tapir_archicad_mcp.tools.custom.command_discovery import archicad_list_commands, command_groups
from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG


def test_command_groups_include_multiword_prefixes():
    groups = command_groups()
    assert {"custom_data", "design_options", "project_data", "solid_ops"} <= set(groups)


def test_unknown_group_is_an_actionable_error():
    with pytest.raises(ToolError, match="Unknown catalogue groups: absent"):
        archicad_list_commands(groups=["absent"])


def test_search_can_page_through_ranked_results():
    keywords = ["publisher set", "drawing"]
    first = archicad_list_commands(keywords=keywords).result
    assert len(first.matches) == 12
    assert first.remaining > 0
    second = archicad_list_commands(keywords=keywords, query_id=first.query_id).result
    assert {match.name for match in first.matches}.isdisjoint(match.name for match in second.matches)
    assert second.remaining == first.remaining - len(second.matches)


@pytest.mark.parametrize(
    ("phrase", "groups"),
    [
        ("compare element GUID sets for clashes", None),
        ("GUID clash", None),
        ("element GUID clash or duplicates", ["elements"]),
    ],
)
def test_search_finds_collisions_using_generated_wordnet_aliases(phrase, groups):
    page = archicad_list_commands(keywords=[phrase], groups=groups).result
    target = next(match for match in page.matches[:3] if match.name == "elements_get_collisions")
    assert target.description


def test_round_robin_interleaves_before_applying_the_page_limit(monkeypatch):
    phrases = [f"intent{index}" for index in range(8)]
    catalogue = {
        f"actions_{phrase}_{number}": {"description": f"Command for {phrase}."}
        for phrase in phrases
        for number in range(4)
    }
    monkeypatch.setattr(command_discovery, "TOOL_DISCOVERY_CATALOG", catalogue)
    expected = [f"actions_{phrase}_{number}" for number in range(4) for phrase in phrases]
    page = archicad_list_commands(keywords=phrases).result
    for start in (0, 12, 24):
        assert [match.name for match in page.matches] == expected[start : start + 12]
        assert page.remaining == max(len(expected) - start - 12, 0)
        if page.remaining:
            page = archicad_list_commands(keywords=phrases, query_id=page.query_id).result


def test_chain_browses_multiple_groups():
    page = archicad_list_commands(groups=["KEYNOTES", "teamwork"]).result
    assert set(page.names.splitlines()) == {
        name for name in TOOL_DISCOVERY_CATALOG if name.startswith(("keynotes_", "teamwork_"))
    }
    assert page.remaining == 0


def test_exact_name_returns_a_single_name_without_description():
    name = "keynotes_get_keynote_tree"
    page = archicad_list_commands(keywords=[name.upper()]).result
    assert page.exact_matches[0].commands == [name]
    assert page.exact_matches[0].exact_status == "found"
    assert page.matches == []
    assert page.remaining == 0
    repeated = archicad_list_commands(keywords=[name], query_id=page.query_id).result
    assert repeated.exact_matches[0].commands == []
    assert repeated.exact_matches[0].exact_status == "found"


def test_chain_can_describe_a_previously_returned_name():
    name = "keynotes_get_keynote_tree"
    compact = archicad_list_commands(groups=["keynotes"]).result
    assert name in compact.names.splitlines()
    args = {"groups": ["keynotes"], "keywords": ["keynote tree"]}
    full = archicad_list_commands(**args, query_id=compact.query_id).result
    assert next(match.description for match in full.matches if match.name == name)
    repeated = archicad_list_commands(**args, query_id=full.query_id).result
    assert name not in {match.name for match in repeated.matches}
    assert archicad_list_commands(groups=["keynotes"], query_id=full.query_id).result.names == ""
    replay = archicad_list_commands(**args, query_id=compact.query_id).result
    assert replay.model_dump(exclude={"query_id"}) == full.model_dump(exclude={"query_id"})
    assert len(compact.query_id) == len(full.query_id) == 12


def test_chain_deduplicates_batches_and_refined_queries():
    first = archicad_list_commands(keywords=["publisher set", "publisher set", "drawing"]).result
    distinct = archicad_list_commands(keywords=["publisher set", "drawing"]).result
    assert first.matches == distinct.matches
    first_names = {match.name for match in first.matches}
    assert len(first_names) == len(first.matches)
    second = archicad_list_commands(
        groups=["navigator"], keywords=["publishing", "drawing"], query_id=first.query_id
    ).result
    assert second.matches
    assert first_names.isdisjoint(match.name for match in second.matches)
    assert all(match.name.startswith("navigator_") for match in second.matches)


def test_chain_reports_missing_and_outside_scope_exact_names():
    results = archicad_list_commands(
        groups=["issues"], keywords=["elements_get_selected_elements", " ", "issues_imaginary_tool"]
    ).result
    assert [(match.keyword_index, match.exact_status) for match in results.exact_matches] == [
        (0, "outside_groups"),
        (2, "missing"),
    ]


def test_chain_pages_follow_one_order_without_gaps_or_duplicates(monkeypatch):
    page_bytes = 512
    monkeypatch.setattr(command_discovery, "PAGE_BYTES", page_bytes)
    expected = [name for name in TOOL_DISCOVERY_CATALOG if name.startswith("elements_")]
    page = archicad_list_commands(groups=["elements"]).result
    assert page.remaining > 0
    found = []
    while True:
        assert len(page.model_dump_json().encode()) <= page_bytes
        found.extend(page.names.splitlines())
        assert 0 < len(found) <= len(expected)
        if not page.remaining:
            break
        page = archicad_list_commands(groups=["elements"], query_id=page.query_id).result
    assert found == expected


def test_chain_rejects_malformed_tokens():
    with pytest.raises(ToolError, match="Invalid or expired query_id"):
        archicad_list_commands(query_id="invalid")


def test_query_ids_expire_when_idle(monkeypatch):
    monkeypatch.setattr(command_discovery, "_continuations", command_discovery.QueryContinuations())
    now = 100.0
    monkeypatch.setattr(command_discovery, "monotonic", lambda: now)
    first = archicad_list_commands(keywords=["elements"]).result
    now += command_discovery.QUERY_TTL_SECONDS
    with pytest.raises(ToolError, match="Invalid or expired query_id"):
        archicad_list_commands(keywords=["elements"], query_id=first.query_id)


def test_continuation_store_evicts_the_least_recently_used_id(monkeypatch):
    monkeypatch.setattr(command_discovery, "_continuations", command_discovery.QueryContinuations())
    monkeypatch.setattr(command_discovery, "MAX_QUERY_STATES", 2)
    arguments = {"keywords": ["elements_get_selected_elements"]}
    oldest = archicad_list_commands(**arguments).result
    other = archicad_list_commands(**arguments).result
    assert archicad_list_commands(**arguments, query_id=oldest.query_id).result.exact_matches[0].commands == []
    archicad_list_commands(**arguments)
    with pytest.raises(ToolError, match="Invalid or expired query_id"):
        archicad_list_commands(**arguments, query_id=other.query_id)
    assert archicad_list_commands(**arguments, query_id=oldest.query_id).result.exact_matches[0].commands == []
