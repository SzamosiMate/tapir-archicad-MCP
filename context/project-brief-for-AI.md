---
### **Project: Python MCP Server for Archicad's Tapir API**

**High-Level Goal:**

Create a Python-based Model Context Protocol (MCP) server that acts as a comprehensive wrapper for Archicad's Tapir JSON API. The server codebase should be able to connect to and manage multiple running Archicad instances and expose their functionality as a structured, configurable set of tools to an AI agent.

**Context and Provided Files:**

You are an expert Python developer specializing in AI agents, API integration, and robust software architecture. You will primarily use the pre-generated Pydantic models from the `multiconn_archicad` library and the command metadata from its `_command_details.json` file to build the server.

**Core Architectural Requirements:**

1.  **Multi-Server Dispatcher Architecture:** The project will be a single Python codebase that can be launched as **multiple, distinct MCP server processes**. Each server process will load only a specific "group" of tools (e.g., "elements", "attributes").
    *   This is the primary strategy to manage the AI's context window, allowing users to enable only the toolsets they need.
    *   The tool group will be selected at runtime via a `--group <group_name>` command-line argument.
    *   Users will configure this in their `claude_desktop_config.json` by creating a separate entry for each tool group they wish to activate.

2.  **Granular, Grouped Toolset:** The server will expose all 80+ Tapir commands as **individual, distinct MCP tools**.
    *   Tool names must follow the convention `{short_group}_{command_name_snake}` to provide logical grouping and adhere to the MCP specification's 64-character limit.
    *   A mapping from the full group name (e.g., "Issue Management Commands") to a short name (e.g., "issues") will be used.

3.  **Generator-Centric Workflow:** The core of the project is a code generator script (`scripts/generate_tools.py`) that **wraps** the existing models from the `multiconn_archicad` library, rather than generating models from scratch. The generator is responsible for:
    *   Fetching the latest command metadata from the `multiconn_archicad` repository.
    *   Creating Python files for each command group (e.g., `elements.py`).
    *   Within each file, generating the `@mcp.tool()` decorated Python functions, strongly typed with the imported Pydantic models.
    *   **Implementing Server-Side Pagination:** For API calls that can return thousands of items, the generator implements a robust, cursor-based pagination wrapper.
        *   It uses a configuration dictionary (`PAGINATED_COMMANDS`) to map a command to the specific response field containing the list to paginate. This elegantly handles complex responses with multiple lists.
        *   For these commands, it automatically generates a new Pydantic response model that inherits from the original, includes the sliced list for the current page, and adds an optional `next_page_token: str | None`.
        *   The generated tool functions include logic to cache the full API response on the first request (keyed by port and parameters) and use a generic pagination handler for subsequent requests.
        *   The docstring for every paginated tool is automatically updated to instruct the AI on how to use the `page_token` to iterate through all results.
    *   Ensuring parameters are correctly serialized to JSON using `model_dump(mode='json')`.

4.  **Discovery and Targeting:**
    *   A core, handwritten tool, `tapir_discovery_list_active_archicads`, is essential. It must return a curated list of running Archicad instances, including their `port`, `projectName`, and `projectType` (`teamwork`, `solo`, or `untitled`).
    *   Every generated Tapir tool must accept a `port: int` parameter to allow the AI to target a specific Archicad instance.
    *   The docstring for every generated tool must explicitly mention that the discovery tool should be used to find a valid `port`.

**Future Areas for Improvement:**

Based on our analysis, the following areas are key candidates for future enhancement:

1.  **Enhanced User Configuration:***Solving the Context Window Problem:** We identified that loading all 80+ tools would overwhelm the AI's context window. The final, and most significant, architectural decision was to refactor the project into a **multi-server dispatcher**.
    *   The single codebase can now be launched as multiple, independent server processes.
    *   Each process loads only one group of tools, selected via a `--group` command-line argument.
    *   This allows the end-user to have granular control over which toolsets are active by configuring multiple server entries in their `claude_desktop_config.json` file.

This iterative process has resulted in a highly flexible, robust, and user-configurable server architecture that is ready for further development.