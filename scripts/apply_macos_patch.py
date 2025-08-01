#!/usr/bin/env python3
"""
Script to apply macOS compatibility patch for multiconn_archicad library.
This patch allows the library to work on non-Windows platforms by providing
dummy implementations for Windows-specific features.
"""

import os
import sys
import shutil
from pathlib import Path


def find_multiconn_archicad_path():
    """Find the path to the multiconn_archicad package."""
    try:
        import multiconn_archicad
        return Path(multiconn_archicad.__file__).parent
    except ImportError:
        print("Error: multiconn_archicad not found. Please install it first.")
        return None


def apply_patch():
    """Apply the macOS compatibility patch."""
    if sys.platform == "win32":
        print("Windows detected - no patch needed.")
        return True
    
    print("Non-Windows platform detected - applying compatibility patch...")
    
    # Find the multiconn_archicad package
    package_path = find_multiconn_archicad_path()
    if not package_path:
        return False
    
    dialog_handlers_path = package_path / "dialog_handlers" / "__init__.py"
    
    if not dialog_handlers_path.exists():
        print(f"Error: {dialog_handlers_path} not found.")
        return False
    
    # Create the patched content
    patched_content = '''import sys
from .dialog_handler_base import UnhandledDialogError, DialogHandlerBase, EmptyDialogHandler

# Platform-specific imports
if sys.platform == "win32":
    from .win_dialog_handler import WinDialogHandler
    from .win_int_handler_factory import win_int_handler_factory
    __all__: tuple[str, ...] = (
        "WinDialogHandler",
        "win_int_handler_factory",
        "UnhandledDialogError",
        "DialogHandlerBase",
        "EmptyDialogHandler",
    )
else:
    # On non-Windows platforms, create dummy classes
    class WinDialogHandler(DialogHandlerBase):
        def __init__(self, *args, **kwargs):
            raise NotImplementedError("WinDialogHandler is not available on non-Windows platforms")
    
    def win_int_handler_factory(*args, **kwargs):
        raise NotImplementedError("win_int_handler_factory is not available on non-Windows platforms")
    
    __all__: tuple[str, ...] = (
        "WinDialogHandler",
        "win_int_handler_factory",
        "UnhandledDialogError",
        "DialogHandlerBase",
        "EmptyDialogHandler",
    )
'''
    
    # Backup the original file
    backup_path = dialog_handlers_path.with_suffix('.py.bak')
    shutil.copy2(dialog_handlers_path, backup_path)
    print(f"Backed up original file to: {backup_path}")
    
    # Write the patched content
    dialog_handlers_path.write_text(patched_content)
    print(f"Applied patch to: {dialog_handlers_path}")
    
    return True


if __name__ == "__main__":
    success = apply_patch()
    if success:
        print("✅ macOS compatibility patch applied successfully!")
    else:
        print("❌ Failed to apply patch.")
        sys.exit(1) 