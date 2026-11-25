import asyncio
from dataclasses import replace
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad.models.tapir import types as tapir
from multiconn_archicad.utilities.namespaces.properties import PropertyUtilities
from multiconn_archicad.utilities.results.batch_results import BatchResult, BatchSlot
from payloads import archicad_call_tool, archicad_get_job
from pydantic import BaseModel

from tapir_archicad_mcp.jobs import JobSettings
from tapir_archicad_mcp.metadata_types import CommandMetadata, Positional, Presentation
from tapir_archicad_mcp.result_budget import ResultBudget, token_count
from tapir_archicad_mcp.result_data import PositionalData, StoredResult
from tapir_archicad_mcp.result_reading import ReadSelection
from tapir_archicad_mcp.tool_results import Completion, ResultMode, delivery_reason
from tapir_archicad_mcp.tools.custom.functions import archicad_get_command_schema
from tapir_archicad_mcp.tools.custom.result_tools import result_read
from tapir_archicad_mcp.tools.tool_registry import get_tool_entry, register_tool_for_dispatch

pytestmark = pytest.mark.asyncio

DETAILS = "elements_get_details_of_elements"
REFRESH = "elements_refresh_elements"
READ_GRID = "properties_read_grid"
WRITE_GRID = "properties_write_grid"


def item(n, kind="element"):
    return {kind + "Id": {"guid": str(UUID(int=n))}}


def failure(n=1):
    return {"error": {"code": n, "message": "Unavailable item"}}


def parameters(**kwargs):
    return {"port": 19723, "params": kwargs}


def reference(response, *path, view=None):
    ref = {"$handle": response["resultHandle"]}
    if path:
        ref["path"] = list(path)
    if view:
        ref["view"] = view
    return ref


async def test_batch_chain_projects_failures_and_reuses_successful_inputs(fake_archicad):
    elements = [item(i) for i in range(1, 110)] + [item(1)]
    fake_archicad.on_tapir_command(
        "GetDetailsOfElements",
        {"detailsOfElements": [{**entry, "id": "Walls"} for entry in elements[:100]] + [failure()] * 10},
    )
    source = await archicad_call_tool(DETAILS, parameters(elements=elements), "handle")
    fake_archicad.on_tapir_command(
        "RefreshElements",
        {"executionResults": [{"success": True}] * 85 + [failure(7)] * 15},
    )
    result = await archicad_call_tool(REFRESH, parameters(elements=reference(source, "detailsOfElements")))
    assert result["summary"]["outcomes"] == {"success": 85, "failed": 15, "upstream_failed": 10, "filtered": 0}
    assert result["summary"]["errorGroups"][0]["count"] == 15
    assert fake_archicad.calls[-1] == ("RefreshElements", {"elements": elements[:100]})

    errors = (
        await result_read(result["resultHandle"], ReadSelection(view="errors"), maxEntries=100)
    ).structured_content
    assert [entry["value"]["coordinate"] for entry in errors["entries"]] == list(range(85, 110))
    assert errors["entries"][-1]["value"]["state"] == "upstream_failed"
    assert errors["entries"][0]["value"]["error"]["code"] == 7

    fake_archicad.on_tapir_command("GetDetailsOfElements", {"detailsOfElements": elements[:85]})
    chained = await archicad_call_tool(
        DETAILS,
        parameters(elements=reference(result, "executionResults", view="inputs")),
        "handle",
    )
    assert fake_archicad.calls[-1] == ("GetDetailsOfElements", {"elements": elements[:85]})
    assert chained["summary"]["outcomes"] == {"success": 85, "failed": 0, "upstream_failed": 25, "filtered": 0}
    assert len(fake_archicad.calls) == 3


async def test_write_input_view_extracts_identifiers_instead_of_acknowledgements(fake_archicad):
    inputs = [
        {**item(1), "infoString": "Keep"},
        {**item(2), "infoString": "Reject"},
        {**item(1), "infoString": "Duplicate"},
    ]
    fake_archicad.on_tapir_command(
        "SetElementInfoStrings", {"executionResults": [{"success": True}, failure(), {"success": True}]}
    )
    written = await archicad_call_tool("elements_set_element_info_strings", parameters(elements=inputs))
    with pytest.raises(ToolError, match="Resolved result references"):
        await archicad_call_tool(DETAILS, parameters(elements=reference(written, "executionResults")))
    assert len(fake_archicad.calls) == 1
    fake_archicad.on_tapir_command("GetDetailsOfElements", {"detailsOfElements": [item(1), item(1)]})
    read = await archicad_call_tool(DETAILS, parameters(elements=reference(written, view="inputs")))
    assert [slot["state"] for slot in read["detailsOfElements"]] == ["success", "upstream_failed", "success"]
    assert fake_archicad.calls[-1][1]["elements"] == [item(1), item(1)]
    inspection = (await result_read(written["resultHandle"], ReadSelection(view="inputs"))).structured_content
    assert [entry["value"]["input"] for entry in inspection["entries"]] == inputs


async def test_nested_refs_and_literal_values_validate_before_dispatch(fake_archicad):
    fake_archicad.on_tapir_command("GetAddOnVersion", {"version": "result:literal"})
    assert (await archicad_call_tool("app_get_add_on_version", {"port": 19723})) == {"version": "result:literal"}
    origin = await archicad_call_tool("app_get_add_on_version", {"port": 19723}, "handle")
    fake_archicad.on_tapir_command("SetElementInfoStrings", {"executionResults": [{"success": True}]})
    await archicad_call_tool(
        "elements_set_element_info_strings",
        parameters(elements=[{**item(1), "infoString": reference(origin, "version")}]),
    )
    assert fake_archicad.calls[-1][1]["elements"][0]["infoString"] == "result:literal"
    before = len(fake_archicad.calls)
    for ref in (
        reference(origin, "version", 0),
        reference(origin, "missing"),
        {"$handle": "result:expired"},
        {"$handle": "job:wrong"},
    ):
        with pytest.raises(ToolError):
            await archicad_call_tool(DETAILS, parameters(elements=ref))
    assert len(fake_archicad.calls) == before


def _store_slots(store, slots):
    batch = PositionalData("elements", BatchResult(tuple(slots)), None)
    result = StoredResult({"elements": batch.view()}, {"kind": "positional"}, batch)
    job = store.submit("fixture_source", 19723, {}, lambda _: Completion(result, "requested", {}))
    job.future.result(timeout=2)
    return {"resultHandle": job.result_handle}


async def test_shared_axis_masks_literals_rejects_other_batches_and_never_dispatches_all_skipped(
    job_store, fake_archicad
):
    class Params(BaseModel):
        elements: list[dict]
        labels: list[str]

    command = "test_shared_alignment"
    observed = []

    def execute(conn_header, params):
        observed.append(params)
        return {"outcomes": [{"label": label} for label in params.labels]}

    register_tool_for_dispatch(
        execute,
        command,
        command,
        "Tests shared axis",
        params_model=Params,
        metadata=CommandMetadata(
            Presentation.SIZE_BASED, positional=Positional("elements", "outcomes", (), ("labels",))
        ),
    )
    origin = _store_slots(job_store, [BatchSlot.failure("lost"), BatchSlot.success(item(1)), BatchSlot.filtered()])
    ref = reference(origin, "elements")
    output = await archicad_call_tool(command, parameters(elements=ref, labels=["left", "middle", "right"]))
    assert observed[0].labels == ["middle"]
    assert [slot["state"] for slot in output["outcomes"]] == ["upstream_failed", "success", "filtered"]
    other = _store_slots(
        job_store, [BatchSlot.success("left"), BatchSlot.success("middle"), BatchSlot.success("right")]
    )
    with pytest.raises(ToolError, match="different batch"):
        await archicad_call_tool(command, parameters(elements=ref, labels=reference(other, "elements")))
    skipped = _store_slots(job_store, [BatchSlot.filtered(), BatchSlot.failure("lost")])
    output = await archicad_call_tool(command, parameters(elements=reference(skipped, "elements"), labels=["a", "b"]))
    assert [slot["state"] for slot in output["outcomes"]] == ["filtered", "upstream_failed"]
    assert len(observed) == 1
    assert await archicad_call_tool(DETAILS, parameters(elements=[])) == {"detailsOfElements": []}
    assert not fake_archicad.calls


async def test_projection_cardinality_is_a_failed_job(fake_archicad):
    fake_archicad.on_tapir_command("GetDetailsOfElements", {"detailsOfElements": []})
    with pytest.raises(ToolError, match="Unexpected execution error"):
        await archicad_call_tool(DETAILS, parameters(elements=[item(1)]))
    handle = (await archicad_get_job())["jobs"][0]["jobHandle"]
    assert (await archicad_get_job(handle))["status"] == "failed"
    assert len(fake_archicad.calls) == 1


async def test_concurrent_calls_keep_source_positions_and_payloads_isolated(job_store, fake_archicad):
    left = _store_slots(job_store, [BatchSlot.success(item(1)), BatchSlot.failure("Left gap")])
    right = _store_slots(job_store, [BatchSlot.filtered(), BatchSlot.failure("Right gap"), BatchSlot.success(item(2))])
    observed = []

    def dispatch(command, parameters):
        observed.append((command, parameters))
        return {"executionResults": [{"success": True}]}

    fake_archicad.core.post_tapir_command = dispatch
    first, second = await asyncio.gather(
        archicad_call_tool(REFRESH, parameters(elements=reference(left, "elements")), "inline"),
        archicad_call_tool(REFRESH, parameters(elements=reference(right, "elements")), "inline"),
    )
    assert [slot["state"] for slot in first["executionResults"]] == ["success", "upstream_failed"]
    assert [slot["state"] for slot in second["executionResults"]] == ["filtered", "upstream_failed", "success"]
    assert sorted(args["elements"][0]["elementId"]["guid"] for _, args in observed) == [
        item(1)["elementId"]["guid"],
        item(2)["elementId"]["guid"],
    ]
    assert all(set(args) == {"elements"} for _, args in observed)


async def test_unaligned_creation_exposes_output_errors_and_forwards_only_returned_ids(fake_archicad):
    fake_archicad.on_tapir_command("CreateSlabs", {"elements": [item(1), failure(9), item(2)]})
    # The contract deliberately makes no claim about the origins of those IDs.
    source = await archicad_call_tool("elements_create_slabs", parameters(slabsData=[]))
    assert source["summary"]["errorGroups"][0]["code"] == 9
    assert source["summary"]["outcomes"]["failed"] == 1
    data = (await result_read(source["resultHandle"], ReadSelection(paths=[["elements", 1]]))).structured_content
    assert data["entries"][0]["value"] == failure(9)
    errors = (await result_read(source["resultHandle"], ReadSelection(view="errors"))).structured_content
    assert errors["entries"][0]["value"]["coordinate"] == 1
    fake_archicad.on_tapir_command("GetDetailsOfElements", {"detailsOfElements": [item(1), item(2)]})
    fresh = await archicad_call_tool(DETAILS, parameters(elements=reference(source, "elements")))
    assert fresh["detailsOfElements"][1] == {"coordinate": 1, "state": "upstream_failed"}
    assert fake_archicad.calls[-1][1]["elements"] == [item(1), item(2)]


async def test_matrix_uses_multiconn_sparse_dispatch_with_row_and_cell_errors(fake_archicad):
    api = Mock()
    api.read_header_metadata.return_value = SimpleNamespace(tapir_info=SimpleNamespace(version="2.0.0"))
    fake_archicad.unified = SimpleNamespace(utilities=SimpleNamespace(property=PropertyUtilities(api)))
    property_api = api.tapir.property
    property_api.get_property_values_of_elements.return_value = [
        tapir.ErrorItem(error=tapir.Error(code=9, message="Element failed")),
        tapir.PropertyValuesArrayItem(
            propertyValues=[
                tapir.PropertyValueArrayItem(propertyValue=tapir.PropertyValue(value="03.14")),
                tapir.PropertyValueArrayItem(propertyValue=tapir.PropertyValue(value="<Undefined>")),
                tapir.PropertyValueErrorItem(
                    error=tapir.Error(code=1, message="Not available or not evaluated property"),
                    isAvailable=False,
                ),
            ]
        ),
    ]
    ids = [item(2), item(2)]
    props = [item(3, "property"), item(1, "property"), item(3, "property")]
    args = parameters(elements=ids, properties=props, useSIUnits=True)
    read = await archicad_call_tool(READ_GRID, args, "handle")
    assert read["summary"]["dimensions"] == [2, 3]
    assert read["summary"]["rowErrors"] == 1
    assert read["summary"]["affectedRows"] == 2
    assert read["summary"]["outcomes"]["failed"] == 5
    assert {g["category"] for g in read["summary"]["errorGroups"]} == {
        "archicad_error",
        "property_undefined",
        "property_unavailable",
    }
    rows = (
        await result_read(read["resultHandle"], ReadSelection(rows=[1], columns=[0, 2], view="outcomes"))
    ).structured_content
    assert rows["entries"][0]["value"] == {"coordinate": [1, 0], "state": "success", "value": "03.14"}
    assert rows["entries"][1]["value"]["error"]["category"] == "property_unavailable"
    assert property_api.get_property_values_of_elements.call_args.kwargs == {
        "include_availability": True,
        "use_si_units": True,
    }
    property_api.set_property_values_of_elements.return_value = [
        tapir.FailedExecutionResult(error=tapir.Error(code=7, message="Write denied")),
    ]
    write = await archicad_call_tool(WRITE_GRID, parameters(grid=reference(read)))
    assert write["summary"]["outcomes"] == {"success": 0, "failed": 1, "upstream_failed": 5, "filtered": 0}
    submitted = property_api.set_property_values_of_elements.call_args.args[0]
    assert len(submitted) == 1 and submitted[0].propertyValue.value == "03.14"
    assert submitted[0].elementId.guid == UUID(int=2) and submitted[0].propertyId.guid == UUID(int=3)
    reread = (
        await result_read(read["resultHandle"], ReadSelection(paths=[["elements"], ["properties"]]))
    ).structured_content
    assert [entry["value"] for entry in reread["entries"]] == ids + props
    with pytest.raises(ToolError, match="acknowledgement"):
        await archicad_call_tool(WRITE_GRID, parameters(grid=reference(write)))
    with pytest.raises(ToolError, match="Expected 3"):
        await archicad_call_tool(
            WRITE_GRID, parameters(grid={"elements": ids, "properties": props, "values": [["a"], ["b"]]})
        )
    property_api.set_property_values_of_elements.assert_called_once()


async def test_matrix_projection_preserves_300_positions_and_skips_empty_dispatch(job_store, fake_archicad):
    api = Mock()
    api.read_header_metadata.return_value = SimpleNamespace(tapir_info=SimpleNamespace(version="2.0.0"))
    fake_archicad.unified = SimpleNamespace(utilities=SimpleNamespace(property=PropertyUtilities(api)))
    property_api = api.tapir.property
    cell = tapir.PropertyValueArrayItem(propertyValue=tapir.PropertyValue(value="1.25"))
    missing = tapir.PropertyValueErrorItem(error=tapir.Error(code=1, message="Missing"))
    property_api.get_property_values_of_elements.return_value = [
        tapir.PropertyValuesArrayItem(
            propertyValues=[missing if 3 * row + column < 10 else cell for column in range(3)]
        )
        for row in range(100)
    ]
    args = parameters(
        elements=[item(i + 1) for i in range(100)], properties=[item(i + 1, "property") for i in range(3)]
    )
    source = await archicad_call_tool(READ_GRID, args, "handle")
    property_api.set_property_values_of_elements.return_value = [
        tapir.SuccessfulExecutionResult(success=True)
    ] * 280 + [tapir.FailedExecutionResult(error=tapir.Error(code=8, message="Denied"))] * 10
    result = await archicad_call_tool(WRITE_GRID, parameters(grid=reference(source)))
    assert result["summary"]["dimensions"] == [100, 3]
    assert result["summary"]["outcomes"] == {"success": 280, "failed": 10, "upstream_failed": 10, "filtered": 0}
    assert len(property_api.set_property_values_of_elements.call_args.args[0]) == 290
    small = await archicad_call_tool(
        READ_GRID, parameters(elements=[], properties=args["params"]["properties"]), "handle"
    )
    empty = await archicad_call_tool(WRITE_GRID, parameters(grid=reference(small)))
    assert empty["summary"]["dimensions"] == [0, 3]
    property_api.get_property_values_of_elements.assert_called_once()
    property_api.set_property_values_of_elements.assert_called_once()

    batch = _store_slots(
        job_store,
        [BatchSlot.success(item(1)), BatchSlot.failure("Missing identifier")],
    )
    with pytest.raises(ToolError, match="axis needs every identifier"):
        await archicad_call_tool(
            READ_GRID, parameters(elements=reference(batch, "elements"), properties=args["params"]["properties"])
        )


async def test_matrix_inline_data_matches_the_registered_result_model(fake_archicad):
    api = Mock()
    api.read_header_metadata.return_value = SimpleNamespace(tapir_info=SimpleNamespace(version="2.0.0"))
    fake_archicad.unified = SimpleNamespace(utilities=SimpleNamespace(property=PropertyUtilities(api)))
    api.tapir.property.get_property_values_of_elements.return_value = [
        tapir.PropertyValuesArrayItem(
            propertyValues=[
                tapir.PropertyValueArrayItem(propertyValue=tapir.PropertyValue(value="2.5")),
                tapir.PropertyValueArrayItem(propertyValue=tapir.PropertyValue(value="<Undefined>")),
            ]
        )
    ]
    data = await archicad_call_tool(
        READ_GRID, parameters(elements=[item(1)], properties=[item(1, "property"), item(2, "property")])
    )
    assert data["rows"][0]["cells"][1]["error"]["category"] == "property_undefined"
    model = get_tool_entry(READ_GRID).output_model
    assert model.model_validate(data).model_dump(mode="json", by_alias=True, exclude_unset=True) == data


async def test_admitted_reference_finishes_after_source_eviction(job_store, fake_archicad):
    fake_archicad.on_tapir_command("GetSelectedElements", {"elements": [item(1)]})
    source = await archicad_call_tool("elements_get_selected_elements", {"port": 19723})
    job_store.settings = JobSettings(async_threshold_seconds=0.01, max_completed_jobs=1)
    entered, release = Event(), Event()
    dispatch = fake_archicad.core.post_tapir_command

    def blocked(command, parameters):
        if command == "GetDetailsOfElements":
            entered.set()
            assert release.wait(5)
            return {"detailsOfElements": parameters["elements"]}
        return dispatch(command, parameters)

    fake_archicad.core.post_tapir_command = blocked
    pending = await archicad_call_tool(DETAILS, parameters(elements=reference(source, "elements")), "handle")
    try:
        assert await asyncio.to_thread(entered.wait, 2)
        fake_archicad.on_tapir_command("GetAddOnVersion", {"version": "2"})
        await archicad_call_tool("app_get_add_on_version", {"port": 19723}, "handle")
        with pytest.raises(ToolError, match="expired"):
            await result_read(source["resultHandle"])
    finally:
        release.set()
    async with asyncio.timeout(5):
        while (finished := await archicad_get_job(pending["jobHandle"]))["status"] == "running":
            pass
    assert finished["summary"]["outcomes"]["success"] == 1
    assert (await archicad_get_job(pending["jobHandle"])) == finished
    with pytest.raises(ToolError, match="jobHandle"):
        await archicad_get_job(finished["resultHandle"])
    with pytest.raises(ToolError, match="resultHandle"):
        await result_read(pending["jobHandle"])


async def test_bounded_large_text_and_selection_specific_continuation(job_store, fake_archicad):
    job_store.settings = replace(job_store.settings, result_budget=ResultBudget(500, 1000, 1600))
    text = "ő🙂<|endoftext|>" * 100
    fake_archicad.on_tapir_command("GetAddOnVersion", {"version": text, "other": 2})
    result = await archicad_call_tool("app_get_add_on_version", {"port": 19723}, "inline")
    assert result["deliveryReason"] == "byte_limit"
    selection = ReadSelection(paths=[["version"], ["other"]])
    current = None
    chunks = []
    other = None
    while True:
        page = await result_read(result["resultHandle"], selection, maxEntries=5, continuation=current)
        encoded = page.content[0].text
        assert len(encoded.encode("utf-8")) <= 1600 and token_count(encoded) <= 500
        for entry in page.structured_content["entries"]:
            if entry["path"] == ["version"]:
                assert entry["textOffset"] == sum(map(len, chunks))
                chunks.append(entry["value"])
            else:
                other = entry["value"]
        if not page.structured_content["truncated"]:
            break
        current = page.structured_content["continuation"]
        with pytest.raises(ToolError, match="Invalid continuation"):
            await result_read(result["resultHandle"], ReadSelection(paths=[["version"]]), continuation=current)
    assert "".join(chunks) == text and other == 2
    assert len(fake_archicad.calls) == 1


async def test_delivery_boundaries_and_reviewed_preference():
    metadata = CommandMetadata(Presentation.SIZE_BASED)
    root = {"value": "<|endoftext|> Éléments"}
    raw = '{"value":"<|endoftext|> Éléments"}'
    tokens, size = token_count(raw), len(raw.encode("utf-8"))
    assert delivery_reason(root, metadata, ResultMode.AUTO, ResultBudget(tokens, tokens, size)) is None
    assert delivery_reason(root, metadata, ResultMode.AUTO, ResultBudget(tokens - 1, tokens, size)) == "token_limit"
    assert delivery_reason(root, metadata, ResultMode.INLINE, ResultBudget(tokens, tokens, size - 1)) == "byte_limit"
    prefer = CommandMetadata(Presentation.HANDLE_PREFERRED, inline_if_true="dryRun")
    assert delivery_reason(root, prefer, ResultMode.AUTO, ResultBudget()) == "command_preference"
    assert delivery_reason(root, prefer, ResultMode.INLINE, ResultBudget()) is None
    assert delivery_reason({**root, "dryRun": True}, prefer, ResultMode.AUTO, ResultBudget()) is None


async def test_count_only_variant_stays_inline_but_identifier_results_use_handle(fake_archicad):
    command = "elements_get_elements_by_criteria"
    fake_archicad.on_tapir_command("GetElementsByCriteria", {"count": 3})
    assert await archicad_call_tool(command, parameters(countOnly=True)) == {"count": 3}
    fake_archicad.on_tapir_command("GetElementsByCriteria", {"count": 1, "elements": [item(1)]})
    result = await archicad_call_tool(command, parameters())
    assert result["summary"]["itemCount"] == 1 and result["notices"]["count"] == 1


async def test_handle_preserves_warning_samples_and_bounds_grouped_errors(fake_archicad):
    fake_archicad.on_tapir_command(
        "GetMissingAttributes",
        {"missingAttributes": [], "warnings": ["Missing layer: " + "abcdef" * 200]},
    )
    warning = await archicad_call_tool("attributes_get_missing_attributes", parameters(), "handle")
    assert warning["notices"]["warnings"]["sample"].startswith("Missing layer")
    assert warning["notices"]["warnings"]["truncated"] is True

    elements = [item(i + 1) for i in range(12)]
    fake_archicad.on_tapir_command(
        "RefreshElements",
        {"executionResults": [failure(i + 1) for i in range(10)] + [failure(10)] * 2},
    )
    result = await archicad_call_tool(REFRESH, parameters(elements=elements))
    assert len(result["summary"]["errorGroups"]) == 8
    assert result["summary"]["omittedErrorGroups"] == 2
    assert result["summary"]["omittedErrors"] == 4


async def test_output_schema_and_references_are_opt_in_and_match_normalized_results():
    assert archicad_get_command_schema(DETAILS).model_dump().keys() == {"name", "input_schema"}
    details = archicad_get_command_schema(DETAILS, include_output=True)
    item_schema = details.output_schema["properties"]["detailsOfElements"]["items"]["oneOf"]
    assert [entry["properties"]["state"].get("const") for entry in item_schema[:2]] == ["success", "failed"]
    args = details.input_schema
    ref = args["$defs"]["TapirResultReference"]
    assert set(ref["properties"]) == {"$handle", "path", "view"}
    assert args["properties"]["params"]["anyOf"][-1]["$ref"] == "#/$defs/TapirResultReference"
    write = archicad_get_command_schema(WRITE_GRID, include_output=True)
    assert set(write.output_schema["properties"]) == {"elements", "properties", "rows"}


async def test_recursive_output_schema_keeps_upstream_refs_resolvable():
    schema = archicad_get_command_schema("navigator_get_navigator_item_tree", include_output=True).output_schema

    def refs(node):
        if isinstance(node, dict):
            if "$ref" in node:
                yield node["$ref"]
            for value in node.values():
                yield from refs(value)
        elif isinstance(node, list):
            for value in node:
                yield from refs(value)

    assert list(refs(schema))
    for pointer in refs(schema):
        target = schema
        for key in pointer.removeprefix("#/").split("/"):
            target = target[key.replace("~1", "/").replace("~0", "~")]
        assert target
    graph = {
        key: {pointer.rsplit("/", 1)[-1] for pointer in refs(definition)} for key, definition in schema["$defs"].items()
    }

    def circular(key, visited):
        return key in visited or any(circular(child, {*visited, key}) for child in graph[key])

    assert any(circular(key, set()) for key in graph)
