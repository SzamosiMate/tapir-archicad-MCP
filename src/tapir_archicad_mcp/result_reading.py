"""Inspect bounded pieces of a retained result without dispatching a command."""

import hmac
from collections.abc import Iterator, Mapping, Sequence
from itertools import chain, islice
from typing import Annotated, Any, Literal

from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult
from pydantic import BaseModel, ConfigDict, Field, model_validator

from tapir_archicad_mcp.jobs import JobStore
from tapir_archicad_mcp.references import Index, Path, select
from tapir_archicad_mcp.result_budget import token_count
from tapir_archicad_mcp.result_data import IndexedView, MatrixResult, StoredResult, error_data, is_sequence, slot_data
from tapir_archicad_mcp.tool_results import ByteLimitExceeded, Encoded, encode

_MAX_READ_IMAGES = 8


class IndexRange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: Index = 0
    stop: Index | None = Field(None, description="Exclusive stop. Omit to read through the end.")

    @model_validator(mode="after")
    def check_order(self):
        if self.stop is not None and self.stop < self.start:
            raise ValueError("Range stop must be at or after start.")
        return self


Indices = Annotated[list[Index], Field(max_length=256)] | IndexRange


class ReadSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paths: list[Path] = Field(default_factory=lambda: [[]], min_length=1, max_length=16)
    indices: Indices | None = Field(None, description="Indices or range on each selected list or on a positional axis.")
    rows: Indices | None = Field(None, description="Selected matrix row indices or range.")
    columns: Indices | None = Field(None, description="Selected matrix column indices or range.")
    view: Literal["data", "outcomes", "successes", "errors", "inputs"] = "data"


def _indices(selection: Indices | None, length: int, label: str) -> Sequence[int]:
    if selection is None:
        return range(length)
    if isinstance(selection, list):
        if any(index >= length for index in selection):
            raise ToolError(f"{label} contains an index outside the stored length {length}.")
        return selection
    stop = length if selection.stop is None else selection.stop
    if stop > length or selection.start > length:
        raise ToolError(f"{label} range exceeds the stored length {length}.")
    return range(selection.start, stop)


def _coordinates(value: Sequence, selection: Indices | None):
    indices = _indices(selection, len(value), "indices")
    for i in indices:
        yield value.indices[i] if isinstance(value, IndexedView) else i, i


def _selected(result: StoredResult, selection: ReadSelection) -> Iterator[tuple[list, Any]]:
    matrix = result.data if isinstance(result.data, MatrixResult) else None
    matrix_slice = selection.rows is not None or selection.columns is not None
    if matrix_slice and (matrix is None or selection.paths != [[]] or selection.indices is not None):
        raise ToolError("Use rows and columns with a matrix result and the root path, without indices.")
    if selection.view == "data":
        root = (
            matrix.view(
                _indices(selection.rows, len(matrix.elements), "rows"),
                _indices(selection.columns, len(matrix.properties), "columns"),
            )
            if matrix_slice
            else result.root()
        )
        values = [(path, select(root, path)) for path in selection.paths]
        if selection.indices is not None:
            for _, value in values:
                if not is_sequence(value):
                    raise ToolError("indices requires a list at every selected path.")
                _indices(selection.indices, len(value), "indices")
        return _data_items(values, selection.indices)
    if selection.view == "inputs" and (result.batch is None or result.batch.inputs is None):
        raise ToolError("This result does not retain positional originating inputs. Matrix axes are available in data.")
    if matrix is not None and selection.paths == [[]] and selection.indices is None:
        rows = _indices(selection.rows, len(matrix.elements), "rows")
        columns = _indices(selection.columns, len(matrix.properties), "columns")
        return _matrix_items(matrix, selection.view, rows, columns)
    batches = dict(result.output_batches)
    if result.batch is not None:
        batches[result.batch.field] = result.batch
    options = {result.batch.field: result.batch} if selection.view == "inputs" else batches
    if not options:
        raise ToolError("This outcome view requires a known batch or a matrix selected by rows and columns.")
    if selection.paths == [[]]:
        chosen = list(options.values())
    else:
        chosen = []
        for path in selection.paths:
            if len(path) != 1 or path[0] not in options:
                raise ToolError(f"Choose the root or a known outcome field from {list(options)!r}.")
            chosen.append(options[path[0]])
    groups = [(batch, _indices(selection.indices, len(batch.outcomes.slots), "indices")) for batch in chosen]
    return (entry for batch, indices in groups for entry in _batch_items(batch, selection.view, indices))


def _data_items(values, indices: Indices | None):
    for path, value in values:
        if is_sequence(value):
            for coordinate, index in _coordinates(value, indices):
                yield [*path, coordinate], value[index]
            if not value and indices is None:
                yield path, []
        else:
            yield path, value


def _included(slot, view: str) -> bool:
    if view == "successes":
        return slot.is_success
    if view == "errors":
        return slot.is_error or slot.is_upstream_failed
    return True


def _batch_items(batch, view: str, indices):
    for index in indices:
        slot = batch.outcomes.slots[index]
        if _included(slot, view):
            data = slot_data(index, slot)
            if view == "inputs":
                data.pop("value", None)
                if batch.inputs[index] is not None:
                    data["input"] = batch.inputs[index]
            yield [batch.field, index], data


def _matrix_items(matrix: MatrixResult, view: str, rows, columns):
    for row_index in rows:
        row = matrix.grid.rows[row_index]
        if row.error is not None and view in {"outcomes", "errors"}:
            yield ["rows", row_index, "error"], error_data(row.error)
        for column in columns:
            slot = row.slots[column]
            if _included(slot, view):
                yield ["rows", row_index, "cells", column], slot_data((row_index, column), slot)


def _pieces(path: list, value: Any, limit: int, skip: int = 0) -> Iterator[dict]:
    try:
        encode(value, limit, max_images=_MAX_READ_IMAGES)
    except ByteLimitExceeded:
        if isinstance(value, str):
            # Non-ASCII and JSON escapes can make one character take up to six bytes.
            width = max(1, limit // 6)
            for start in range(skip * width, len(value), width):
                yield {
                    "path": path,
                    "textOffset": start,
                    "textLength": len(value),
                    "value": value[start : start + width],
                }
        elif isinstance(value, Mapping):
            parts = chain.from_iterable(_pieces([*path, key], child, limit) for key, child in value.items())
            yield from islice(parts, skip, None)
        elif is_sequence(value):
            parts = chain.from_iterable(
                _pieces([*path, coordinate], value[index], limit) for coordinate, index in _coordinates(value, None)
            )
            yield from islice(parts, skip, None)
        elif not skip:
            yield {"path": path, "value": value}
    else:
        if not skip:
            yield {"path": path, "value": value}


def _cursor(store: JobStore, key: bytes, position: tuple[int, int]) -> str:
    offset = f"{position[0]}.{position[1]}"
    return f"{offset}.{store.sign_read_cursor(key + offset.encode())}"


def _position(store: JobStore, key: bytes, cursor: str | None) -> tuple[int, int]:
    if cursor is None:
        return 0, 0
    parts = cursor.split(".")
    if len(parts) == 3 and all(len(part) <= 18 and part.isascii() and part.isdecimal() for part in parts[:2]):
        position = (int(parts[0]), int(parts[1]))
        if hmac.compare_digest(_cursor(store, key, position).encode(), cursor.encode()):
            return position
    raise ToolError("Invalid continuation for this result and selection. Reuse the same resultHandle and selection.")


def read_result(
    store: JobStore,
    result_handle: str,
    selection: ReadSelection,
    max_entries: int,
    continuation: str | None,
) -> CallToolResult:
    result = store.get_result(result_handle).result
    key = (result_handle + "\n" + selection.model_dump_json() + "\n").encode()
    start, fragment = _position(store, key, continuation)
    selected = _selected(result, selection)
    budget = store.settings.result_budget
    piece_limit = max(16, min(4096, budget.max_bytes // 4, budget.auto_tokens // 2))
    records = []
    # Each continuation starts at the next selection ordinal and fragment, with
    # original paths preserved even when some outcomes are filtered out.
    for item_number, (path, value) in enumerate(islice(selected, start, None), start):
        skip = fragment if item_number == start else 0
        parts = _pieces(path, value, piece_limit, skip)
        for part_number, entry in enumerate(parts, skip):
            records.append(((item_number, part_number), entry))
            if len(records) > max_entries:
                break
        if len(records) > max_entries:
            break

    def payload(count: int) -> Encoded | None:
        truncated = count < len(records)
        response = {
            "resultHandle": result_handle,
            "entries": [entry for _, entry in records[:count]],
            "truncated": truncated,
        }
        if truncated:
            response["continuation"] = _cursor(store, key, records[count][0])
        try:
            encoded = encode(response, budget.max_bytes, max_images=_MAX_READ_IMAGES)
        except ByteLimitExceeded:
            return None
        return encoded if token_count(encoded.text) <= budget.auto_tokens else None

    high = min(max_entries, len(records))
    if (encoded := payload(high)) is not None:
        return encoded.mcp()
    low = 1
    best = None
    while low < high:
        mid = (low + high) // 2
        if (encoded := payload(mid)) is not None:
            best = encoded
            low = mid + 1
        else:
            high = mid
    if best is not None:
        return best.mcp()
    raise ToolError(
        "This selection does not fit the inspection limits. Select a shorter path or raise the result limits."
    )
