import importlib
import logging

from tapir_archicad_mcp import constants

log = logging.getLogger()


def register_tool_group(group_short_name: str):
    """
    Selectively registers a specific group of generated tools, plus the
    essential hand-written tools (like discovery). The act of importing a tool
    module runs the @mcp.tool decorators within, registering the tools with
    the global 'mcp' instance from app.py.
    """

    try:
        from tapir_archicad_mcp.tools.custom import functions
        log.info(f"Registered essential custom tools from: {functions.__name__}")
    except ImportError as e:
        log.error(f"Could not import essential custom tools. Error: {e}")
        raise

    if group_short_name == 'discovery':
        log.info("Registration complete for 'discovery' group (custom tools only).")
        return

    if group_short_name not in constants.MODULE_NAME_MAPPING:
        log.error(f"Unknown tool group '{group_short_name}'.")
        raise ValueError(f"Unknown tool group '{group_short_name}'. Available groups are: {', '.join(constants.AVAILABLE_GROUPS)}")

    module_name = f"{constants.MODULE_NAME_MAPPING[group_short_name]}"
    full_module_path = f"tapir_archicad_mcp.tools.generated.{module_name}"

    try:
        importlib.import_module(full_module_path)
        log.info(f"Successfully imported and registered tool group: '{group_short_name}' from module '{full_module_path}'.")
    except ImportError as e:
        log.error(f"Failed to import module for group '{group_short_name}': {e}")
        raise ImportError(f"Could not find the generated tool module '{full_module_path}'. Please ensure tools have been generated correctly.") from e