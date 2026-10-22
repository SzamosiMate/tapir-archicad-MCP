from __future__ import annotations

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from caracara_archicad_mcp.result_registry import ResultRegistry
from caracara_archicad_mcp.script_sandbox import run_script


@pytest.fixture(autouse=True)
def clean_registry():
    """Ensure ResultRegistry is clean before and after each test."""
    ResultRegistry.clear()
    yield
    ResultRegistry.clear()


@pytest.mark.asyncio
async def test_run_script_executes_multistep_geometric_calculation():
    """Sandboxed test executing a multi-step calculation and verifying output capture."""
    # Pre-populate STORAGE_SETS with element geometry
    wall_data = [
        {"elementId": {"guid": "w-1"}, "beg": {"x": 0.0, "y": 0.0}, "end": {"x": 10.0, "y": 0.0}},
        {"elementId": {"guid": "w-2"}, "beg": {"x": 10.0, "y": 0.0}, "end": {"x": 10.0, "y": 8.0}},
        {"elementId": {"guid": "w-3"}, "beg": {"x": 10.0, "y": 8.0}, "end": {"x": 0.0, "y": 0.0}},
    ]
    set_id = ResultRegistry.register(wall_data, element_type="Wall")

    code = f"""
walls = STORAGE_SETS['{set_id}']
total_length = 0.0

for w in walls:
    dx = w['end']['x'] - w['beg']['x']
    dy = w['end']['y'] - w['beg']['y']
    length = math.sqrt(dx**2 + dy**2)
    total_length += length

print(f"Wall Count: {{len(walls)}}")
print(f"Total Perimeter: {{total_length:.2f}}m")
"""

    output = await run_script(code)

    assert "Wall Count: 3" in output
    assert "Total Perimeter: 30.81m" in output


@pytest.mark.asyncio
async def test_run_script_preauthenticated_bindings_in_scope(fake_archicad):
    """Verifies that conn, acc, act, and STORAGE_SETS are bound and available in scope."""
    code = """
print(f"Product Version: {conn.product_info.version}")
print(f"Has Acc: {acc is not None}")
print(f"Storage Sets Type: {type(STORAGE_SETS).__name__}")
"""

    output = await run_script(code, port=fake_archicad.port)

    assert "Product Version: 28" in output
    assert "Has Acc: True" in output
    assert "Storage Sets Type: dict" in output


@pytest.mark.asyncio
async def test_run_script_error_containment_division_by_zero():
    """Verifies that runtime exceptions are safely contained without crashing."""
    code = """
x = 10
y = 0
z = x / y
"""

    output = await run_script(code)

    assert "Execution failed with ZeroDivisionError: division by zero" in output


@pytest.mark.asyncio
async def test_run_script_error_containment_syntax_error():
    """Verifies that syntax errors are safely contained and reported."""
    code = "for x in"

    output = await run_script(code)

    assert "Execution failed with SyntaxError" in output


@pytest.mark.asyncio
async def test_run_script_error_containment_captures_stdout_before_error():
    """Verifies that partial stdout emitted before an exception is captured in the error summary."""
    code = """
print("Phase A: Geometry loaded successfully")
print("Phase B: Initializing boundary solver")
raise ValueError("Invalid polygon self-intersection at vertex 3")
"""

    output = await run_script(code)

    assert "Phase A: Geometry loaded successfully" in output
    assert "Phase B: Initializing boundary solver" in output
    assert "Execution failed with ValueError: Invalid polygon self-intersection at vertex 3" in output


@pytest.mark.asyncio
async def test_run_script_strips_markdown_code_fences():
    """Verifies that code wrapped in Markdown fences (```python ... ```) executes cleanly."""
    code = """```python
val = math.pow(2, 8)
print(f"Calculated: {val}")
```"""

    output = await run_script(code)

    assert "Calculated: 256.0" in output


@pytest.mark.asyncio
async def test_run_script_result_variable_fallback():
    """Verifies that assigning to 'result' variable returns its string representation when no print output."""
    code = """
radius = 5.0
result = math.pi * (radius ** 2)
"""

    output = await run_script(code)

    assert output.startswith("78.5398")


@pytest.mark.asyncio
async def test_run_script_raise_errors_option():
    """Verifies that ToolError is raised when raise_errors=True is explicitly requested."""
    with pytest.raises(ToolError, match="ZeroDivisionError"):
        await run_script("1 / 0", raise_errors=True)
