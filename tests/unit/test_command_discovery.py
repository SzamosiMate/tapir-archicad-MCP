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
    individual = [archicad_list_commands(keywords=[keyword]).result.matches[0].commands for keyword in keywords]
    first = archicad_list_commands(keywords=keywords).result
    assert [match.commands for match in first.matches] == individual
    assert all(len(match.commands) == 3 and match.remaining > 0 for match in first.matches)
    second = archicad_list_commands(keywords=keywords, query_id=first.query_id).result
    assert set(first.descriptions).isdisjoint(second.descriptions)
    assert all(a.remaining > b.remaining for a, b in zip(first.matches, second.matches, strict=True))


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
    assert "elements_get_collisions" in page.matches[0].commands
    assert "elements_get_collisions" in page.descriptions


def test_page_limit_applies_to_each_phrase(monkeypatch):
    phrases = [f"intent{index}" for index in range(8)]
    catalogue = {
        f"actions_{phrase}_{number}": {"description": f"Command for {phrase}."}
        for phrase in phrases
        for number in range(4)
    }
    monkeypatch.setattr(command_discovery, "TOOL_DISCOVERY_CATALOG", catalogue)
    page = archicad_list_commands(keywords=phrases).result
    assert len(page.descriptions) == 24
    for index, match in enumerate(page.matches):
        assert match.keyword_index == index
        assert match.commands == [f"actions_{phrases[index]}_{number}" for number in range(3)]
        assert match.remaining == 1


def test_chain_browses_multiple_groups():
    page = archicad_list_commands(groups=["KEYNOTES", "teamwork"]).result
    assert set(page.names.splitlines()) == {
        name for name in TOOL_DISCOVERY_CATALOG if name.startswith(("keynotes_", "teamwork_"))
    }
    assert page.remaining == 0


def test_exact_name_returns_a_single_name_without_description():
    name = "keynotes_get_keynote_tree"
    page = archicad_list_commands(keywords=[name.upper()]).result
    assert page.matches[0].commands == [name]
    assert page.matches[0].exact_status == "found"
    assert page.matches[0].remaining == 0
    assert page.descriptions == {}
    repeated = archicad_list_commands(keywords=[name], query_id=page.query_id).result
    assert repeated.matches[0].commands == []
    assert repeated.matches[0].exact_status == "found"


def test_chain_can_describe_a_previously_returned_name():
    name = "keynotes_get_keynote_tree"
    compact = archicad_list_commands(groups=["keynotes"]).result
    assert name in compact.names.splitlines()
    args = {"groups": ["keynotes"], "keywords": ["keynote tree"]}
    full = archicad_list_commands(**args, query_id=compact.query_id).result
    assert name in full.matches[0].commands
    assert full.descriptions[name]
    assert name not in archicad_list_commands(**args, query_id=full.query_id).result.descriptions
    assert archicad_list_commands(groups=["keynotes"], query_id=full.query_id).result.names == ""
    replay = archicad_list_commands(**args, query_id=compact.query_id).result
    assert replay.model_dump(exclude={"query_id"}) == full.model_dump(exclude={"query_id"})
    assert len(compact.query_id) == len(full.query_id) == 12


def test_chain_deduplicates_batches_and_refined_queries():
    first = archicad_list_commands(keywords=["publisher set", "publisher set", "drawing"]).result
    assert first.matches[0].commands == first.matches[1].commands
    assert set(first.descriptions) == {name for match in first.matches for name in match.commands}
    second = archicad_list_commands(
        groups=["navigator"], keywords=["publishing", "drawing"], query_id=first.query_id
    ).result
    assert second.descriptions
    assert set(first.descriptions).isdisjoint(second.descriptions)
    assert all(name.startswith("navigator_") for name in second.descriptions)


def test_chain_reports_missing_and_outside_scope_exact_names():
    results = archicad_list_commands(
        groups=["issues"], keywords=["elements_get_selected_elements", " ", "issues_imaginary_tool"]
    ).result
    assert [(match.keyword_index, match.exact_status) for match in results.matches] == [
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
    assert archicad_list_commands(**arguments, query_id=oldest.query_id).result.matches[0].commands == []
    archicad_list_commands(**arguments)
    with pytest.raises(ToolError, match="Invalid or expired query_id"):
        archicad_list_commands(**arguments, query_id=other.query_id)
    assert archicad_list_commands(**arguments, query_id=oldest.query_id).result.matches[0].commands == []
