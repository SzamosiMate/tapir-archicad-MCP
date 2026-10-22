"""In-Process Script Sandbox for relational and geometric calculations.

Allows AI agents to execute local Python scripts with pre-authenticated Archicad
bindings (conn, acc, act, STORAGE_SETS), eliminating multi-turn tool loops.
"""

from __future__ import annotations

import contextlib
import io
import json
import logging
import math
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from caracara_archicad_mcp.app import mcp
from caracara_archicad_mcp.context import multi_conn_instance
from caracara_archicad_mcp.result_registry import STORAGE_SETS, ResultRegistry

log = logging.getLogger(__name__)


def _clean_code_snippet(code: str) -> str:
    """Strip markdown code block delimiters if present."""
    code = code.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines).strip()
    return code


def _resolve_archicad_bindings(port: int = 19723) -> tuple[Any, Any, Any]:
    """Resolve pre-authenticated conn, acc, and act bindings for the given port."""
    conn = None
    acc = None
    act = None

    # Try multi_conn_instance context var
    with contextlib.suppress(Exception):
        multi_conn = multi_conn_instance.get()
        from multiconn_archicad import Port

        if Port(port) in multi_conn.active:
            conn = multi_conn.active[Port(port)]

    # Try archicad ACConnection fallback if conn is still None
    if conn is None:
        with contextlib.suppress(Exception):
            from archicad import ACConnection

            conn = ACConnection.connect(port)

    if conn is not None:
        acc = getattr(conn, "commands", None) or getattr(conn, "core", None)
        act = getattr(conn, "types", None)

    if act is None:
        with contextlib.suppress(Exception):
            import archicad

            act = getattr(archicad, "Types", None)

    return conn, acc, act


@mcp.tool(
    name="run_script",
    title="Run Python Script in Archicad Sandbox",
    description=(
        "Executes a Python code snippet locally in-process with pre-authenticated Archicad bindings. "
        "Eliminates multi-turn tool loops for relational or geometric calculations. "
        "Available bindings in scope: "
        "- conn: Active Archicad connection object "
        "- acc: Archicad commands interface (conn.commands or conn.core) "
        "- act: Archicad types interface (conn.types) "
        "- STORAGE_SETS: In-RAM dictionary of active element sets (set_id -> list of elements) "
        "- ResultRegistry: Helper class to register, retrieve, or count sets "
        "- math: Standard Python math library for geometric math "
        "- json: Standard Python json library "
        "Standard output (print statements) is captured and returned as a concise summary."
    ),
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def run_script(
    code: str,
    port: int | None = None,
    raise_errors: bool = False,
) -> str:
    """Execute Python code snippet locally with pre-authenticated Archicad bindings."""
    target_port = port or 19723
    cleaned_code = _clean_code_snippet(code)

    conn, acc, act = _resolve_archicad_bindings(target_port)

    # Prepare execution scope
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    scope: dict[str, Any] = {
        "conn": conn,
        "acc": acc,
        "act": act,
        "STORAGE_SETS": STORAGE_SETS,
        "ResultRegistry": ResultRegistry,
        "math": math,
        "json": json,
        "port": target_port,
    }

    try:
        with contextlib.redirect_stdout(stdout_buffer), contextlib.redirect_stderr(stderr_buffer):
            exec(cleaned_code, scope)  # noqa: S102
    except Exception as e:
        stdout_content = stdout_buffer.getvalue()
        stderr_content = stderr_buffer.getvalue()
        error_type = type(e).__name__
        error_msg = f"{error_type}: {e}"
        log.warning(f"Error in run_script execution: {error_msg}")

        summary = f"Execution failed with {error_msg}"
        if stdout_content:
            summary = f"Stdout before failure:\n{stdout_content.strip()}\n\n{summary}"
        if stderr_content:
            summary = f"{summary}\nStderr:\n{stderr_content.strip()}"

        if raise_errors:
            raise ToolError(summary) from e
        return summary

    stdout_content = stdout_buffer.getvalue()
    if stdout_content.strip():
        return stdout_content.strip()

    # If nothing printed, check if result or output variable was assigned
    if "result" in scope and scope["result"] is not None:
        return str(scope["result"])
    if "output" in scope and scope["output"] is not None:
        return str(scope["output"])

    return "Script executed successfully with no stdout output."
