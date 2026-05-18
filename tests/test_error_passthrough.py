"""Tests that Archicad error messages are extracted from ValidationErrors
and passed through to the MCP client in a human-readable format.
"""
import importlib.util
import sys
import unittest
from pathlib import Path

from pydantic import BaseModel, ValidationError

# Import validation.py directly to avoid loading the generated tool files
# (which require a full multiconn_archicad environment).
_VALIDATION_PATH = Path(__file__).resolve().parents[1] / "src" / "tapir_archicad_mcp" / "tools" / "validation.py"
_spec = importlib.util.spec_from_file_location("validation", _VALIDATION_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
extract_archicad_errors = _mod.extract_archicad_errors


class TestArchicadErrorExtraction(unittest.TestCase):
    """Verify extract_archicad_errors produces actionable messages."""

    def _make_validation_error(self, data: dict) -> ValidationError:
        class ElementId(BaseModel):
            guid: str

        class Item(BaseModel):
            elementId: ElementId

        class Result(BaseModel):
            elements: list[Item]

        try:
            Result.model_validate(data)
        except ValidationError as e:
            return e
        self.fail("Expected ValidationError")

    def test_per_element_error_is_extracted(self):
        ve = self._make_validation_error({
            "elements": [{"error": {"code": -123, "message": "Failed to create door."}}]
        })
        msg = extract_archicad_errors(ve, "CreateDoors")
        self.assertIn("Failed to create door.", msg)
        self.assertIn("Archicad rejected CreateDoors", msg)
        self.assertNotIn("validation error", msg.lower())

    def test_mixed_success_and_error(self):
        ve = self._make_validation_error({
            "elements": [
                {"elementId": {"guid": "ok"}},
                {"error": {"code": -1, "message": "Host wall missing"}},
            ]
        })
        msg = extract_archicad_errors(ve, "CreateWindows")
        self.assertIn("Host wall missing", msg)

    def test_top_level_error(self):
        ve = self._make_validation_error({
            "error": {"code": -1, "message": "Command not available"}
        })
        msg = extract_archicad_errors(ve, "SomeCommand")
        self.assertIn("Command not available", msg)

    def test_non_archicad_error_falls_back(self):
        ve = self._make_validation_error({"wrong_field": 123})
        msg = extract_archicad_errors(ve, "SomeCommand")
        self.assertIn("Received an invalid response", msg)

    def test_duplicate_messages_are_deduplicated(self):
        ve = self._make_validation_error({
            "elements": [
                {"error": {"code": -1, "message": "Same error"}},
                {"error": {"code": -1, "message": "Same error"}},
            ]
        })
        msg = extract_archicad_errors(ve, "CreateDoors")
        self.assertEqual(msg.count("Same error"), 1)


if __name__ == "__main__":
    unittest.main()
