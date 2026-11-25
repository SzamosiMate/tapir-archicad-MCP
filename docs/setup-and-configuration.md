# Setup and configuration

See [Command discovery](command-discovery.md) for searching the Archicad catalogue and continuing a search across calls.

This guide covers installation, troubleshooting, server options, and advanced usage. For a quick introduction, see the [README](../README.md).

## Requirements

- Archicad running on Windows or macOS, with a project open.
- The [Tapir Archicad Add-On](https://github.com/ENZYME-APD/tapir-archicad-automation), which provides Archicad automation commands. Install it for your Archicad version; discovery marks instances without Tapir as unavailable.
- [uv](https://docs.astral.sh/uv/getting-started/installation/), which installs and runs the MCP server and its dependencies. It must be available on the PATH seen by your MCP client.
- An MCP client: the AI application that connects to the server.

uv can download a compatible Python version if needed. If managing Python yourself, the server supports Python 3.12, 3.13, and 3.14.

The server connects to running Archicad instances on its host and targets Tapir 2.0.1. Available commands and parameters depend on the installed Archicad and Tapir versions; discovery reports version warnings.

## Installation

Choose one installation method for your client. After setup, restart the client if needed and use the [verification prompt](#verify-the-connection).

### MCP bundle

If your client supports [MCP bundles](https://github.com/modelcontextprotocol/mcpb), download [tapir-archicad.mcpb](https://github.com/SzamosiMate/tapir-archicad-MCP/releases/latest/download/tapir-archicad.mcpb) and open it in the client. The bundle uses `uv` to provision Python and its locked dependencies. The first launch may take a while while the environment is prepared.

### Manual configuration

For clients that support the standard `mcpServers` configuration, add the following entry to the client's configuration file. Preserve any existing servers:

```json
{
  "mcpServers": {
    "ArchicadTapir": {
      "command": "uvx",
      "args": ["--from", "tapir-archicad-mcp", "archicad-server"]
    }
  }
}
```

For Claude Desktop, the configuration file is normally:

- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

The Microsoft Store build of Claude Desktop does not read the usual `%APPDATA%` configuration file; the bundle is an alternative. Other clients may use a different file or configuration format; follow your client's MCP setup instructions and use the same command and arguments.

### Verify the connection

Open Archicad and ask your assistant:

> What Archicad projects do I have open?

The `discovery_list_active_archicads` tool reports ready instances with project names and ports, and reports unavailable instances separately. If more than one instance is open, use its port to target the one you want.

## Troubleshooting

- **The client cannot find `uv` or `uvx`:** Install [uv](https://docs.astral.sh/uv/getting-started/installation/), restart the client, and check that its environment can find the executable. GUI applications may use a different PATH than your terminal; if needed, use the executable's absolute path in the client configuration.
- **The bundle fails to install or the server disconnects:** Uninstall the bundle, restart the client, and reinstall it. The first launch can take longer while uv prepares the environment.
- **No ready Archicad instance appears:** Check that Archicad is running and the Tapir add-on is installed and loaded. Discovery reports missing Tapir or unresponsive instances separately; it also reports version warnings.
- **A command is slow or its response is lost:** See [long-running commands](#long-running-commands) before repeating an operation that changes a project.
- **Server logs:** Check `~/.tapir_mcp/logs/tapir_mcp_server.log` (on Windows, under your user profile).
- **Claude Desktop logs:** On Windows, check `%APPDATA%\Claude\logs\mcp-server-Archicad (Tapir).log`. For the Microsoft Store build, check `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\logs\mcp-server-Archicad (Tapir).log`.

## Server options

Pass flags to `archicad-server` after its name, or set the corresponding environment variables in the server process. CLI flags override environment variables.

| Flag | Environment variable | Default | Description |
| --- | --- | --- | --- |
| `--transport` | — | `stdio` | `stdio`, `sse`, or `streamable-http` |
| `--host` | `TAPIR_MCP_HOST` | `127.0.0.1` | HTTP bind address |
| `--port` | `TAPIR_MCP_PORT` | `8000` | HTTP bind port |
| `--streamable-http-path` | `TAPIR_MCP_STREAMABLE_HTTP_PATH` | `/mcp` | Streamable HTTP endpoint path |
| `--mount-path` | `TAPIR_MCP_MOUNT_PATH` | None | Optional SSE route prefix |
| `--token` | `TAPIR_MCP_TOKEN` | None | Optional bearer token for HTTP; ignored for stdio |
| `--async-threshold-seconds` | `TAPIR_MCP_ASYNC_THRESHOLD_SECONDS` | `45` | Maximum wait before returning a running job handle |
| `--job-ttl-seconds` | `TAPIR_MCP_JOB_TTL_SECONDS` | `86400` | Finished job and page lifetime; `0` disables age expiry |
| `--max-completed-jobs` | `TAPIR_MCP_MAX_COMPLETED_JOBS` | `128` | Maximum retained finished jobs |

## HTTP transports

For example, start a local Streamable HTTP server:

```sh
uvx --from tapir-archicad-mcp archicad-server --transport streamable-http
```

Connect an HTTP-capable MCP client to `http://127.0.0.1:8000/mcp`. Use `--streamable-http-path` to change the endpoint or `--transport sse` for SSE. For HTTP transports, set `TAPIR_MCP_TOKEN` in the server environment (or pass `--token`) to require a bearer token; configure the client to send that token as an Authorization header. Authentication is optional and is not enabled by default. The default bind address accepts local connections only. Consider transport encryption and network access controls before exposing an HTTP server beyond your machine.

The HTTP server's port is separate from the port identifying an Archicad instance.

## Working with results

### Element queries

With Tapir 2.0.0 or newer, ask your assistant to find elements by type, property values, or classification. For example, ask it to find exterior walls with a fire rating of at least 60 minutes using the properties available in your project. The `elements_query` command accepts nested AND/OR conditions and returns matching element IDs in pages when needed.

By default, the command searches the floor plan. Pass `params.elements` to filter a list of candidate IDs while preserving their order and duplicate matches. An empty candidate list yields no matches.

When calling the command directly, look up its schema with `archicad_get_command_schema` and set `params.query.schema_version` to `"1.0"`. Use `properties_search_properties` to find property GUIDs. Set `includeEnumValues` to `true` to look up enumeration choices and pass their exact case-sensitive labels in the query.

### Long-running commands

Commands normally return their result directly. If a command takes longer than 45 seconds by default, `archicad_call_tool` returns a job handle while execution continues:

```json
{"status": "running", "jobHandle": "job:83af21..."}
```

Call `archicad_get_job(job_handle="job:83af21...")` to check it; repeat while the status is `running`. The final status is `completed` or `failed`. If your client times out sooner, lower `--async-threshold-seconds`.

If a response is lost, call `archicad_get_job()` to list recent jobs before repeating a command that changes the project. Cancelling a request does not stop a command already started, and retrying it may duplicate changes. Jobs remain available across HTTP client reconnects while the server is running, but are lost on restart. Finished jobs expire after 24 hours by default, with at most 128 retained.

### Pagination

Some commands return results in pages. If a result includes `next_page_token`, call `archicad_call_tool` again with the same command and arguments, adding `page_token` to the arguments dictionary. Repeat until there is no next token. Page snapshots share the job retention settings and do not survive a server restart.
