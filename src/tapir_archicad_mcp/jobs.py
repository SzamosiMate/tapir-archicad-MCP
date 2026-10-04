"""Server-owned executions, independent of MCP request cancellation."""

import asyncio
import json
import logging
import time
import uuid
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from functools import wraps
from threading import RLock
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad.errors import APIErrorBase, RequestError

from tapir_archicad_mcp.pagination import INVALID_TOKEN, PaginationRequest, PaginationSnapshot

log = logging.getLogger(__name__)
COMMAND_WORKERS = 32
PREVIEW_MAX_CHARS = 300


def locked(method: Callable) -> Callable:
    """Hold the instance's store lock for a synchronous method."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper


@dataclass(frozen=True)
class JobSettings:
    """Job configuration; CLI/environment values are validated by the argument parser."""

    async_threshold_seconds: float = 45
    job_ttl_seconds: float = 86400
    max_completed_jobs: int = 128


def arguments_preview(arguments: dict) -> str:
    """Format supplied arguments as a compact snippet for identifying a job."""
    preview = json.dumps(arguments, ensure_ascii=False, separators=(",", ":"))
    return preview if len(preview) <= PREVIEW_MAX_CHARS else preview[: PREVIEW_MAX_CHARS - 1] + "…"


def _failure_details(exc: BaseException) -> dict:
    upstream = exc if isinstance(exc, APIErrorBase) else exc.__cause__
    message = str(exc) if isinstance(exc, (APIErrorBase, ToolError)) else "Unexpected execution error."
    if isinstance(upstream, RequestError):
        message += " Archicad's actual outcome may be unknown; do not automatically retry this command."
    elif not isinstance(exc, (APIErrorBase, ToolError)):
        message += " Archicad's actual outcome may be unknown; inspect the server logs."
    error = {"type": type(exc).__name__, "message": message}
    if isinstance(upstream, APIErrorBase) and upstream.code is not None:
        error["code"] = upstream.code
    return error


class JobStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    handle: str
    command: str
    port: int
    arguments_preview: str
    submitted_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: JobStatus = JobStatus.RUNNING
    completed_at: str | None = None
    result: Any = None
    error: dict | None = None
    exception: Exception | None = None
    future: Future = field(init=False, repr=False)
    completion: asyncio.Future | None = field(default=None, init=False, repr=False)

    def summary(self) -> dict:
        return {
            "jobHandle": self.handle,
            "command": self.command,
            "port": self.port,
            "status": self.status.value,
            "submittedAt": self.submitted_at,
            "completedAt": self.completed_at,
            "argumentsPreview": self.arguments_preview,
        }

    def rendered_result(self) -> Any:
        return self.result.page() if isinstance(self.result, PaginationSnapshot) else self.result


class JobStore:
    def __init__(
        self,
        settings: JobSettings | None = None,
        *,
        max_workers: int = COMMAND_WORKERS,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self.settings = settings or JobSettings()
        self._clock = clock or time.monotonic
        self._lock = RLock()
        self._jobs: dict[str, Job] = {}
        self._completed: OrderedDict[str, float] = OrderedDict()
        self._accepting = True
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="TapirJob")

    @locked
    def submit(self, command: str, port: int, arguments: dict, execute: Callable[[str], Any]) -> Job:
        if not self._accepting:
            raise ToolError("The job store is shutting down; no new commands can be started.")
        if len(self._jobs) - len(self._completed) >= self._max_workers:
            raise ToolError(f"Server busy: all {self._max_workers} command workers are occupied. Try again later.")
        job = Job("job:" + uuid.uuid4().hex, command, port, arguments_preview(arguments))
        self._jobs[job.handle] = job
        try:
            job.future = self._executor.submit(self._execute, job, execute)
        except Exception:
            del self._jobs[job.handle]
            raise
        return job

    def _execute(self, job: Job, execute: Callable[[str], Any]) -> None:
        log.info("[%s] Execution start: '%s' on port %s", job.handle, job.command, job.port)
        result = None
        exception = None
        error = None
        try:
            result = execute(job.handle)
            if result is None:
                result = {}
        except BaseException as exc:
            # A worker exiting abnormally must still finalize its admitted job.
            log.exception("[%s] Execution failed: '%s' on port %s", job.handle, job.command, job.port)
            error = _failure_details(exc)
            exception = exc.with_traceback(None) if isinstance(exc, Exception) else RuntimeError(error["message"])
        self._complete(job, result, exception, error)
        log.info("[%s] Execution end: %s", job.handle, job.status)

    @locked
    def _complete(self, job: Job, result: Any, exception: Exception | None, error: dict | None) -> None:
        job.result = result
        job.exception = exception
        job.error = error
        job.status = JobStatus.FAILED if exception is not None else JobStatus.COMPLETED
        job.completed_at = datetime.now(UTC).isoformat()
        self._completed[job.handle] = self._clock()
        self.prune()

    async def wait(self, job: Job) -> None:
        # All waiters run on the application loop; share one worker-to-loop bridge.
        if job.completion is None:
            job.completion = asyncio.wrap_future(job.future)
        # Cancelling a waiter must never cancel work or its result capture.
        await asyncio.wait({job.completion}, timeout=self.settings.async_threshold_seconds)

    @locked
    def initial_result(self, job: Job) -> dict:
        if job.status == JobStatus.RUNNING:
            return {"status": job.status.value, "jobHandle": job.handle}
        if job.exception is not None:
            raise job.exception
        return job.rendered_result()

    @locked
    def get(self, handle: str) -> Job:
        try:
            return self._jobs[handle]
        except KeyError:
            raise ToolError("Unknown or expired job_handle. List retained jobs with archicad_get_job().") from None

    @locked
    def list_jobs(self) -> dict:
        return {"jobs": [job.summary() for job in reversed(self._jobs.values())]}

    @locked
    def response(self, job: Job) -> dict:
        response = {"jobHandle": job.handle, "status": job.status.value}
        if job.status == JobStatus.COMPLETED:
            response["result"] = job.rendered_result()
        elif job.status == JobStatus.FAILED:
            response["error"] = dict(job.error)
        return response

    @locked
    def get_page(self, token: str, request: PaginationRequest) -> dict:
        session, _, raw_offset = token.partition(":")
        job = self._jobs.get("job:" + session)
        snapshot = job.result if job is not None else None
        if isinstance(snapshot, PaginationSnapshot):
            return snapshot.continuation(request, raw_offset)
        raise ToolError(INVALID_TOKEN)

    @locked
    def prune(self) -> None:
        """Evict oldest finished jobs that exceed the age or capacity limits."""
        now = self._clock()
        ttl = self.settings.job_ttl_seconds
        while self._completed:
            handle, completed_at = next(iter(self._completed.items()))
            expired = ttl > 0 and now - completed_at >= ttl
            if not expired and len(self._completed) <= self.settings.max_completed_jobs:
                break
            self._completed.popitem(last=False)
            del self._jobs[handle]

    async def cleanup_loop(self) -> None:
        while True:
            await asyncio.sleep(60)
            self.prune()

    @locked
    def stop_admission(self) -> None:
        self._accepting = False

    def shutdown(self) -> None:
        self.stop_admission()
        self._executor.shutdown(wait=True)
        with self._lock:
            self._jobs.clear()
            self._completed.clear()
