"""Build stored command results and summarize aligned outcomes once."""

from collections.abc import Mapping

from multiconn_archicad.utilities.results.batch_results import BatchResult, normalize_error
from pydantic import ValidationError

from tapir_archicad_mcp.images import retain_images
from tapir_archicad_mcp.result_data import (
    MatrixResult,
    OutcomeSummary,
    PositionalData,
    StoredResult,
    json_value,
    matrix_result,
    ordinary_summary,
)
from tapir_archicad_mcp.tools.preparation import AxisBinding
from tapir_archicad_mcp.tools.tool_registry import ToolRegistryEntry


def _outcome(entry: ToolRegistryEntry, field: str, value):
    if normalize_error(value) is not None or not isinstance(value, Mapping) or "error" not in value:
        return value
    for adapter in entry.error_adapters[field]:
        try:
            return adapter.validate_python(value)
        except ValidationError:
            continue
    raise ValueError(f"Unrecognized item error in the declared {field} outcome list.")


def _outcomes(entry: ToolRegistryEntry, field: str, values) -> list:
    if not isinstance(values, list):
        raise TypeError(f"Expected an array in the declared {field} outcome list.")
    return [_outcome(entry, field, value) for value in values]


def normalize(entry: ToolRegistryEntry, raw, axis: AxisBinding | None) -> StoredResult:
    if isinstance(raw, MatrixResult):
        return matrix_result(raw)
    data = json_value(raw) if raw is not None else {}
    if not isinstance(data, dict):
        raise TypeError("Expected an object as the command result.")
    data = retain_images(entry, data)
    outcome_views = {}
    additional = OutcomeSummary()
    for declaration in entry.metadata.outcome_lists:
        if (values := data.get(declaration.field)) is not None:
            normalized = BatchResult.from_items(_outcomes(entry, declaration.field, values))
            outcome_views[declaration.field] = PositionalData(declaration.field, normalized, None)
            for slot in normalized.slots:
                additional.add(slot, declaration.unit)
    if contract := entry.metadata.positional:
        field = contract.output_field
        values = _outcomes(entry, field, data[field])
        outcomes = axis.outcomes.project_successes(values) if axis is not None else BatchResult.from_items(values)
        batch = PositionalData(
            field,
            outcomes,
            axis.inputs if axis is not None else None,
            contract.input_identity_fields,
            contract.output_identity_fields,
        )
        summary = OutcomeSummary()
        for slot in outcomes.slots:
            summary.add(slot, "item")
        return StoredResult(
            {**data, field: batch.view()},
            {"kind": "positional", "itemCount": len(outcomes.slots), "outcomeUnit": "item", **summary.data()},
            batch,
            outcome_views,
        )
    summary = ordinary_summary(data, entry.metadata)
    if outcome_views:
        total = sum(len(view.outcomes.slots) for view in outcome_views.values())
        summary.update(
            {
                "outcomeUnit": entry.metadata.outcome_lists[0].unit,
                "itemCount": summary.get("itemCount", total),
                **additional.data(),
            }
        )
    return StoredResult(data, summary, output_batches=outcome_views)
