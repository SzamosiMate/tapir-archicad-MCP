# Archicad Tapir MCP Server

Connect your AI assistant to Archicad. Use natural language to explore projects and automate workflows through the [Tapir add-on](https://github.com/ENZYME-APD/tapir-archicad-automation) and the official Archicad JSON API.

[![PyPI version](https://img.shields.io/pypi/v/tapir-archicad-mcp)](https://pypi.org/project/tapir-archicad-mcp/)
[![CI](https://github.com/SzamosiMate/tapir-archicad-MCP/actions/workflows/test.yml/badge.svg?branch=master)](https://github.com/SzamosiMate/tapir-archicad-MCP/actions/workflows/test.yml)
![Platforms: Windows and macOS](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS-blue)
[![Supported Tapir version](https://img.shields.io/badge/Tapir_Add--On-2.0.0-blue)](https://github.com/ENZYME-APD/tapir-archicad-automation/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## See it in action

Astra uses photos and a plan as references to model in Archicad.

[![Watch the Archicad modeling demo on YouTube](https://img.youtube.com/vi/LuWmoVjfpUA/hqdefault.jpg)](https://www.youtube.com/watch?v=LuWmoVjfpUA)

## What can it do?

- Inspect open projects, elements, properties, and attributes.
- Create and modify model elements, and work with views and layouts.
- Export project data and use supported IFC and Teamwork commands.
- Access **800+ Archicad commands**, discovered on demand by your assistant.
- Connect to multiple running Archicad instances.

## Quick start

You'll need Archicad running on Windows or macOS, the [Tapir add-on](https://github.com/ENZYME-APD/tapir-archicad-automation), [uv](https://docs.astral.sh/uv/getting-started/installation/), and an MCP client. The server requires Python 3.12–3.14; uv can provision Python for you.

### Ask your AI to install it

Copy this prompt into your AI assistant:

> Install the Archicad Tapir MCP server for my MCP client, following the instructions at https://github.com/SzamosiMate/tapir-archicad-MCP/blob/master/docs/setup-and-configuration.md. Help me verify that it can connect to my running Archicad instance.

### Install it yourself

If your client supports MCP bundles, download [tapir-archicad.mcpb](https://github.com/SzamosiMate/tapir-archicad-MCP/releases/latest/download/tapir-archicad.mcpb) and open it in your client. The client must be able to find `uv` on its PATH.

Prefer the old-school approach? Follow the [manual setup instructions](docs/setup-and-configuration.md#manual-configuration)—editing a config file is optional hacker cred.

### Try it

With Archicad running, ask your assistant:

> What Archicad projects do I have open?

The assistant can list ready instances, their project names and ports, and report instances that are unavailable. If you have multiple projects open, specify the port when asking it to work on one.

## How it works

Your MCP client runs this server, which connects to Archicad through [`multiconn_archicad`](https://github.com/SzamosiMate/multiconn_archicad). The server exposes five MCP tools for finding instances, listing commands, looking up their schemas, executing commands, and checking long-running jobs. Your assistant discovers the Archicad commands it needs instead of loading all their schemas at once.

## Important to know

The server can create, modify, and delete model elements, export files, and interact with Teamwork. Project names, paths, and model data returned by commands are sent to your MCP client. Review changes made to your projects and use a copy when experimenting.

Available commands depend on your installed Archicad and Tapir versions. Instance discovery reports a missing Tapir add-on as unavailable and warns when the installed Tapir version differs from the version supported by the server.

## Documentation

See [Setup and configuration](docs/setup-and-configuration.md) for client setup, troubleshooting, server options, HTTP transports, jobs, and pagination.

## Development and contributing

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), clone the repository, and run:

```sh
uv sync --locked
uv run --locked pytest tests
```

Contributions are welcome: [open an issue or pull request](https://github.com/SzamosiMate/tapir-archicad-MCP/issues). Command wrappers are generated from the pinned `multiconn-archicad` release; see `scripts/generate_tools.py` and `scripts/generator_config.py` for the generator and its configuration.

## License and acknowledgments

This project is licensed under the [MIT License](LICENSE). The bundle icon uses the Tapir mark from [ENZYME-APD/tapir-archicad-automation](https://github.com/ENZYME-APD/tapir-archicad-automation) (`branding/logo/png/tapir_logo_black_512.png`), MIT, Copyright 2024 Enzyme APD.
