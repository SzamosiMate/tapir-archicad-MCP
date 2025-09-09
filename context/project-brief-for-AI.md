### **Comprehensive Project Brief: Python MCP Server for Archicad's APIs**

**1. High-Level Goal & Vision**

The primary objective of this project is to create a robust, scalable, and user-friendly Python-based Model Context Protocol (MCP) server. This server will act as a comprehensive wrapper for Archicad's automation APIs.

The ultimate vision is to provide AI agents with a complete and intelligent toolkit to automate complex architectural workflows within Archicad, effectively bridging the gap between natural language commands and procedural architectural design tasks.

---

**2. Implemented Architecture**

The project is built on a sophisticated architecture designed to be both powerful for automation and simple for end-users to install and operate. To solve the critical challenge of managing an infeasibly large number of API commands (over 130), the server implements an intelligent **`discover`/`call`** pattern. This keeps the server as a single entity while intelligently managing the toolset exposed to the AI.

The server only exposes three primary, handwritten tools to the AI client:
*   `discovery_list_active_archicads()`: Finds and identifies all running Archicad instances.
*   `archicad_discover_tools(query: str)`: Performs a semantic search over all available API commands.
*   `archicad_call_tool(name: str, arguments: dict)`: Acts as a dispatcher to execute the specific tool function identified by the `name` parameter.

This architecture is supported by the following implemented features:

*   **Foundation:** The server is built using the `mcp-sdk`'s `FastMCP` class and the `multiconn-archicad` library to manage connections to multiple Archicad instances simultaneously.

*   **Generator-Centric Workflow:** A code generation script (`scripts/generate_tools.py`) automatically creates the internal toolset. It processes command schemas from **both the community Tapir API and the official Archicad JSON API**, creating a unified, de-duplicated catalog of **over 130 tools**. Where functionality overlaps, the more feature-rich community command is prioritized to ensure the best tool is always presented. This catalog is used for both discovery and dispatching.

*   **Intelligent Semantic Search:** A powerful, 100% local search engine has been implemented using `sentence-transformers` and `faiss-cpu`.
    *   **Enhanced Context:** Search accuracy is maximized by generating vector embeddings from a rich combination of the tool's name, its description, and meaningful keywords (parameter names, enum values) automatically extracted from its Pydantic schema.
    *   **Adaptive Filtering:** Search results are filtered using a sophisticated "Top-Score Relative Threshold." This dynamic method adapts to the query's quality and only returns tools that are highly relevant to the top match, dramatically reducing noise.
    *   **Automatic Index Versioning:** The search index is cached locally and versioned with a SHA2-256 hash of the tool catalog, ensuring it is automatically and transparently rebuilt if the underlying tools change.

*   **Robust Packaging and Distribution:** The project is structured and **published to PyPI** as a proper Python package. This enables a dramatically simplified user experience, where the server can be run with a universal command (`uvx tapir-archicad-mcp`) that works for every user without requiring any local configuration.

*   **Professional-Grade Logging:** A dual-channel logging system sends diagnostic messages to `stderr` and the MCP data stream to `stdout`, preventing log messages from corrupting communication. Logs are also written to a persistent, rotating file, ensuring they are always available for debugging.

---

**3. Next Steps and Future Vision**

#### **Immediate Roadmap: Post-Release Priorities**

With the initial version now published, the focus shifts to enhancing the user experience and robustness of the toolset.

1.  **Enhance API Command Descriptions:** Review the original descriptions for all 130+ API commands in the source metadata. With a much larger toolset now available, enriching descriptions with more keywords and clearer explanations of use-cases is the top priority to improve the accuracy and relevance of the semantic search for public users.

2.  **Develop Example Workflows and Guides:** Create a set of practical examples and user guides that demonstrate how to chain `discover` and `call` commands to accomplish common architectural tasks (e.g., "Select all walls on the active story and change their composite structure"). This will help users understand the server's full potential.

#### **Advanced Architectural Goals**

Once the core functionality is mature, the following long-term features can be explored:

*   **Stateful Handle Architecture:** To manage large data payloads (e.g., thousands of elements) without flooding the LLM's context window, the server can be evolved to return lightweight "handles" to data stored server-side in Pandas DataFrames. This would unlock powerful, server-side data manipulation capabilities for the AI.
*   **Graph-Based Discovery:** Model the relationships between tools as a graph to allow `discover_tools` to not only find matching tools but also suggest logical next steps in a workflow.