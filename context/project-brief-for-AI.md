### **Comprehensive Project Brief: Python MCP Server for Archicad's APIs**

**1. High-Level Goal & Vision**

The primary objective of this project is to create a robust, scalable, and user-friendly Python-based Model Context Protocol (MCP) server. This server will act as a comprehensive wrapper for Archicad's automation APIs, including both the community-driven Tapir API and the official Archicad JSON API.

The ultimate vision is to provide AI agents with a complete and intelligent toolkit to automate complex architectural workflows within Archicad, effectively bridging the gap between natural language commands and procedural architectural design tasks.

---

**2. Current Architecture and Implemented Features**

The project is built on a solid foundation that already addresses several key challenges in API wrapping and multi-instance management.

*   **Foundation:** The server is built using the `mcp-sdk`'s `FastMCP` class, providing a high-level, decorator-based approach for defining MCP tools. It leverages an `async` lifespan manager to handle the initialization and shutdown of core services.

*   **Multi-Instance Connection Management:** The server uses the powerful `multiconn_archicad` library to discover, connect to, and manage multiple running instances of Archicad simultaneously. A `MultiConn` instance is managed via a context variable, making it accessible to all tool functions.

*   **Generator-Centric Workflow (`scripts/generate_tools.py`):** The cornerstone of the current architecture is a sophisticated code generation script. Instead of manual implementation, this script automates the creation of MCP tools by:
    1.  **Fetching Metadata:** It programmatically fetches the latest command schemas and details directly from the `multiconn_archicad` repository.
    2.  **Logical Grouping:** It intelligently groups the 80+ Tapir commands into logical categories (e.g., "elements", "attributes", "project") and creates separate, organized Python files for each group.
    3.  **Strongly-Typed Tool Generation:** It generates the Python code for each MCP tool, complete with `@mcp.tool()` decorators, correct function signatures, and strong type hints using the pre-generated Pydantic models from the library. This ensures that the tools are robust and self-documenting.

*   **Handwritten Core Tools:** The architecture supports a mix of generated and handwritten tools. A crucial custom tool, `discovery_list_active_archicads`, has been implemented to allow the AI agent to find and identify active Archicad instances.

*   **Instance Targeting:** Every generated tool function is designed to accept a `port: int` parameter. This allows the AI agent to explicitly target which Archicad instance a command should be sent to, a critical feature for multi-project workflows.

*   **Robust Server-Side Pagination:** For API commands that can return thousands of results (e.g., `GetAllElements`), the generator already implements a complete, cursor-based pagination system. It automatically creates paginated Pydantic response models and injects the necessary logic and docstrings to guide the AI on how to iterate through large datasets.

---

**3. The Architectural Challenge: The Context Window Problem**

With the addition of the official Archicad JSON API, the total number of tools will exceed 160. Exposing this many tools directly to an LLM is infeasible—it would consume an enormous portion of the context window, drastically increase token costs, and confuse the model, leading to poor performance and unreliable tool selection.

The initial proposed solution, detailed in a previous version of this brief, was a **Multi-Server Dispatcher Architecture**. The idea was to launch a separate server process for each tool group. However, upon further review, this approach was rejected due to significant user experience and architectural drawbacks:
*   **Installation & Management Burden:** Requiring a non-technical user to configure and manage up to 20 separate server processes is impractical.
*   **Workflow Fragmentation:** Most useful workflows require tools from multiple groups (e.g., "elements" and "properties"), forcing the user to know which combination of servers to run.
*   **Lack of Agent Awareness:** The agent, connected to one server, would have no knowledge of tools in other inactive servers and couldn't prompt the user to enable them.
*   **Inconsistent Server Sizes:** The tool groups are imbalanced, ranging from a few tools to over 40, with some schemas being thousands of tokens long on their own.

---

**4. The New Architectural Direction: Intelligent Tool Discovery**

Given the limitations of the multi-server approach, the project will pivot to a more sophisticated and user-friendly **`discover`/`call` architecture**. This pattern keeps the server as a single, easy-to-install entity while intelligently managing the toolset exposed to the AI.

The server will only expose two primary, handwritten tools for interacting with the Archicad APIs:
*   `archicad_discover_tools(query: str) -> list[ToolInfo]`: This tool will perform a semantic search over all available API commands.
*   `archicad_call_tool(name: str, arguments: dict) -> dict`: This tool will act as a dispatcher, executing the specific tool function identified by the `name` parameter.

---

**5. Detailed Action Plan for the Next Version**

1.  **Implement the Intelligent Discovery & Execution Pattern:**
    *   Create the handwritten `archicad_discover_tools` and `archicad_call_tool` functions.
    *   Build a tool registry (a simple Python dictionary) at server startup that maps tool names as strings to their callable Python function objects. The `call_tool` function will use this registry for dispatching.

2.  **Build the Local Semantic Search Index:**
    *   Implement the hybrid caching mechanism for embeddings:
        *   On the server's *first-ever* run, it will use a library like `sentence-transformers` to generate embeddings for all tool descriptions from the `tool_catalog.json`.
        *   This vector index will be saved to a local file (e.g., `tool_index.faiss`).
        *   On all subsequent startups, the server will load the pre-computed index directly into memory for fast startup and search performance.

3.  **Expand and Adapt the Code Generator (`scripts/generate_tools.py`):**
    *   Modify the generator to process commands from both the Tapir API and the official Archicad JSON API.
    *   The generator's primary output will now be a `tool_catalog.json` file. This file will be the comprehensive, searchable database of all tool metadata (name, description, input/output schemas).
    *   The generator will still create the grouped Python tool files, which will be imported by the server to populate the tool registry for the `call_tool` dispatcher.

4.  **Package for Distribution:**
    *   Structure the project for packaging and create a `pyproject.toml` file.
    *   Publish the server as a package on PyPI to dramatically simplify the installation process for end-users (`pip install tapir-archicad-mcp`).

5.  **Statically Enhance Tool Descriptions:**
    *   Review the descriptions for all tools in the source metadata. Where necessary, augment them to be more descriptive and rich with keywords to improve the accuracy of the semantic search.

---

**6. Future Areas for Improvement**

Once the core discovery architecture is implemented and stable, the following advanced features can be explored:

**Advanced State and Data Management for Large-Scale Operations**

While the `discover/call` architecture solves the problem of managing a large number of *tool definitions*, a second, equally critical challenge arises when tool calls return large data payloads (e.g., thousands of Archicad elements). Directly returning this data to the LLM would flood the context window, leading to high costs, slow performance, and potential loss of context.

To address this, the server can be evolved to implement a **"Stateful Handle" architecture**, a pattern analogous to how powerful systems like OpenAI's Code Interpreter operate. Instead of returning raw data, tools will return a lightweight reference, or "handle," to data that is stored and managed within the server's session.

This would involve the following key components:

1.  **Server-Side Session State Cache:** An in-memory cache (e.g., using `cachetools.TTLCache` for automatic memory management) will be implemented. This cache will not store raw lists, but will instead use **Pandas DataFrames** as its core in-memory data structure. This unlocks powerful, standardized, and highly efficient data manipulation capabilities.

2.  **The Handle (`ResultSetInfo` Model):** "Fetch-type" tools (like `GetAllElements`) will be modified to no longer return the full dataset. Instead, they will:
    *   Convert the API response into a Pandas DataFrame.
    *   Store the DataFrame in the session cache with a unique `handle_id`.
    *   Return a compact `ResultSetInfo` Pydantic model to the agent. This object will contain the `handle_id`, item count, a preview of the first few rows, and a data schema description, giving the agent just enough context to plan its next steps.

3.  **A Hybrid Tool Architecture:** The server's toolset will be divided into two categories:
    *   **Auto-Generated "Fetch & Execute" Tools:** The existing generator will be adapted. "Fetch" tools will be wrapped to return handles, and "Execute" tools (like `SetPropertyValuesOfElements`) will be modified to accept a `handle_id` as their payload argument.
    *   **Handwritten Generic "Data Manipulation" Tools:** A new, powerful suite of generic tools will be created to allow the agent to operate on the data in the cache. These tools will be thin, safe wrappers around standard Pandas operations, such as:
        *   `data_filter(handle_id, query_string)`: Uses `DataFrame.query()` to create filtered subsets.
        *   `data_transform(handle_id, expression)`: Uses `DataFrame.eval()` to modify or create new data columns.
        *   `data_merge(left_handle, right_handle, on_field)`: Uses `pandas.merge()` to combine datasets.
        *   `data_assemble_payload(...)`: A generic tool for restructuring data from multiple handles into the complex Pydantic models required by "Execute" tools.

This architecture enables the agent to perform complex, multi-step data processing workflows (e.g., fetch all elements, filter for walls, get their properties, transform the property values, and then execute an update) entirely on the server-side. This keeps the context window clean, handles massive datasets with ease, and provides the agent with an incredibly powerful and scalable toolkit for real-world automation.

*   **Graph-Based Discovery:** Model the relationships and dependencies between tools as a weighted graph. For example, `GetElementsByType` has a strong relationship with `GetPropertiesOfElements`. This graph could be used to bias the search results, allowing `discover_tools` to not only return tools that match the query but also to suggest logical next steps in a workflow.
*   **Dynamic, Context-Aware Tool Descriptions:** Investigate techniques to modify tool descriptions at runtime. Based on the user's prompt or the session's tool call history, the description could be augmented with contextual examples or details, providing the LLM with even more relevant information to improve its tool selection accuracy.