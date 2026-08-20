# Archicad Tapir MCP Server

This project provides a Model Context Protocol (MCP) server for Archicad. It acts as a bridge, allowing AI agents and applications (like Claude for Desktop) to interact with running Archicad instances by wrapping both the community-driven **Tapir API** and the **official Archicad JSON API**.

The server dynamically generates a comprehensive set of **191+** MCP tools from the combined API schemas, enabling fine-grained control over Archicad projects.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()

## Key Features

-   **Pydantic-Powered Runtime Validation & Schema Generation:** Every tool's input and output shapes are backed by rigorous Pydantic models. The server dynamically compiles these into detailed JSON Schemas for the AI agent to inspect, and strictly validates all incoming tool arguments at runtime *before* forwarding them to Archicad. It handles complex models, Union types, and TypeAliases seamlessly.
-   **Progressive Tool Discovery (CLI-style):** The server uses a deterministic workflow (`archicad_list_commands` and `archicad_get_command_schema`) that allows AI agents to list available commands and fetch exact parameter schemas on demand. This avoids flooding the model's context window with large schemas.
-   **No Heavy Machine-Learning Dependencies:** Vector-based search has been removed. The server no longer requires heavy packages like PyTorch, `faiss-cpu`, or `sentence-transformers`, dramatically reducing the package size and eliminating server startup delays.
-   **Massive Toolset, Minimal Footprint:** Provides access to a unified toolset of **191+ commands** by merging the community Tapir API and the official Archicad JSON API.
-   **Flexible Network Transports:** Supports `sse` (Server-Sent Events) and `streamable-http` transports in addition to standard input/output (`stdio`), allowing the server to be run on remote host configurations.
-   **Bearer Token Authentication:** Secures HTTP endpoints when using SSE or Streamable-HTTP via an opt-in token validation middleware (`--token` flag or `TAPIR_MCP_TOKEN` environment variable).
-   **Multi-Instance Control:** Connect to and manage multiple running Archicad instances simultaneously, targeting commands to specific instances via port numbers.
-   **Cross-Platform Support:** Compatible with both Windows and macOS systems.

## Installation & Setup

Follow these steps to get the server running and connected to an MCP client like Claude for Desktop.

### 1. Prerequisites

-   **Python 3.12+** and **`uv`**: Ensure you have a modern version of Python and the `uv` package manager installed.
-   **Archicad & Tapir Add-On**: You must have Archicad running (which includes the official JSON API). To access the full set of community-developed tools, the [Tapir Archicad Add-On](https://github.com/ENZYME-APD/tapir-archicad-automation) must also be installed.
-   **MCP Client**: An application that can host MCP servers, such as [Claude for Desktop](https://www.claude.ai/download) or [Gemini CLI](https://github.com/google-gemini/gemini-cli).

### 2. Configure Your AI Client

Open your client's `config.json` file and add the following configuration. This command works across operating systems:

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

### 3. Claude Desktop extension (optional)

If you prefer not to edit `config.json` by hand, pack this repository as an [MCPB](https://github.com/modelcontextprotocol/mcpb) desktop extension:

```bash
npm install -g @anthropic-ai/mcpb
mcpb validate manifest.json
mcpb pack . tapir-archicad-0.5.4.mcpb
```

Then in Claude Desktop: Settings → Extensions → **Install Extension…** and select the `.mcpb` file. Quit Claude fully and reopen it.

This also covers the Microsoft Store build of Claude Desktop, which does not read the usual `%APPDATA%\Claude\claude_desktop_config.json` path.

`uv` must be on the PATH that Claude Desktop sees. The bundle uses `server.type: "uv"`, so uv provisions Python and installs the locked dependencies. No system Python is required.

The packed extension launches this package's `archicad-server` entry point. It can modify the open Archicad project, export files, and send or receive Teamwork. Treat enabling it like giving the MCP client your Archicad seat.

Icon artwork is the official Tapir mark from [ENZYME-APD/tapir-archicad-automation](https://github.com/ENZYME-APD/tapir-archicad-automation) (`branding/logo/png/tapir_discord_512.png`), MIT, Copyright 2024 Enzyme APD.

## Configuration Options

You can customize the server via CLI flags or environment variables:

| CLI Flag | Environment Variable | Default | Description |
| :--- | :--- | :--- | :--- |
| `--transport` | - | `stdio` | Transport protocol to use (`stdio`, `sse`, or `streamable-http`) |
| `--host` | `TAPIR_MCP_HOST` | `127.0.0.1` | Bind address for HTTP-based transports |
| `--port` | `TAPIR_MCP_PORT` | `8000` | Bind port for HTTP-based transports |
| `--token` | `TAPIR_MCP_TOKEN` | `None` | Optional Bearer token to secure HTTP endpoints |

## Usage

1. **Restart Claude for Desktop** to apply configuration changes.
2. Ensure at least one instance of Archicad is running.
3. The client will initially have access to a small set of core tools. Start by asking the AI to find running Archicad instances:

   > "Can you check what Archicad projects I have running?"

   The AI will call `discovery_list_active_archicads` and report the active instances and their `port` numbers.

4. State your main goal:

   > "Using port 19723, get all the Wall elements from the project."

5. The AI will execute a progressive discovery and calling loop:
   - **Step 1:** It queries `archicad_list_commands` to look up the correct command name for the requested action (identifying `elements_get_elements_by_type`).
   - **Step 2:** It calls `archicad_get_command_schema` with the target command name to retrieve the exact required JSON parameter structure.
   - **Step 3:** It calls `archicad_call_tool` with the command name, the targeted `port`, and the required parameter payload.

## How It Works

The server operates through a layered architecture:

-   **AI Agent (e.g., Claude):** Interprets user prompts and orchestrates tool discovery.
-   **MCP Client (e.g., Claude for Desktop):** Manages the server process and handles communication.
-   **MCP Server (This Project):** Standardizes tool descriptions, parameters, and results, presenting a clean `list`/`schema`/`call` interface.
-   **`multiconn_archicad` Library:** Resolves active socket connections and handles low-level command dispatch to Archicad instances.
-   **Archicad & Tapir Add-On:** Built-in APIs and Tapir Add-on execute commands and return structured data.

## Contributing

Contributions are welcome! Please feel free to submit an issue or open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.