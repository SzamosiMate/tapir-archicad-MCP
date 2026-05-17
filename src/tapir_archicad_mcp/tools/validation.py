from typing import Any, get_origin, Union
from types import UnionType
from pydantic import BaseModel, TypeAdapter


def is_union(obj: Any) -> bool:
    origin = get_origin(obj)
    return origin is Union or origin is UnionType


def validate_result(model_or_type: Any, result_dict: dict) -> Any:
    # Fast path for standard BaseModels
    if isinstance(model_or_type, type) and issubclass(model_or_type, BaseModel):
        return model_or_type.model_validate(result_dict)
    else:
        return TypeAdapter(model_or_type).validate_python(result_dict)