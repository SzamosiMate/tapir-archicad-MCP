import logging
import uuid
from typing import Any, Optional, Self

log = logging.getLogger(__name__)


class DispatchLifecycle:
    """
    Logs the start and the end of one dispatched tool call.

    Both lines carry the same short request id, so a start can be paired with
    its end even when calls overlap. Used as a context manager so the dispatch
    itself stays free of logging branches:

        with DispatchLifecycle(name) as lifecycle:
            ...
            lifecycle.bind_port(port)
            ...
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.request_id = uuid.uuid4().hex[:8]
        self.port: Optional[int] = None

    def bind_port(self, port: int) -> None:
        """Records the target port once the arguments have been validated."""
        self.port = port

    @property
    def _target(self) -> str:
        return f"'{self.tool_name}'" + (f" on port {self.port}" if self.port is not None else "")

    def __enter__(self) -> Self:
        log.info(f"[{self.request_id}] Dispatch start: {self._target}")
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        outcome = "ok" if exc_type is None else f"failed with {exc_type.__name__}"
        log.info(f"[{self.request_id}] Dispatch end: {self._target} - {outcome}")
