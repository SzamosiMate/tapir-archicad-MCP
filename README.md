# Archicad Tapir MCP Server

This project provides a Model Context Protocol (MCP) server for Archicad. It acts as a bridge, allowing AI agents and applications (like Claude for Desktop) to interact with running Archicad instances by wrapping the powerful [Tapir JSON API](https://github.com/ENZYME-APD/tapir-archicad-automation).

The server dynamically generates a comprehensive set of over 80 MCP tools from the Tapir API schema, enabling fine-grained control over Archicad projects.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)]()

> **Disclaimer:** This project is in an early stage of development. It has not been extensively tested and is intended primarily for experimental and educational purposes. Interfaces and functionality may change in future updates. Please use with caution.

## Key Features

-   **Multi-Instance Control:** Connect to and manage multiple running Archicad instances simultaneously.
-   **Comprehensive Toolset:** Auto-generates over 80 distinct MCP tools, providing access to the full functionality of the Tapir API.
-   **Dynamic Discovery:** Includes a core tool to discover active Archicad instances, their ports, and open projects.
-   **Strongly-Typed:** Uses Pydantic models for all API commands and results, ensuring data integrity and providing a clear schema for AI interaction.
-   **Extensible Structure:** Designed with a clean separation between auto-generated and custom tools, making it easy to add your own functionality.

## Installation & Setup

Follow these steps to get the server running and connected to an MCP client like Claude for Desktop.

### 1. Prerequisites

-   **Python 3.10+** and **`uv`**: Ensure you have a modern version of Python and the `uv` package manager installed. You can install `uv` with `pip install uv`.
-   **Archicad & Tapir Add-On**: You must have Archicad running with the [Tapir Archicad Add-On](https://github.com/ENZYME-APD/tapir-archicad-automation) installed. The server cannot function without it.
-   **MCP Client**: An application that can host MCP servers, such as [Claude for Desktop](https://www.claude.ai/download).

### 2. Clone the Repository

Get the project code on your local machine:
```bash
git clone https://github.com/your-username/archicad-mcp-server.git
cd archicad-mcp-server
```

### 3. Install Dependencies

Create a virtual environment and install the required Python packages using `uv`.
```bash
# Create and activate the virtual environment
uv venv

# On macOS/Linux
source .venv/bin/activate
# On Windows
.venv\Scripts\activate

# Install dependencies from pyproject.toml
uv sync
```

### 4. Configure Claude for Desktop

Finally, tell Claude how to run your server. Open your `claude_desktop_config.json` file and add the following configuration.

-   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
-   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ArchicadTapir": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/your/archicad-mcp-server",
        "python",
        "-m",
        "tapir_archicad_mcp.server"
      ]
    }
  }
}
```
**Important:** You **must** replace `"/path/to/your/archicad-mcp-server"` with the **full, absolute path** to the directory where you cloned the project.

## Usage

1.  **Restart Claude for Desktop** to apply the configuration changes.
2.  Ensure at least one instance of Archicad (with Tapir) is running.
3.  The "Tools & Resources" icon should appear in Claude. Click it to see the list of available Archicad tools.
4.  Start interacting! Ask a question like:

    > "Can you check what Archicad projects I have running?"

Claude will ask for your permission to run the `tapir_discovery_list_active_archicads` tool and will then report the active instances it found. From there, you can use the port number to target specific commands.

## How It Works

The server operates through a layered architecture:

-   **AI Agent (e.g., Claude):** Interacts with the user and decides which tools to call.
-   **MCP Client (e.g., Claude for Desktop):** Manages the server process and communication.
-   **Archicad Tapir MCP Server (This Project):** Exposes the Tapir API as a set of standardized MCP tools.
-   **`multiconn_archicad` Library:** The underlying Python library that handles the low-level communication with Archicad instances.
-   **Archicad & Tapir Add-On:** The final destination that executes the commands.

## Contributing

Contributions are welcome! Please feel free to submit an issue or open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
