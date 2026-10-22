# Caracara Archicad MCP Server

An extended Model Context Protocol (MCP) server for Archicad automation, based on [tapir-archicad-MCP](https://github.com/SzamosiMate/tapir-archicad-MCP).

It acts as an intelligent bridge, allowing AI agents and applications (like Claude for Desktop, Claude Code, or Gemini CLI) to interact with running Archicad instances by wrapping both the community-driven **Tapir API** and the **official Archicad JSON API**.

The server dynamically generates a comprehensive set of **191+** MCP tools from the combined API schemas, enabling fine-grained, resilient control over Archicad BIM projects.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-fork%20%7C%20active-blue.svg)]()

---

## Extended Caracara Features

In addition to core Tapir MCP capabilities, **Caracara** introduces enhancements designed for high-performance AI agent workflows:

-   **Script Sandboxing (`script_sandbox`):** Execute multi-step batch operations within an isolated, high-speed execution sandbox directly alongside Archicad to avoid round-trip latency.
-   **Field Masking & Projection (`field_masking`):** Selectively filter and project element properties and model hierarchies to drastically reduce token consumption and eliminate context-window bloat.
-   **Polymorphic Meta-Verbs (`meta_verbs`):** High-level semantic actions that simplify complex BIM workflows (querying, transforming, grouping) into ergonomic agent primitives.
-   **Result Registry & Caching (`result_registry`):** Server-side handle storage and virtual element sets for referencing large query results across conversational turns without re-fetching.

---

## Key Features

-   **Pydantic-Powered Runtime Validation & Schema Generation:** Every tool's input and output shapes are backed by rigorous Pydantic models. The server dynamically compiles these into detailed JSON Schemas for the AI agent to inspect, and strictly validates all incoming tool arguments at runtime *before* forwarding them to Archicad. It handles complex models, Union types, and TypeAliases seamlessly.
-   **Progressive Tool Discovery (CLI-style):** The server uses a deterministic workflow (`archicad_list_commands` and `archicad_get_command_schema`) that allows AI agents to list available commands and fetch exact parameter schemas on demand. This avoids flooding the model's context window with large schemas.
-   **No Heavy Machine-Learning Dependencies:** Vector-based search has been removed. The server does not require heavy packages like PyTorch, `faiss-cpu`, or `sentence-transformers`, dramatically reducing package size and eliminating startup delays.
-   **Massive Toolset, Minimal Footprint:** Provides access to a unified toolset of **191+ commands** by merging the community Tapir API and the official Archicad JSON API.
-   **Flexible Network Transports:** Supports `sse` (Server-Sent Events) and `streamable-http` transports in addition to standard input/output (`stdio`), allowing the server to be run on remote host configurations.
-   **Bearer Token Authentication:** Secures HTTP endpoints when using SSE or Streamable-HTTP via an opt-in token validation middleware (`--token` flag or `CARACARA_MCP_TOKEN` / `TAPIR_MCP_TOKEN` environment variable).
-   **Multi-Instance Control:** Connect to and manage multiple running Archicad instances simultaneously, targeting commands to specific instances via port numbers.
-   **Cross-Platform Support:** Compatible with both Windows and macOS systems.

---

## Installation & Setup

Follow these steps to get the server running and connected to an MCP client like Claude for Desktop.

### 1. Prerequisites

-   **Python 3.12+** and **`uv`**: Ensure you have Python 3.12+ and the `uv` package manager installed.
-   **Archicad & Tapir Add-On**: You must have Archicad running (which includes the official JSON API). To access the full set of community-developed tools, the [Tapir Archicad Add-On](https://github.com/ENZYME-APD/tapir-archicad-automation) must also be installed.
-   **MCP Client**: An application that can host MCP servers, such as [Claude for Desktop](https://www.claude.ai/download), Claude Code, or [Gemini CLI](https://github.com/google-gemini/gemini-cli).

### 2. Configure Your AI Client

Open your client's `config.json` file and add the configuration. This configuration works across operating systems:

-   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
-   **Windows:** `%APDATA%\Claude\claude_desktop_config.json`

**Standard deployment (via `uvx`):**
```json
{
  "mcpServers": {
    "ArchicadCaracara": {
      "command": "uvx",
      "args": [
        "--from",
        "caracara-archicad-mcp",
        "caracara-server"
      ]
    }
  }
}
```

**Local development deployment (`pip install -e .`):**
```json
{
  "mcpServers": {
    "ArchicadCaracara": {
      "command": "caracara-server",
      "args": []
    }
  }
}
```

A complete boilerplate configuration snippet is also provided in [`claude_desktop_config.example.json`](claude_desktop_config.example.json).

### 3. One-click install (optional MCP Bundle)

If your client supports [MCP Bundles](https://github.com/modelcontextprotocol/mcpb) you can skip manual configuration. Claude Desktop, Claude Code and MCP for Windows install `.mcpb` files directly.

`uv` still has to be on the PATH your client sees, but it provisions Python and the locked dependencies itself. The bundle can modify the open project, export files, and send or receive Teamwork, so treat installing it like handing your client your Archicad seat.

<details>
<summary>If the bundle will not start</summary>

-   **"Server disconnected", or the install itself fails.** Uninstall the bundle, restart the client, then install it again. Installing over an existing bundle can leave stale state behind that a straight reinstall does not clear.
-   **Nothing happens for the first half minute.** That is uv building the environment, and antivirus scanning or a slow connection stretches it out. Restart the client once before assuming the bundle is broken.
-   **Claude Desktop logs** are at `%APPDATA%\Claude\logs\mcp-server-Archicad (Caracara).log`. On the Microsoft Store build that path is redirected and the real file is `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\logs\mcp-server-Archicad (Caracara).log`.

</details>

---

## Configuration Options

You can customize the server via CLI flags or environment variables (both `CARACARA_*` and legacy `TAPIR_*` are recognized):

| CLI Flag | Environment Variable | Default | Description |
| :--- | :--- | :--- | :--- |
| `--transport` | - | `stdio` | Transport protocol to use (`stdio`, `sse`, or `streamable-http`) |
| `--host` | `CARACARA_MCP_HOST` / `TAPIR_MCP_HOST` | `127.0.0.1` | Bind address for HTTP-based transports |
| `--port` | `CARACARA_MCP_PORT` / `TAPIR_MCP_PORT` | `8000` | Bind port for HTTP-based transports |
| `--token` | `CARACARA_MCP_TOKEN` / `TAPIR_MCP_TOKEN` | `None` | Optional Bearer token to secure HTTP endpoints |
| `--async-threshold-seconds` | `CARACARA_MCP_ASYNC_THRESHOLD_SECONDS` | `45` | Seconds to wait before returning a running job handle |
| `--job-ttl-seconds` | `CARACARA_MCP_JOB_TTL_SECONDS` | `86400` | Seconds to keep finished jobs; `0` disables time-based expiry |
| `--max-completed-jobs` | `CARACARA_MCP_MAX_COMPLETED_JOBS` | `128` | Maximum number of finished jobs to keep |

CLI flags override environment variables.

---

## Long-Running Commands

Commands normally return their result directly. If a command takes longer than 45 seconds, `archicad_call_tool` returns a job handle while execution continues:

```json
{"status": "running", "jobHandle": "job:83af21..."}
```

Call `archicad_get_job(job_handle="job:83af21...")` to check progress and retrieve the result. Repeat while the status is `running`; the final status is `completed` or `failed`. If your client times out sooner, lower `--async-threshold-seconds`.

If a response is lost, call `archicad_get_job()` to list recent jobs before repeating a command that changes the project. Cancelling a request does not stop a command already started, and retrying it may duplicate changes.

Jobs remain available across HTTP client reconnects while the server is running, but are lost on server restart. Retention defaults to 24 hours and a maximum of 128 finished jobs.

---

## Usage

1. **Restart your MCP client** to apply configuration changes.
2. Ensure at least one instance of Archicad is running.
3. Start by asking the AI to find running Archicad instances:

   > *"Can you check what Archicad projects I have running?"*

   The AI will call `discovery_list_active_archicads` and report the active instances and their `port` numbers.

4. State your main goal:

   > *"Using port 19723, get all the Wall elements from the project."*

5. The AI will execute a progressive discovery and calling loop:
   - **Step 1:** Queries `archicad_list_commands` to look up the correct command name for the requested action (`elements_get_elements_by_type`).
   - **Step 2:** Calls `archicad_get_command_schema` with the target command name to retrieve the exact parameter structure.
   - **Step 3:** Calls `archicad_call_tool` with the command name, targeted `port`, and parameter payload.

---

## How It Works

The server operates through a layered architecture:

-   **AI Agent (e.g., Claude):** Interprets user prompts and orchestrates tool discovery.
-   **MCP Client (e.g., Claude for Desktop):** Manages the server process and handles communication.
-   **MCP Server (Caracara):** Standardizes tool descriptions, parameters, sandboxing, and results, presenting a clean `list`/`schema`/`call` interface.
-   **`multiconn_archicad` Library:** Resolves active socket connections and handles low-level command dispatch to Archicad instances.
-   **Archicad & Tapir Add-On:** Built-in APIs and Tapir Add-on execute commands and return structured data.

---

## Origins & Acknowledgements

**Caracara Archicad** is a fork of [tapir-archicad-MCP](https://github.com/SzamosiMate/tapir-archicad-MCP), created and originally maintained by [Máté Szamosi (@SzamosiMate)](https://github.com/SzamosiMate).

We are deeply grateful to Máté and the [Enzyme APD](https://github.com/ENZYME-APD/tapir-archicad-automation) team for developing the Archicad automation ecosystem and making it open-source.

**Why this fork?**  
Caracara explores advanced agentic extensions—including script sandboxing, polymorphic meta-verbs, field masking, and virtual element sets. Wherever possible, improvements and bug fixes applicable to the core server are contributed back upstream.

*Note: For issues or feature requests related specifically to Caracara, please use the [Caracara Issue Tracker](https://github.com/parikshit99/caracara-archicad/issues) to avoid burdening upstream maintainers.*

Icon artwork is the official Tapir mark from [ENZYME-APD/tapir-archicad-automation](https://github.com/ENZYME-APD/tapir-archicad-automation) (`branding/logo/png/tapir_logo_black_512.png`), MIT, Copyright 2024 Enzyme APD.

---

## Contributing

Contributions are welcome! Please feel free to submit an issue or open a pull request on the Caracara repository.

---

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
