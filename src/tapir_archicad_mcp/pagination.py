from copy import deepcopy
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable
import secrets
import time

CACHE_LIFETIME_SECONDS = 1200
PAGE_SIZE = 100
MAX_CACHE_ENTRIES = 128


@dataclass(frozen=True)
class PaginationRequest:
    """The request identity that a continuation token must match."""

    connection: Any
    command: str
    parameters: str
    field: str

    def matches(self, other: "PaginationRequest") -> bool:
        return (
            self.connection is other.connection
            and self.command == other.command
            and self.parameters == other.parameters
            and self.field == other.field
        )


@dataclass
class _Snapshot:
    request: PaginationRequest
    response: dict
    created_at: float


PAGINATION_CACHE: dict[str, _Snapshot] = {}
_CACHE_LOCK = Lock()
_INVALID_TOKEN = "Invalid or expired page_token. Please start a new request."


def dispatch_paginated(
        fetch: Callable[[], Any], request: PaginationRequest, page_token: str | None = None
) -> Any:
    """Route continuation requests to the cache and initial requests to Archicad."""
    if page_token is not None:
        with _CACHE_LOCK:
            return _fetch_cached_page(request, page_token)
    response = fetch()
    with _CACHE_LOCK:
        return _cache_response(response, request)


def _fetch_cached_page(request: PaginationRequest, page_token: str) -> dict:
    _prune(time.monotonic())
    session, separator, raw_offset = page_token.partition(":")
    snapshot = PAGINATION_CACHE.get(session)
    if not separator or snapshot is None or not snapshot.request.matches(request):
        raise ValueError(_INVALID_TOKEN)
    item_count = len(snapshot.response[request.field])
    # A valid index cannot need more digits than the list length.
    if len(raw_offset) > len(str(item_count)) or not raw_offset.isascii() or not raw_offset.isdecimal():
        raise ValueError(_INVALID_TOKEN)
    offset = int(raw_offset)
    if offset <= 0 or offset % PAGE_SIZE or offset >= item_count:
        raise ValueError(_INVALID_TOKEN)
    return _page(snapshot, session, offset)


def _cache_response(response: dict, request: PaginationRequest) -> dict:
    _prune(time.monotonic())
    if not isinstance(response, dict) or not isinstance(response.get(request.field), list):
        return response
    if len(response[request.field]) <= PAGE_SIZE:
        return response

    snapshot = _Snapshot(request, deepcopy(response), time.monotonic())
    session = secrets.token_urlsafe(24)
    while len(PAGINATION_CACHE) >= MAX_CACHE_ENTRIES:
        del PAGINATION_CACHE[next(iter(PAGINATION_CACHE))]
    PAGINATION_CACHE[session] = snapshot
    return _page(snapshot, session, 0)


def _prune(now: float) -> None:
    for key, snapshot in list(PAGINATION_CACHE.items()):
        if now - snapshot.created_at >= CACHE_LIFETIME_SECONDS:
            del PAGINATION_CACHE[key]


def _page(snapshot: _Snapshot, session: str, offset: int) -> dict:
    field = snapshot.request.field
    response = deepcopy({key: value for key, value in snapshot.response.items() if key != field})
    items = snapshot.response[field]
    response[field] = deepcopy(items[offset : offset + PAGE_SIZE])
    response.pop("next_page_token", None)
    if offset + PAGE_SIZE < len(items):
        response["next_page_token"] = f"{session}:{offset + PAGE_SIZE}"
    return response
