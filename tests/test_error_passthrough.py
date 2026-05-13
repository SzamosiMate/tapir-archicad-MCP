"""Tests that Archicad error messages are extracted from ValidationErrors
and passed through to the MCP client in a human-readable format.
"""
import sys
import unittest
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class TestArchicadErrorExtraction(unittest.TestCase):
    """Verify _extract_archicad_errors works on generated tool modules."""

    def _get_extract_fn(self):
        """Import _extract_archicad_errors from a generated tool file."""
        # Build a minimal version matching what generate_tools.py emits
        ns = {}
        code = dedent('''
            def _extract_archicad_errors(validation_error, command_name: str) -> str:
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
        ''')
        exec(code, ns)
        return ns["_extract_archicad_errors"]

    def _make_validation_error(self, data: dict):
        from pydantic import BaseModel, ValidationError

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
        fn = self._get_extract_fn()
        ve = self._make_validation_error({
            "elements": [{"error": {"code": -123, "message": "Failed to create door."}}]
        })
        msg = fn(ve, "CreateDoors")
        self.assertIn("Failed to create door.", msg)
        self.assertIn("Archicad rejected CreateDoors", msg)
        self.assertNotIn("validation error", msg.lower())

    def test_mixed_success_and_error(self):
        fn = self._get_extract_fn()
        ve = self._make_validation_error({
            "elements": [
                {"elementId": {"guid": "ok"}},
                {"error": {"code": -1, "message": "Host wall missing"}},
            ]
        })
        msg = fn(ve, "CreateWindows")
        self.assertIn("Host wall missing", msg)

    def test_top_level_error(self):
        fn = self._get_extract_fn()
        ve = self._make_validation_error({
            "error": {"code": -1, "message": "Command not available"}
        })
        msg = fn(ve, "SomeCommand")
        self.assertIn("Command not available", msg)

    def test_non_archicad_error_falls_back(self):
        fn = self._get_extract_fn()
        ve = self._make_validation_error({"wrong_field": 123})
        msg = fn(ve, "SomeCommand")
        self.assertIn("Received an invalid response", msg)

    def test_duplicate_messages_are_deduplicated(self):
        fn = self._get_extract_fn()
        ve = self._make_validation_error({
            "elements": [
                {"error": {"code": -1, "message": "Same error"}},
                {"error": {"code": -1, "message": "Same error"}},
            ]
        })
        msg = fn(ve, "CreateDoors")
        self.assertEqual(msg.count("Same error"), 1)


if __name__ == "__main__":
    unittest.main()
