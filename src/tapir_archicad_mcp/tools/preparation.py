"""Resolve result references before validating a command's concrete arguments."""

from dataclasses import dataclass
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad.utilities.results.batch_results import BatchResult, BatchSlot
from pydantic import BaseModel, ValidationError

from tapir_archicad_mcp.jobs import JobStore
from tapir_archicad_mcp.metadata_types import MatrixAdapter
from tapir_archicad_mcp.references import ResultReference, select
from tapir_archicad_mcp.result_data import MatrixResult, PositionalData, StoredResult, as_argument, is_sequence
from tapir_archicad_mcp.tools.tool_registry import ToolRegistryEntry
from tapir_archicad_mcp.validation_errors import format_validation_error


@dataclass(frozen=True)
class ReferenceBinding:
    reference: ResultReference
    source: StoredResult
    batch: PositionalData | None = None


@dataclass(frozen=True)
class AxisBinding:
    outcomes: BatchResult
    inputs: tuple


@dataclass(frozen=True)
class PreparedCall:
    arguments: BaseModel
    references: dict[tuple, ReferenceBinding]
    axis: AxisBinding | None = None


def _batch_values(batch: PositionalData, view: str) -> list:
    if view == "inputs" and batch.inputs is None:
        raise ToolError("This result has no originating input list. Select a result field using view='output'.")
    fields = batch.input_identity_fields if view == "inputs" else batch.output_identity_fields
    values = []
    for index, slot in batch.outcomes.iter_slots():
        if not slot.is_success:
            continue
        value = as_argument(batch.inputs[index] if view == "inputs" else slot.value)
        if fields:
            # Some read commands allow callers to omit identifier fields in a field selection.
            if not isinstance(value, dict) or not all(field in value for field in fields):
                raise ToolError(
                    "The stored item omits its identifier. Request the identifier field or use view='inputs'."
                )
            value = {field: value[field] for field in fields}
        values.append(value)
    return values


def prepare_call(name: str, entry: ToolRegistryEntry, arguments: dict, store: JobStore) -> PreparedCall:
    bindings: dict[tuple, ReferenceBinding] = {}
    contract = entry.metadata.positional

    def resolve(raw: Any, destination: tuple) -> Any:
        if isinstance(raw, list):
            return [resolve(item, (*destination, index)) for index, item in enumerate(raw)]
        if not isinstance(raw, dict):
            return raw
        if "$handle" not in raw:
            return {key: resolve(value, (*destination, key)) for key, value in raw.items()}
        handle = raw["$handle"]
        if isinstance(handle, str) and handle.startswith("job:"):
            raise ToolError("A reference requires a resultHandle. Poll the jobHandle with archicad_get_job.")
        try:
            ref = ResultReference.model_validate(raw)
        except ValidationError as exc:
            raise ToolError(format_validation_error(f"result reference at {list(destination)}", exc)) from None
        source = store.get_result(ref.handle).result
        batch = source.batch
        if ref.view == "output" and len(ref.path) == 1 and isinstance(ref.path[0], str):
            batch = source.output_batches.get(ref.path[0], batch)
        if batch and (ref.path == [batch.field] or (ref.view == "inputs" and not ref.path)):
            if (
                entry.metadata.adapter
                and destination[-1] in {"elements", "properties"}
                and any(not slot.is_success for slot in batch.outcomes.slots)
            ):
                raise ToolError(
                    "A property grid axis needs every identifier. Supply literal IDs, a stored grid axis, "
                    "or a collection with no failed or filtered slots."
                )
            bindings[destination] = ReferenceBinding(ref, source, batch)
            return _batch_values(batch, ref.view)
        if ref.view == "inputs":
            raise ToolError(
                "Use view='inputs' with the positional result field or omit path for its originating inputs."
            )
        bindings[destination] = ReferenceBinding(ref, source)
        if (
            entry.metadata.adapter is MatrixAdapter.WRITE
            and destination == ("params", "grid")
            and not ref.path
            and isinstance(source.data, MatrixResult)
        ):
            if source.data.use_si_units is None:
                raise ToolError("A property write acknowledgement is not a values grid. Reference a property read.")
            return source.data
        return as_argument(select(source.root(), ref.path))

    concrete = dict(arguments)
    if "params" in concrete:
        concrete["params"] = resolve(concrete["params"], ("params",))
    axis_outcomes = None
    parameters = concrete.get("params")
    if contract and isinstance(parameters, dict):
        controlling = bindings.get(("params", contract.input_field))
        submitted = parameters.get(contract.input_field)
        if controlling is not None and controlling.batch is not None:
            source = controlling.batch.outcomes
            positions = [index for index, slot in source.iter_slots() if slot.is_success]
            for field in contract.shared_inputs:
                values = parameters.get(field)
                if values is None:
                    continue
                binding = bindings.get(("params", field))
                if binding and binding.batch:
                    if binding.batch is not controlling.batch:
                        raise ToolError(f"Shared-axis parameter {field!r} references a different batch.")
                    continue
                if binding or not is_sequence(values) or len(values) != len(source.slots):
                    raise ToolError(f"Shared-axis parameter {field!r} needs one literal item per original position.")
                parameters[field] = [values[index] for index in positions]
            axis_outcomes = source
        elif isinstance(submitted, list):
            for field in contract.shared_inputs:
                values = parameters.get(field)
                binding = bindings.get(("params", field))
                if values is not None and (binding or not is_sequence(values) or len(values) != len(submitted)):
                    raise ToolError(f"Shared-axis parameter {field!r} needs one literal item per controlling input.")
            axis_outcomes = BatchResult(tuple(BatchSlot.success(None) for _ in submitted))
    try:
        validated = entry.arguments_model.model_validate(concrete)
    except ValidationError as exc:
        detail = format_validation_error(name, exc)
        if bindings:
            destinations = ", ".join(repr(list(path)) for path in bindings)
            detail = f"Resolved result references at {destinations}. {detail}"
        raise ToolError(detail) from None

    axis = None
    if axis_outcomes is not None:
        # Capture the actual validated inputs, including aliases/coercions used at dispatch.
        validated_values = validated.params.model_dump(mode="json", by_alias=True, exclude_none=True)
        compact = iter(validated_values[contract.input_field])
        axis = AxisBinding(
            axis_outcomes, tuple(next(compact) if slot.is_success else None for slot in axis_outcomes.slots)
        )
    return PreparedCall(validated, bindings, axis)
