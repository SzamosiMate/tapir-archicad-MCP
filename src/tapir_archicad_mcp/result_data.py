"""The retained result graph and lazy views shared by references and inspection."""

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from mcp.types import ImageContent
from multiconn_archicad.utilities.results.batch_results import BatchError, BatchGrid, BatchResult, BatchSlot, SlotState
from multiconn_archicad.utilities.results.property_errors import PropertyUnavailableError, PropertyUndefinedError
from pydantic import BaseModel, Field, JsonValue, NonNegativeInt

from tapir_archicad_mcp.metadata_types import CommandMetadata


class ResultError(BaseModel):
    category: str
    code: int | str
    message: str
    causes: list["ResultError"] = Field(default_factory=list)


class Success[C, T](BaseModel):
    coordinate: C
    state: Literal["success"]
    value: T


class Failure[C](BaseModel):
    coordinate: C
    state: Literal["failed"]
    error: ResultError


class Skipped[C](BaseModel):
    coordinate: C
    state: Literal["upstream_failed", "filtered"]


CellCoordinate = tuple[NonNegativeInt, NonNegativeInt]


class MatrixRow[T](BaseModel):
    index: NonNegativeInt
    cells: list[Success[CellCoordinate, T] | Failure[CellCoordinate] | Skipped[CellCoordinate]]
    error: ResultError | None = None


class MatrixData[E, P, T](BaseModel):
    elements: list[E]
    properties: list[P]
    rows: list[MatrixRow[T]]


def json_value(value: Any) -> Any:
    return value.model_dump(mode="json", by_alias=True, exclude_unset=True) if isinstance(value, BaseModel) else value


_PROPERTY_ERRORS = {
    PropertyUndefinedError: "property_undefined",
    PropertyUnavailableError: "property_unavailable",
}


def error_category(error: BatchError) -> str:
    return _PROPERTY_ERRORS.get(type(error), "archicad_error")


def error_data(error: BatchError) -> dict:
    return {
        "category": error_category(error),
        "code": error.code,
        "message": error.message,
        "causes": ErrorList(error.causes),
    }


def state_name(state: SlotState) -> str:
    return "failed" if state is SlotState.ERROR else state.value


def slot_data(coordinate: int | tuple[int, int], slot: BatchSlot) -> dict:
    data = {"coordinate": coordinate, "state": state_name(slot.state)}
    if slot.is_success:
        data["value"] = json_value(slot.value)
    if slot.is_error:
        data["error"] = error_data(slot.error)
    return data


class IndexedView(Sequence):
    """A lazy sequence with an absolute coordinate for every item."""

    def __init__(self, indices: Sequence[int], get_item):
        self.indices = indices
        self.get_item = get_item

    def __len__(self) -> int:
        return len(self.indices)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return IndexedView(self.indices[index], self.get_item)
        return self.get_item(self.indices[index])


class ErrorList(IndexedView):
    def __init__(self, errors: tuple[BatchError, ...]):
        super().__init__(range(len(errors)), lambda i: error_data(errors[i]))


@dataclass(frozen=True)
class PositionalData:
    field: str
    outcomes: BatchResult
    inputs: tuple | None
    input_identity_fields: tuple[str, ...] = ()
    output_identity_fields: tuple[str, ...] = ()

    def view(self) -> IndexedView:
        return IndexedView(range(len(self.outcomes.slots)), lambda i: slot_data(i, self.outcomes.slots[i]))


@dataclass(frozen=True)
class MatrixResult:
    elements: Sequence
    properties: Sequence
    grid: BatchGrid
    use_si_units: bool | None = None

    def __post_init__(self):
        if len(self.grid.rows) != len(self.elements) or self.grid.width != len(self.properties):
            raise ValueError("Property grid dimensions did not match the supplied element and property axes.")

    def view(self, rows: Sequence[int] | None = None, columns: Sequence[int] | None = None) -> dict:
        rows = range(len(self.elements)) if rows is None else rows
        columns = range(len(self.properties)) if columns is None else columns

        def row_data(i: int) -> dict:
            row = self.grid.rows[i]
            return {
                "index": i,
                "cells": IndexedView(columns, lambda j: slot_data((i, j), row.slots[j])),
                "error": error_data(row.error) if row.error is not None else None,
            }

        data = {
            "elements": IndexedView(rows, lambda i: json_value(self.elements[i])),
            "properties": IndexedView(columns, lambda j: json_value(self.properties[j])),
            "rows": IndexedView(rows, row_data),
        }
        if self.use_si_units is not None:
            data["useSIUnits"] = self.use_si_units
        return data


@dataclass(frozen=True)
class StoredResult:
    data: Mapping[str, Any] | MatrixResult
    summary: dict
    batch: PositionalData | None = None
    output_batches: Mapping[str, PositionalData] = field(default_factory=dict)

    def root(self) -> Mapping[str, Any]:
        return self.data.view() if isinstance(self.data, MatrixResult) else self.data


def is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def as_argument(value: Any) -> JsonValue:
    if isinstance(value, ImageContent):
        return value.data
    if isinstance(value, Mapping):
        return {key: as_argument(item) for key, item in value.items()}
    if is_sequence(value):
        return [as_argument(item) for item in value]
    return json_value(value)


class OutcomeSummary:
    MAX_GROUPS = 8
    MAX_TEXT = 220

    def __init__(self):
        self.totals = dict.fromkeys(map(state_name, SlotState), 0)
        self.groups: dict[tuple, dict] = {}
        self.omitted = Counter()

    def add(self, slot: BatchSlot, unit: str):
        state = state_name(slot.state)
        self.totals[state] += 1
        if slot.is_error:
            self.add_error(slot.error, state, unit)

    def add_error(self, error: BatchError, state: str, unit: str):
        category = error_category(error)
        key = (state, unit, category, error.code)
        if key in self.groups:
            self.groups[key]["count"] += 1
        elif len(self.groups) < self.MAX_GROUPS:
            # Escape control characters through normal JSON serialization and bound the sample.
            message = " ".join(error.message[: self.MAX_TEXT].split())
            self.groups[key] = {
                "state": state,
                "unit": unit,
                "category": category,
                "code": error.code[: self.MAX_TEXT] if isinstance(error.code, str) else error.code,
                "count": 1,
                "message": message,
            }
        else:
            self.omitted[key] += 1

    def data(self) -> dict:
        return {
            "outcomes": self.totals,
            "errorGroups": list(self.groups.values()),
            "omittedErrorGroups": len(self.omitted),
            "omittedErrors": sum(self.omitted.values()),
        }


def matrix_result(matrix: MatrixResult) -> StoredResult:
    outcomes = OutcomeSummary()
    row_errors = 0
    affected_elements = 0
    for row in matrix.grid.rows:
        if row.error is not None:
            row_errors += 1
            outcomes.add_error(row.error, "failed", "row")
        if any(slot.is_error or slot.is_upstream_failed for slot in row.slots):
            affected_elements += 1
        for slot in row.slots:
            outcomes.add(slot, "cell")
    return StoredResult(
        matrix,
        {
            "kind": "matrix",
            "dimensions": [len(matrix.elements), len(matrix.properties)],
            "outcomeUnit": "cell",
            "rowErrors": row_errors,
            "affectedRows": affected_elements,
            **(
                {"valueType": "string", "useSIUnits": matrix.use_si_units}
                if matrix.use_si_units is not None
                else {"valueType": "acknowledgement"}
            ),
            **outcomes.data(),
        },
    )


def ordinary_summary(data: Mapping, metadata: CommandMetadata) -> dict:
    summary: dict[str, Any] = {"kind": "ordinary", "dataType": "object"}
    if metadata.count_field and is_sequence(items := data.get(metadata.count_field)):
        summary["itemCount"] = len(items)
    return summary
