"""Tests for the generate_tools.py code generation pipeline.

Verifies that generated code uses TypeAdapter-based validation
instead of direct .model_validate() calls, which fails for
TypeAlias union types in multiconn_archicad.
"""
import sys
import unittest
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from generate_tools import (
    _generate_call_block,
    _generate_paginated_model_code,
)


class TestCallBlockGeneration(unittest.TestCase):
    def test_uses_validate_result_helper(self) -> None:
        cmd = {"name_for_api": "DeleteElements", "name_camel": "DeleteElements"}
        block = _generate_call_block(cmd, "DeleteElementsResult", has_params=True, has_result=True,
                                     config=_fake_config())
        self.assertIn("_validate_result(DeleteElementsResult", block)
        self.assertNotIn(".model_validate(", block)

    def test_no_result_returns_none(self) -> None:
        cmd = {"name_for_api": "HighlightElements", "name_camel": "HighlightElements"}
        block = _generate_call_block(cmd, "HighlightElementsResult", has_params=True, has_result=False,
                                     config=_fake_config())
        self.assertIn("return None", block)
        self.assertNotIn("_validate_result", block)


class TestPaginatedModelGeneration(unittest.TestCase):
    def test_inherits_from_base_model(self) -> None:
        code = _generate_paginated_model_code("GetAllElementsResult", "PaginatedGetAllElementsResult", "elements")
        self.assertIn("class PaginatedGetAllElementsResult(BaseModel):", code)
        self.assertIn('extra="allow"', code)
        self.assertNotIn("GetAllElementsResult)", code.split("class")[1].split(":")[0])


def _fake_config():
    from generator_config import ApiSourceConfig
    return ApiSourceConfig(
        name="tapir",
        details_url="",
        model_names_url="",
        output_dir=Path("/tmp"),
        api_call_method="post_tapir_command",
        group_mapping={},
    )


if __name__ == "__main__":
    unittest.main()
