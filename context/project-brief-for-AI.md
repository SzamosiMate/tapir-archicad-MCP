### **Project: Generate a Python MCP Server for Archicad's Tapir API**

**High-Level Goal:**

Create a Python-based Model Context Protocol (MCP) server that acts as a comprehensive wrapper for Archicad's Tapir JSON API. The server should be able to connect to and manage multiple running Archicad instances and expose their functionality as a structured set of tools to an AI agent.

**Context and Provided Files:**

You are an expert Python developer specializing in AI agents, API integration, and robust software architecture. You will be provided with the following files that constitute the `multiconn_archicad` library and the Tapir API definition:

1.  `core_commands.py`: Contains the low-level logic for sending commands to the Archicad JSON API.
2.  `multi_conn.py`: The main class for managing connections to multiple Archicad instances.
3.  Supporting library files (`conn_header.py`, `basic_types.py`, etc.): Core data structures for the connection library.
4.  A **master JSON schema file** (`master_schema.json`): This file defines all available Tapir commands, their parameters, their return values, their descriptions, and their documentation categories. It uses `$ref` for object references.

**Core Architectural Requirements:**

Based on a detailed design discussion, the server **must** adhere to the following architectural principles:

1.  **Single "Meta" Server:** The implementation will be a **single MCP server** that uses the `MultiConn` object from the `multiconn_archicad` library internally. This server will act as a gateway to all available Archicad instances, rather than creating one server per instance.

2.  **Flat, Grouped Toolset:** The server will expose all 80+ Tapir commands as **individual, distinct MCP tools**.
    *   We have decided **against** a single generic `run_command` tool in favor of providing granular control and discoverability.
    *   Tool names **must** follow a prefixing convention based on the command's documentation category from the master schema (e.g., `tapir_layers_create`, `tapir_elements_getDetails`). This provides logical grouping for both the AI and potential user interfaces.

3.  **Static Pydantic Model Generation:** The server's workflow will be built around a **static code generation** step. A Python script will be responsible for reading the `master_schema.json` and generating a `tapir_models.py` file.
    *   This `tapir_models.py` file will contain a Pydantic `BaseModel` for every command's parameters (e.g., `CreateLayersParams`) and every command's result (e.g., `CreateLayersResult`).
    *   This approach is chosen for its performance, type safety, testability, and superior developer experience.

4.  **Discovery and Targeting:**
    *   The server must provide a core helper tool, `list_active_archicads()`, which returns a list of running Archicad instances, including their `port` and `projectName`.
    *   Every generated Tapir tool **must** accept a `port: int` parameter to allow the AI to target a specific Archicad instance.

**Implementation Plan:**

Please provide the complete Python code for the following two key components:

**Part 1: The Code Generator (`generate_mcp_components.py`)**

This script will be the heart of the build process. It should perform two main functions:

1.  **Generate Pydantic Models:**
    *   Read and parse `master_schema.json`.
    *   Correctly handle and resolve all `$ref` references within the schema. The `jsonschema` library is recommended for this.
    *   For each of the 80+ commands, generate two Pydantic model classes: one for its `parameters` and one for its `result`.
    *   Write all generated Pydantic classes into a single file named `tapir_models.py`.
    *   Also, generate a master dictionary `ALL_COMMAND_MODELS` that maps command name strings to their generated `Params` model classes (e.g., `"CreateLayers": CreateLayersParams`).

2.  **Generate MCP Tool Functions:**
    *   For each command, generate the complete Python code for its corresponding `@mcp.tool()` decorated function.
    *   The function signature should be strongly typed using the generated Pydantic models (e.g., `def tool_CreateLayers(port: int, params: CreateLayersParams) -> CreateLayersResult:`).
    *   The function body should contain the logic to call the `multiconn_archicad` library, validate the result against the Pydantic `Result` model, and return it.
    *   Write all generated tool functions into a single file named `tapir_tools.py`.

**Part 2: The Main Server File (`mcp_tapir_server.py`)**

This file will be the main entry point for the MCP server. It should be clean and primarily responsible for wiring everything together.

*   It should use `mcp.server.fastmcp.FastMCP`.
*   It should instantiate the `MultiConn` object on startup.
*   It should import all the generated tools from `tapir_tools.py` and register them with the `FastMCP` instance.
*   It must include the handwritten implementation for the `list_active_archicads()` tool.
*   It should include the `if __name__ == "__main__":` block to make the server runnable.

**Example of a Generated Tool Function (for guidance):**

The code generated for the `CreateLayers` command in `tapir_tools.py` should look conceptually like this:

```python
# In the generated tapir_tools.py

from .tapir_models import CreateLayersParams, CreateLayersResult
from mcp.server.fastmcp import tool
from multiconn_archicad.basic_types import Port

# Note: This is an example. The actual implementation will need access to the 
# multi_conn instance from the main server file. This can be handled by passing it
# or using a global/context variable pattern.

@tool(name="tapir_layers_create")
def tapir_create_layers(port: int, params: CreateLayersParams) -> CreateLayersResult:
    """
    Creates one or more new layers in the project. (Description from schema)
    """
    target_port = Port(port)
    # Assume 'multi_conn' is accessible here
    if target_port not in multi_conn.open_port_headers:
        raise ValueError(f"Port {port} is not a valid Archicad instance.")
    
    conn_header = multi_conn.open_port_headers[target_port]
    result_dict = conn_header.core.post_tapir_command(
        command="CreateLayers",
        parameters=params.model_dump()
    )
    return CreateLayersResult(**result_dict)
```