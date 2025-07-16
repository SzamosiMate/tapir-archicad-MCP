import json
import sys
from pathlib import Path

import platformdirs

from tapir_archicad_mcp.constants import MODULE_NAME_MAPPING

APP_FOLDER_NAME = "Claude"
CONFIG_FILE_NAME = "claude_desktop_config.json"


def get_config_path() -> Path | None:
    """Finds the path to the claude_desktop_config.json file."""
    base_dir = platformdirs.user_config_path(roaming=True)

    config_dir = base_dir / APP_FOLDER_NAME
    if not config_dir.exists():
        print(f"Configuration directory not found at: {config_dir}")
        print("Please run Claude Desktop at least once to create it.")
        return None

    config_file = config_dir / CONFIG_FILE_NAME
    if not config_file.exists():
        print(f"Configuration file not found at: {config_file}")
        print("Please ensure Claude Desktop has been run and a config file exists.")
        return None

    return config_file


def configure_claude_desktop():
    """
    Adds or updates the Tapir MCP server configurations in the
    claude_desktop_config.json file.
    """
    config_file = get_config_path()
    if not config_file:
        sys.exit(1)

    print(f"Found Claude Desktop config file at: {config_file}")

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading or parsing config file: {e}")
        sys.exit(1)

    if 'servers' not in config_data:
        config_data['servers'] = {}

    added_count = 0
    updated_count = 0

    groups_to_configure = list(MODULE_NAME_MAPPING.keys()) + ['discovery']

    for group in groups_to_configure:
        server_id = f"tapir_archicad_{group}"
        server_name = f"Archicad Tapir ({group.capitalize()})"
        server_command = [
            sys.executable,
            "-m",
            "tapir_archicad_mcp.server",
            "--group",
            group
        ]

        server_entry = {
            "name": server_name,
            "command": server_command,
            "enabled": False  # Default to disabled to not overwhelm the user
        }

        if server_id not in config_data['servers']:
            print(f"  [+] Adding new server: '{server_name}'")
            added_count += 1
        else:
            print(f"  [*] Updating existing server: '{server_name}'")
            updated_count += 1

        config_data['servers'][server_id] = server_entry

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    except IOError as e:
        print(f"Error writing to config file: {e}")
        sys.exit(1)

    print("\n--- Configuration Complete ---")
    print(f"Successfully added {added_count} and updated {updated_count} server configurations.")
    print("You can now launch Claude Desktop and enable the 'Archicad Tapir' servers you need from the Servers menu.")


def main():
    """Entry point for the console script."""
    configure_claude_desktop()

if __name__ == "__main__":
    main()