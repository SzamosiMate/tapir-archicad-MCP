from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad.models.tapir import types as tapir
from multiconn_archicad.models.tapir.types import ElementId, ElementIdArrayItem
from multiconn_archicad.utilities.namespaces.elements import ElementUtilities
from multiconn_archicad.utilities.queries import PropertyCatalogue, PropertyTest, Query
from multiconn_archicad.utilities.queries import TestRegistry as QueryTestRegistry
from multiconn_archicad.utilities.results.batch_results import BatchResult, BatchSlot
from payloads import archicad_call_tool

from tapir_archicad_mcp.tools.custom.functions import archicad_get_command_schema, archicad_list_commands

QUERY = {
    "schema_version": "1.0",
    "where": {"kind": "element_type", "test": {"kind": "element_type", "types": ["Wall", "Door"]}},
}


def element(number):
    return ElementIdArrayItem(elementId=ElementId(guid=UUID(int=number)))


def arguments(**params):
    return {"port": 19723, "params": {"query": deepcopy(QUERY), **params}}


@pytest.fixture
def query_api(fake_archicad):
    api = Mock()
    fake_archicad.unified = SimpleNamespace(utilities=SimpleNamespace(element=api))
    api.find_elements.return_value = [element(1)]
    return api


def test_discovery_schema_includes_query_tree_and_explicit_version(query_api):
    page = archicad_list_commands(keywords=["elements_query"]).result
    assert page.exact_matches[0].commands == ["elements_query"]
    schema = archicad_get_command_schema("elements_query").input_schema
    assert set(schema["properties"]) == {"port", "params", "page_token"}
    assert set(schema["$defs"]["SerializedQuery"]["required"]) == {"schema_version", "where"}
    assert schema["$defs"]["ElementQueryParameters"]["additionalProperties"] is False
    for family in ("RealTest", "RealListTest"):
        description = schema["$defs"][family]["description"]
        assert "SI units" in description and "degrees" in description

    def resolve_refs(value):
        if isinstance(value, dict):
            if "$ref" in value:
                target = schema
                for part in value["$ref"].removeprefix("#/").split("/"):
                    target = target[part]
                assert target
            for child in value.values():
                resolve_refs(child)
        elif isinstance(value, list):
            for child in value:
                resolve_refs(child)

    resolve_refs(schema)


def test_discovery_schema_exposes_property_families_and_operand_shapes(query_api):
    definitions = archicad_get_command_schema("elements_query").input_schema["$defs"]
    mapping = definitions["PropertyPredicate"]["properties"]["test"]["discriminator"]["mapping"]
    for kind, family, value_type, item_type in (
        ("enum", "EnumTest", "string", None),
        ("guid", "GuidTest", "string", None),
        ("multi_enum", "MultiEnumTest", "array", "string"),
        ("string_list", "StringListTest", "array", "string"),
        ("integer_list", "IntegerListTest", "array", "integer"),
        ("real_list", "RealListTest", "array", "number"),
    ):
        assert mapping[kind] == f"#/$defs/{family}"
        value_schema = definitions[family]["properties"]["value"]
        assert value_schema["type"] == value_type
        if item_type:
            assert value_schema["items"]["type"] == item_type
    assert definitions["GuidTest"]["properties"]["value"]["format"] == "uuid"
    assert definitions["MultiEnumTest"]["properties"]["value"]["uniqueItems"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("supplied", [False, True], ids=["search", "filter"])
@pytest.mark.parametrize(
    "kind, operand, parsed",
    [
        ("enum", "Red", "Red"),
        ("guid", "ABCDEFAB-1234-4234-8234-ABCDEFABCDEF", UUID("abcdefab-1234-4234-8234-abcdefabcdef")),
        ("multi_enum", ["Red", "Blue"], ("Red", "Blue")),
        ("string_list", ["A", "B", "A"], ("A", "B", "A")),
        ("integer_list", [9007199254740993, 2, 2], (9007199254740993, 2, 2)),
        ("real_list", [1.25, 2, 1.25], (1.25, 2.0, 1.25)),
    ],
)
async def test_property_operands_survive_mcp_validation_and_dispatch(query_api, supplied, kind, operand, parsed):
    request = arguments()
    request["params"]["query"]["where"] = {
        "kind": "property",
        "field_id": str(UUID(int=9)),
        "test": {"kind": kind, "operator": "is", "value": operand},
    }
    if supplied:
        request["params"]["elements"] = [element(1).model_dump(mode="json")]
        query_api.filter_elements_by_query_result.return_value = BatchResult((BatchSlot.success(element(1)),))
    response = await archicad_call_tool("elements_query", request)
    assert response["elements"] == [element(1).model_dump(mode="json")]
    if supplied:
        query = query_api.filter_elements_by_query_result.call_args.args[1]
        query_api.find_elements.assert_not_called()
    else:
        query = query_api.find_elements.call_args.args[0]
        query_api.filter_elements_by_query_result.assert_not_called()
    assert query.where.test.kind == kind
    assert query.where.test.value == parsed
    # Pagination serializes the validated parameters to identify continuations.
    # Verify that the parsed UUID/tuple operands stay valid executable JSON.
    loaded = Query.model_validate_json(query.model_dump_json())
    assert loaded.model_dump(mode="json") == query.model_dump(mode="json")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "kind, operand",
    [
        ("enum", ["Red"]),
        ("guid", "not-a-guid"),
        ("multi_enum", "Red"),
        ("multi_enum", ["Red", "Red"]),
        ("string_list", "A"),
        ("integer_list", [1, 2.5]),
        ("integer_list", [True]),
        ("real_list", ["1.5"]),
    ],
)
async def test_invalid_property_operands_fail_before_execution(query_api, kind, operand):
    request = arguments()
    request["params"]["query"]["where"] = {
        "kind": "property",
        "field_id": str(UUID(int=9)),
        "test": {
            "kind": kind,
            "operator": "contains" if "list" in kind or kind == "multi_enum" else "is",
            "value": operand,
        },
    }
    with pytest.raises(ToolError, match="Invalid arguments"):
        await archicad_call_tool("elements_query", request)
    query_api.find_elements.assert_not_called()
    query_api.filter_elements_by_query_result.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("multi", [False, True], ids=["enum", "multi_enum"])
@pytest.mark.parametrize("valid", [False, True], ids=["unknown_choice", "known_choice"])
async def test_enum_choices_are_validated_against_current_metadata(fake_archicad, multi, valid):
    property_id = UUID(int=9)
    details = tapir.PropertyDetails(
        propertyId=tapir.PropertyId(guid=property_id),
        propertyType="Custom",
        propertyGroupName="MCP test",
        propertyName="Color",
        propertyCollectionType="MultipleChoiceEnumeration" if multi else "SingleChoiceEnumeration",
        propertyValueType="String",
        propertyMeasureType="Default",
        propertyIsEditable=True,
        isExpressionBased=False,
        possibleEnumValues=[{"enumValue": {"displayValue": label, "guid": UUID(int=0)}} for label in ("Red", "Blue")],
    )
    api = Mock()
    api.read_header_metadata.return_value = SimpleNamespace(tapir_info=SimpleNamespace(version="2.0.0"))
    api.utilities.element = ElementUtilities(api)
    api.utilities.property.discover_query_fields.return_value = PropertyCatalogue(
        [details], QueryTestRegistry.from_union(PropertyTest)
    )
    fake_archicad.unified = api
    label = "Red" if valid else "red"
    request = arguments(elements=[])
    request["params"]["query"]["where"] = {
        "kind": "property",
        "field_id": str(property_id),
        "test": {"kind": "multi_enum" if multi else "enum", "operator": "is", "value": [label] if multi else label},
    }
    if valid:
        response = await archicad_call_tool("elements_query", request)
        assert response["elements"] == []
    else:
        with pytest.raises(ToolError, match="not a choice"):
            await archicad_call_tool("elements_query", request)
    api.utilities.property.discover_query_fields.assert_called_once_with(property_ids=(property_id,))
    api.tapir.element.get_all_elements.assert_not_called()
    api.tapir.property.get_property_values_of_elements.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("params", [{}, {"elements": None}])
async def test_search_uses_find_elements(query_api, params):
    result = await archicad_call_tool("elements_query", arguments(**params))
    assert result["elements"] == [element(1).model_dump(mode="json")]
    query = query_api.find_elements.call_args.args[0]
    assert isinstance(query, Query)
    assert query.model_dump(mode="json") == QUERY
    query_api.filter_elements_by_query_result.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("empty", [False, True])
async def test_supplied_elements_preserve_matching_duplicates_and_omit_errors(query_api, empty):
    candidates = [] if empty else [element(1), element(2), element(1), element(3)]
    slots = (
        ()
        if empty
        else (
            BatchSlot.success(element(1)),
            BatchSlot.filtered(),
            BatchSlot.success(element(1)),
            BatchSlot.failure("read error"),
        )
    )
    query_api.filter_elements_by_query_result.return_value = BatchResult(slots)
    result = await archicad_call_tool(
        "elements_query", arguments(elements=[item.model_dump(mode="json") for item in candidates])
    )
    assert result["elements"] == ([] if empty else [element(1).model_dump(mode="json")] * 2)
    assert query_api.filter_elements_by_query_result.call_args.args[0] == candidates
    query_api.find_elements.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["missing_version", "bad_kind", "extra_field", "bad_operand"])
async def test_invalid_queries_fail_before_execution(query_api, change):
    request = arguments()
    query = request["params"]["query"]
    if change == "missing_version":
        query.pop("schema_version")
    elif change == "bad_kind":
        query["where"]["kind"] = "invented"
    elif change == "extra_field":
        request["params"]["countOnly"] = True
    else:
        query["where"] = {
            "kind": "property",
            "field_id": str(UUID(int=9)),
            "test": {"kind": "integer", "operator": "is", "value": "three"},
        }
    with pytest.raises(ToolError):
        await archicad_call_tool("elements_query", request)
    query_api.find_elements.assert_not_called()


@pytest.mark.asyncio
async def test_query_wide_failure_remains_an_error(query_api):
    query_api.find_elements.side_effect = ValueError("where: unknown property GUID")
    with pytest.raises(ToolError, match="unknown property GUID"):
        await archicad_call_tool("elements_query", arguments())


@pytest.mark.asyncio
async def test_pagination_reads_retained_matches_without_reexecution(query_api):
    query_api.find_elements.return_value = [element(i) for i in range(1, 102)]
    request = arguments()
    first = await archicad_call_tool("elements_query", request)
    assert len(first["elements"]) == 100
    second = await archicad_call_tool("elements_query", {**request, "page_token": first["next_page_token"]})
    assert second["elements"] == [element(101).model_dump(mode="json")]
    query_api.find_elements.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_runs_real_multiconn_nested_query(fake_archicad):
    api = Mock()
    api.read_header_metadata.return_value = SimpleNamespace(tapir_info=SimpleNamespace(version="2.0.0"))
    api.utilities.element = ElementUtilities(api)
    fake_archicad.unified = api
    api.tapir.element.get_elements_by_type.return_value = tapir.ElementsWithExecutionResults(
        elements=[element(1), element(1)]
    )
    api.tapir.element.filter_elements.side_effect = lambda elements, element_types: (
        elements if tapir.ElementType.WALL in element_types else []
    )
    wall = {"kind": "element_type", "test": {"kind": "element_type", "types": ["Wall"]}}
    door = {"kind": "element_type", "test": {"kind": "element_type", "types": ["Door"]}}
    request = arguments()
    request["params"]["query"]["where"] = {"kind": "any", "items": [{"kind": "all", "items": [wall, door]}, wall]}
    result = await archicad_call_tool("elements_query", request)
    assert result["elements"] == [element(1).model_dump(mode="json")]
    assert api.tapir.element.get_elements_by_type.call_args.args == (tapir.ElementType.WALL,)
    api.tapir.element.change_selection_of_elements.assert_not_called()


@pytest.mark.asyncio
async def test_empty_candidates_still_validate_query_version(fake_archicad):
    api = Mock()
    api.utilities.element = ElementUtilities(api)
    fake_archicad.unified = api
    request = arguments(elements=[])
    request["params"]["query"]["schema_version"] = "99.0"
    with pytest.raises(ToolError, match="Unsupported query schema version"):
        await archicad_call_tool("elements_query", request)
    api.read_header_metadata.assert_not_called()


@pytest.mark.asyncio
async def test_discovered_instance_does_not_need_batch_worklist_membership(query_api):
    from tapir_archicad_mcp.context import multi_conn_instance

    multi_conn_instance.get().active = {}
    result = await archicad_call_tool("elements_query", arguments())
    assert result["elements"] == [element(1).model_dump(mode="json")]
    query_api.find_elements.assert_called_once()
