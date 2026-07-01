from typing import Any, get_origin, Union
from types import UnionType
from pydantic import BaseModel, TypeAdapter, ValidationError


def is_union(obj: Any) -> bool:
    origin = get_origin(obj)
    return origin is Union or origin is UnionType


def validate_result(model_or_type: Any, result_dict: dict) -> Any:
    # Fast path for standard BaseModels
    if isinstance(model_or_type, type) and issubclass(model_or_type, BaseModel):
        return model_or_type.model_validate(result_dict)
    else:
        return TypeAdapter(model_or_type).validate_python(result_dict)


def extract_archicad_errors(validation_error: ValidationError, command_name: str) -> str:
    """Extract actionable Archicad error messages from a ValidationError.

    When Archicad returns per-element errors (e.g. {"error": {"code": ..., "message": ...}})
    instead of the expected success schema, Pydantic rejects them. This helper pulls out
    the original Archicad messages so the caller gets useful feedback instead of a raw
    Pydantic traceback.
    """
    archicad_messages = []
    for err in validation_error.errors():
        inp = err.get("input")
        if isinstance(inp, dict):
            ac_err = inp.get("error") or inp
            if isinstance(ac_err, dict) and "message" in ac_err:
                archicad_messages.append(ac_err["message"])
    if archicad_messages:
        unique = list(dict.fromkeys(archicad_messages))
        joined = "; ".join(unique)
        return f"Archicad rejected {command_name}: {joined}"
    return f"Received an invalid response from the Archicad API for {command_name}: {validation_error}"