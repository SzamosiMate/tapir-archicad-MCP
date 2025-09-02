### **Comprehensive Project Brief: Python MCP Server for Archicad's APIs**

**1. High-Level Goal & Vision**

The primary objective of this project is to create a robust, scalable, and user-friendly Python-based Model Context Protocol (MCP) server. This server will act as a comprehensive wrapper for Archicad's automation APIs.

The ultimate vision is to provide AI agents with a complete and intelligent toolkit to automate complex architectural workflows within Archicad, effectively bridging the gap between natural language commands and procedural architectural design tasks.

---

**2. Implemented Architecture**

The project is built on a sophisticated architecture designed to be both powerful for automation and simple for end-users to install and operate. To solve the critical challenge of managing an infeasibly large number of API commands (160+), the server implements an intelligent **`discover`/`call`** pattern. This keeps the server as a single entity while intelligently managing the toolset exposed to the AI.

The server only exposes three primary, handwritten tools to the AI client:
*   `discovery_list_active_archicads()`: Finds and identifies all running Archicad instances.
*   `archicad_discover_tools(query: str)`: Performs a semantic search over all available API commands.
*   `archicad_call_tool(name: str, arguments: dict)`: Acts as a dispatcher to execute the specific tool function identified by the `name` parameter.

This architecture is supported by the following implemented features:

*   **Foundation:** The server is built using the `mcp-sdk`'s `FastMCP` class and the `multiconn-archicad` library to manage connections to multiple Archicad instances simultaneously.

*   **Generator-Centric Workflow:** A code generation script (`scripts/generate_tools.py`) automatically creates the internal toolset. It fetches the latest command schemas, generates plain Python functions for each command, and populates an in-memory catalog that is used for both discovery and dispatching.

*   **Intelligent Semantic Search:** A powerful, 100% local search engine has been implemented using `sentence-transformers` and `faiss-cpu`.
    *   **Enhanced Context:** Search accuracy is maximized by generating vector embeddings from a rich combination of the tool's name, its description, and meaningful keywords (parameter names, enum values) automatically extracted from its Pydantic schema.
    *   **Adaptive Filtering:** Search results are filtered using a sophisticated "Top-Score Relative Threshold." This dynamic method adapts to the query's quality and only returns tools that are highly relevant to the top match, dramatically reducing noise.
    *   **Automatic Index Versioning:** The search index is cached locally and versioned with a SHA256 hash of the tool catalog, ensuring it is automatically and transparently rebuilt if the underlying tools change.

*   **Robust Packaging and Distribution:** The project is structured as a proper Python package with a `pyproject.toml` file. This enables a dramatically simplified user experience, where the server can be run with a universal command (`uvx tapir-archicad-mcp`) that works for every user without requiring them to edit local file paths in their AI client's configuration.

*   **Professional-Grade Logging:** A dual-channel logging system sends diagnostic messages to `stderr` and the MCP data stream to `stdout`, preventing log messages from corrupting communication. Logs are also written to a persistent, rotating file, ensuring they are always available for debugging.

---

**3. Next Steps and Future Vision**

#### **Immediate Roadmap**

The following tasks are the immediate priority to finalize the core feature set and prepare for a public release:

1.  **Publish Package to PyPI:** Finalize the packaging and publish the `tapir-archicad-mcp` package to PyPI. This is the last step to enable the simple `uvx` installation for all users. *(Note: This is contingent on the `multiconn-archicad` dependency being published to PyPI first.)*

2.  **Expand Generator for Official JSON API:** Modify the code generator to process commands from both the community Tapir API and the official Archicad JSON API, bringing the total number of available tools to over 160.

3.  **Statically Enhance Source Descriptions:** Review the original descriptions for all API commands in the source metadata. Where necessary, augment them to be more descriptive and rich with keywords to further improve the accuracy of the semantic search.

#### **Advanced Architectural Goals**

Once the core functionality is complete, the following long-term features can be explored:

*   **Stateful Handle Architecture:** To manage large data payloads (e.g., thousands of elements) without flooding the LLM's context window, the server can be evolved to return lightweight "handles" to data stored server-side in Pandas DataFrames. This would unlock powerful, server-side data manipulation capabilities for the AI.
*   **Graph-Based Discovery:** Model the relationships between tools as a graph to allow `discover_tools` to not only find matching tools but also suggest logical next steps in a workflow.