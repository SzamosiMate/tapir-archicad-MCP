# Archicad Tapir MCP Server

This project provides a Model Context Protocol (MCP) server for Archicad. It acts as a bridge, allowing AI agents and applications (like Claude for Desktop) to interact with running Archicad instances by wrapping the powerful [Tapir JSON API](https://github.com/ENZYME-APD/tapir-archicad-automation).

The server dynamically generates a comprehensive set of over 80 MCP tools from the Tapir API schema, enabling fine-grained control over Archicad projects.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()

> **Disclaimer:** This project is in an early stage of development. It has not been extensively tested and is intended primarily for experimental and educational purposes. Interfaces and functionality may change in future updates. Please use with caution.

## Key Features

-   **Intelligent Tool Discovery:** The server exposes a simple `discover_tools` function that uses a powerful local semantic search engine to find the most relevant Archicad command from a user's natural language query.
-   **Massive Toolset, Minimal Footprint:** Provides access to the entire Tapir API (80+ commands, expanding to 160+) without overwhelming the AI's context window.
-   **100% Local & Private Search:** The semantic search index is built and runs entirely on your machine using `sentence-transformers` and `faiss-cpu`. No data ever leaves your computer, and no API keys are required.
-   **Adaptive & Relevant Results:** Search uses a sophisticated "Top-Score Relative Threshold" to filter out noise and return only the most relevant tools for a given query.
-   **Multi-Instance Control:** Connect to and manage multiple running Archicad instances simultaneously.
-   **Robust & Packaged:** Designed as a proper Python package with a `pyproject.toml`, enabling simple and reliable installation.

## Installation & Setup

Follow these steps to get the server running and connected to an MCP client like Claude for Desktop.

### 1. Prerequisites

-   **Python 3.12+** and **`uv`**: Ensure you have a modern version of Python and the `uv` package manager installed. You can install `uv` with `pip install uv`.
-   **Archicad & Tapir Add-On**: You must have Archicad running with the [Tapir Archicad Add-On](https://github.com/ENZYME-APD/tapir-archicad-automation) installed. The server cannot function without it.
-   **MCP Client**: An application that can host MCP servers, such as [Claude for Desktop](https://www.claude.ai/download) or [Gemini CLI ](https://github.com/google-gemini/gemini-cli)

### 2. Configure Your AI Client

This is now the **only step required**. Open your client's `config.json` file and add the following configuration. This command is universal and works on any operating system without modification.

-   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
-   **Windows:** `%APDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ArchicadTapir": {
      "command": "uvx",
        "args": [
          "--from",
          "tapir-archicad-mcp",
          "archicad-server"
        ]
    }
  }
}
```

**How This Works:**
The `uvx` command (part of the `uv` toolchain) is a powerful utility that automatically handles the entire process for you:
1.  The first time the AI client needs the tool, `uvx` will download the latest version of `tapir-archicad-mcp` from PyPI.
2.  It will install it into a temporary, isolated environment.
3.  It will run the server.

## Usage

1.  **Restart Claude for Desktop** to apply the configuration changes.
2.  Ensure at least one instance of Archicad (with Tapir) is running.
3.  The client will now have access to a small set of core tools. Start by asking it to find the running Archicad instances:

    > "Can you check what Archicad projects I have running?"

    The AI will run `discovery_list_active_archicads` and report the active instances and their `port` numbers.

4.  Now, state your main goal. For example:

    > "Okay, using port 12345, get all the Wall elements from the project."

5.  The AI will now perform the two-step `discover`/`call` workflow:
    *   **First, it will call `archicad_discover_tools`** with a query like `"get all wall elements"`. The server's semantic search will find that the best match is the `elements_get_elements_by_type` tool.
    *   **Second, it will call `archicad_call_tool`**, using the `name="elements_get_elements_by_type"` it just discovered and constructing the necessary `arguments` (including the `port` and `params` with `elementType="Wall"`).
    *   The final result is returned to you.

## How It Works

The server operates through a layered architecture:

-   **AI Agent (e.g., Claude):** Interacts with the user and decides which tools to call.
-   **MCP Client (e.g., Claude for Desktop):** Manages the server process and communication.
-   **Archicad Tapir MCP Server (This Project):** Provides an intelligent abstraction layer over the Tapir API, exposing a simple `discover`/`call` interface.
-   **`multiconn_archicad` Library:** The underlying Python library that handles the low-level communication with Archicad instances.
-   **Archicad & Tapir Add-On:** The final destination that executes the commands.

## Contributing

Contributions are welcome! Please feel free to submit an issue or open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.

