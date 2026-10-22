def register_all_tools():
    """
    This function's purpose is to explicitly import all tool modules.
    The act of importing them runs the @mcp.tool decorators within, which
    registers the tools with the central 'mcp' instance from app.py.
    """
