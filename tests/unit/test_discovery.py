import pytest
from tapir_archicad_mcp.tools.custom.functions import (
    archicad_list_commands,
    archicad_get_command_schema,
)
from tapir_archicad_mcp.tools.custom.models import CommandOverview, CommandSchema


def test_archicad_list_commands(fake_archicad):
    """
    Test that the list command returns a populated list of CommandOverview models
    without leaking the full JSON schemas.
    """
    commands = archicad_list_commands()

    assert isinstance(commands, list)
    assert len(commands) > 0

    # Check the structure of the returned objects
    first_cmd = commands[0]
    assert isinstance(first_cmd, CommandOverview)
    assert first_cmd.name
    assert first_cmd.description

    # Ensure generated tools were successfully picked up by the registry
    all_names = [cmd.name for cmd in commands]
    assert "elements_get_selected_elements" in all_names
    assert "elements_create_slabs" in all_names


def test_archicad_get_command_schema_valid(fake_archicad):
    """
    Test that requesting a schema for a valid tool returns the correct
    CommandSchema model containing the input properties.
    """
    schema_result = archicad_get_command_schema("elements_get_selected_elements")

    assert isinstance(schema_result, CommandSchema)
    assert schema_result.name == "elements_get_selected_elements"

    # Verify the input_schema dict was built correctly
    assert "type" in schema_result.input_schema
    assert schema_result.input_schema["type"] == "object"

    # Every tool must require at least a 'port'
    assert "port" in schema_result.input_schema["properties"]
    assert "port" in schema_result.input_schema["required"]


def test_archicad_get_command_schema_invalid(fake_archicad):
    """
    Test that requesting a schema for a non-existent tool raises a
    ValueError with a helpful error message to guide the LLM.
    """
    with pytest.raises(ValueError, match="not found. Please use 'archicad_list_commands'"):
        archicad_get_command_schema("made_up_command_name")