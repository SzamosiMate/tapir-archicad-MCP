"""Server-owned executions, independent of MCP request cancellation."""

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
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
from typing import TYPE_CHECKING, Any, NewType

from mcp.server.mcpserver.exceptions import ToolError
from multiconn_archicad.errors import APIErrorBase, RequestError

from tapir_archicad_mcp.result_budget import ResultBudget

if TYPE_CHECKING:
    from tapir_archicad_mcp.tool_results import Completion

JobHandle = NewType("JobHandle", str)
ResultHandle = NewType("ResultHandle", str)

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
    result_budget: ResultBudget = field(default_factory=ResultBudget)


def arguments_preview(arguments: dict) -> str:
    """Format supplied arguments as a compact snippet for identifying a job."""
    encoder = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"))
    chunks = []
    length = 0
    for chunk in encoder.iterencode(arguments):
        if length + len(chunk) > PREVIEW_MAX_CHARS:
            chunks.append(chunk[: PREVIEW_MAX_CHARS - length])
            return "".join(chunks)[: PREVIEW_MAX_CHARS - 1] + "…"
        length += len(chunk)
        chunks.append(chunk)
    return "".join(chunks)


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
    handle: JobHandle
    command: str
    port: int
    arguments_preview: str
    submitted_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: JobStatus = JobStatus.RUNNING
    completed_at: str | None = None
    result: Any = None
    error: dict | None = None
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

    @property
    def result_handle(self) -> ResultHandle:
        return ResultHandle("result:" + self.handle.removeprefix("job:"))


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
        self._read_key = secrets.token_bytes(32)
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="TapirJob")

    def submit(self, command: str, port: int, arguments: dict, execute: Callable[[str], Any]) -> Job:
        return self.submit_prepared(command, port, arguments_preview(arguments), execute)

    @locked
    def submit_prepared(self, command: str, port: int, preview: str, execute: Callable[[str], Any]) -> Job:
        if not self._accepting:
            raise ToolError("The job store is shutting down; no new commands can be started.")
        if len(self._jobs) - len(self._completed) >= self._max_workers:
            raise ToolError(f"Server busy: all {self._max_workers} command workers are occupied. Try again later.")
        job = Job(JobHandle("job:" + uuid.uuid4().hex), command, port, preview)
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
        error = None
        try:
            result = execute(job.handle)
            if result is None:
                result = {}
        except BaseException as exc:
            # A worker exiting abnormally must still finalize its admitted job.
            log.exception("[%s] Execution failed: '%s' on port %s", job.handle, job.command, job.port)
            error = _failure_details(exc)
        self._complete(job, result, error)
        log.info("[%s] Execution end: %s", job.handle, job.status)

    @locked
    def _complete(self, job: Job, result: Any, error: dict | None) -> None:
        job.result = result
        job.error = error
        job.status = JobStatus.FAILED if error is not None else JobStatus.COMPLETED
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
        if job.error is not None:
            raise ToolError(job.error["message"])
        return job.result

    @locked
    def get(self, handle: str) -> Job:
        if handle.startswith("result:"):
            raise ToolError("archicad_get_job requires a jobHandle. Use result_read for a resultHandle.")
        self.prune()
        try:
            return self._jobs[handle]
        except KeyError:
            raise ToolError("Unknown or expired job_handle. List retained jobs with archicad_get_job().") from None

    @locked
    def list_jobs(self) -> dict:
        self.prune()
        return {"jobs": [job.summary() for job in reversed(self._jobs.values())]}

    @locked
    def response(self, job: Job) -> dict:
        response = {"jobHandle": job.handle, "status": job.status.value}
        if job.status == JobStatus.COMPLETED:
            response["result"] = job.result
        elif job.status == JobStatus.FAILED:
            response["error"] = dict(job.error)
        return response

    @locked
    def get_result(self, handle: str) -> "Completion":
        if not handle.startswith("result:"):
            raise ToolError("A resultHandle is required. Use archicad_get_job to poll a jobHandle.")
        self.prune()
        job = self._jobs.get("job:" + handle.removeprefix("result:"))
        if job is None or job.status is not JobStatus.COMPLETED:
            raise ToolError("Unknown or expired resultHandle. Request resultMode='handle' when executing a command.")
        return job.result

    def sign_read_cursor(self, value: bytes) -> str:
        return hmac.new(self._read_key, value, hashlib.sha256).hexdigest()

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
