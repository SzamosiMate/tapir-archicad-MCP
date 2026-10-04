import logging
import uuid
from typing import Any, Self

log = logging.getLogger(__name__)


class DispatchLifecycle:
    """
    Logs the start and the end of the request a dispatched tool sends to Archicad.

    Scoped to the call itself, so the two timestamps bracket Archicad's work and
    nothing else - not the registry lookup, the argument validation or the
    connection lookup that precede it. Both lines carry the same short request
    id, so a start can be paired with its end when calls overlap.

    A job handle can identify the same dispatch across polling requests.
    """

    def __init__(self, tool_name: str, port: int, job_handle: str | None = None):
        self.tool_name = tool_name
        self.port = port
        self.request_id = job_handle or uuid.uuid4().hex[:8]

    def __enter__(self) -> Self:
        log.info(f"[{self.request_id}] Request start: '{self.tool_name}' on port {self.port}")
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        outcome = "ok" if exc_type is None else f"failed with {exc_type.__name__}"
        log.info(f"[{self.request_id}] Request end: '{self.tool_name}' on port {self.port} - {outcome}")
