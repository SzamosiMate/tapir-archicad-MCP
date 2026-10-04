from typing import Any, Generic, TypeVar

from mcp.server.mcpserver import MCPServer
from multiconn_archicad import MultiConn

from tapir_archicad_mcp.jobs import JobStore

T = TypeVar("T")


class ServerState(Generic[T]):
    """A process-wide server-state slot."""

    _UNSET = object()

    def __init__(self, name: str) -> None:
        self._name = name
        self._value: Any = self._UNSET

    def get(self) -> T:
        if self._value is self._UNSET:
            raise LookupError(f"{self._name} has not been initialized.")
        return self._value

    def set(self, value: T) -> None:
        self._value = value

    def clear(self) -> None:
        self._value = self._UNSET


mcp_instance: ServerState[MCPServer] = ServerState("mcp_instance")
multi_conn_instance: ServerState[MultiConn] = ServerState("multi_conn_instance")
job_store_instance: ServerState[JobStore] = ServerState("job_store_instance")
