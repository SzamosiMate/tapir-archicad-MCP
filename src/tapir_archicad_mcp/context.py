"""Server-scoped state published by the lifespan and read by the tool handlers.

A ``ContextVar`` would be the natural home for this, but mcp 2 dispatches each
request in a snapshot of the transport's contextvars and runs synchronous
handlers on a worker thread, so a value set inside the lifespan is no longer
visible to a handler reached over SSE or streamable HTTP. The SDK's migration
guide prescribes a module-level object that the lifespan populates instead;
these holders are exactly that, wrapped in a ``get``/``set``/``reset`` surface
so tests can substitute a stand-in and restore it afterwards.
"""

from typing import Any, Generic, TypeVar

from mcp.server.mcpserver import MCPServer
from multiconn_archicad.multi_conn import MultiConn

T = TypeVar("T")


class ServerState(Generic[T]):
    """A process-wide slot holding one server-scoped object."""

    _UNSET = object()

    def __init__(self, name: str) -> None:
        self._name = name
        self._value: Any = self._UNSET

    def get(self) -> T:
        """Return the stored object, raising ``LookupError`` while unset."""
        if self._value is self._UNSET:
            raise LookupError(f"{self._name} has not been initialized.")
        return self._value

    def set(self, value: T) -> Any:
        """Store ``value`` and return the previous one for a later ``reset``."""
        previous = self._value
        self._value = value
        return previous

    def reset(self, token: Any) -> None:
        """Restore the value returned by the matching ``set`` call."""
        self._value = token


mcp_instance: ServerState[MCPServer] = ServerState("mcp_instance")
multi_conn_instance: ServerState[MultiConn] = ServerState("multi_conn_instance")
