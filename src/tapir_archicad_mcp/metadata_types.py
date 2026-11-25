"""Runtime command contracts. The maintained table imports only this module."""

from dataclasses import dataclass
from enum import StrEnum


class Presentation(StrEnum):
    SIZE_BASED = "size_based"
    HANDLE_PREFERRED = "handle_preferred"


class MatrixAdapter(StrEnum):
    READ = "property_grid_read"
    WRITE = "property_grid_write"


@dataclass(frozen=True)
class Positional:
    """One ordered API outcome per submitted item on the controlling axis."""

    input_field: str
    output_field: str
    error_types: tuple[str, ...]
    shared_inputs: tuple[str, ...] = ()
    input_identity_fields: tuple[str, ...] = ()
    output_identity_fields: tuple[str, ...] = ()
    empty_outputs: tuple[str, ...] = ()
    partial_output_types: tuple[str, ...] = ()


@dataclass(frozen=True)
class OutcomeList:
    field: str
    error_types: tuple[str, ...]
    unit: str = "item"


@dataclass(frozen=True)
class CommandMetadata:
    presentation: Presentation
    positional: Positional | None = None
    adapter: MatrixAdapter | None = None
    # Explicit counts and delivery exceptions for ordinary outputs.
    count_field: str | None = None
    summary_fields: tuple[str, ...] = ()
    inline_if_true: str | None = None
    handle_if_list: str | None = None
    outcome_lists: tuple[OutcomeList, ...] = ()
    reason: str = ""
    reviewed: str = ""
