import pytest
from pydantic import BaseModel, ConfigDict, ValidationError

from tapir_archicad_mcp.validation_errors import format_validation_error


class Point(BaseModel):
    x: float
    y: float


class Wall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    begCoordinate: Point
    height: float | None = None
    name: str | None = None


class Params(BaseModel):
    walls: list[Wall]


def _error(data: dict) -> ValidationError:
    with pytest.raises(ValidationError) as raised:
        Params.model_validate(data)
    return raised.value


def _lines(message: str) -> list[str]:
    return message.splitlines()


def test_many_errors_of_one_type_give_one_line():
    message = format_validation_error("elements_create_walls", _error({"walls": [{}] * 1000}))

    lines = _lines(message)
    assert lines[0] == "Invalid arguments provided for tool 'elements_create_walls': 1000 errors of 1 type."
    assert lines[1] == (
        "- missing (1000): Field required at walls.0.begCoordinate, walls.1.begCoordinate, walls.2.begCoordinate, …"
    )
    assert len(lines) == 3


def test_types_keep_first_occurrence_order():
    error = _error({"walls": [{"begCoordinate": {"x": 0, "y": 0}, "height": "high"}, {"other": 1}]})

    lines = _lines(format_validation_error("elements_create_walls", error))

    assert lines[0].endswith("3 errors of 3 types.")
    assert [line.split(" (")[0] for line in lines[1:4]] == ["- float_parsing", "- missing", "- extra_forbidden"]


def test_more_than_max_types_adds_a_tail_line():
    error = _error({"walls": [{"begCoordinate": {"x": 0, "y": 0}, "height": "high"}, {"other": 1}]})

    lines = _lines(format_validation_error("elements_create_walls", error, max_types=2))

    assert len(lines) == 5
    assert lines[3] == "...and 1 more error type."


def test_locations_are_listed_without_ellipsis_when_they_fit():
    lines = _lines(format_validation_error("elements_create_walls", _error({"walls": [{}, {}]})))

    assert lines[1] == "- missing (2): Field required at walls.0.begCoordinate, walls.1.begCoordinate"


def test_input_values_are_not_echoed():
    error = _error({"walls": [{"begCoordinate": {"x": 0, "y": 0}, "height": "secret-123"}]})

    assert "secret-123" not in format_validation_error("elements_create_walls", error)


def test_schema_hint_is_the_last_line():
    lines = _lines(format_validation_error("elements_create_walls", _error({"walls": [{}]})))

    assert lines[-1] == "Call archicad_get_command_schema('elements_create_walls') for the exact schema."
