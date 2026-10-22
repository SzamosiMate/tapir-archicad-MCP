"""Pagination snapshots owned and retained by execution jobs."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

PAGE_SIZE = 100
INVALID_TOKEN = "Invalid or expired page_token. Please start a new request."


@dataclass(frozen=True)
class PaginationRequest:
    connection: Any
    port: int
    command: str
    parameters: str
    field: str


@dataclass
class PaginationSnapshot:
    request: PaginationRequest
    response: dict
    token: str

    def page(self, offset: int = 0) -> dict:
        field = self.request.field
        response = deepcopy({key: value for key, value in self.response.items() if key != field})
        items = self.response[field]
        response[field] = deepcopy(items[offset : offset + PAGE_SIZE])
        response.pop("next_page_token", None)
        if offset + PAGE_SIZE < len(items):
            response["next_page_token"] = f"{self.token}:{offset + PAGE_SIZE}"
        return response

    def continuation(self, request: PaginationRequest, raw_offset: str) -> dict:
        original = self.request
        if (
            request.command != original.command
            or request.port != original.port
            or request.parameters != original.parameters
            or request.field != original.field
            or (request.connection is not None and request.connection is not original.connection)
        ):
            raise ToolError(INVALID_TOKEN)
        return self.page(self._page_offset(raw_offset))

    def _page_offset(self, raw_offset: str) -> int:
        item_count = len(self.response[self.request.field])
        if len(raw_offset) > len(str(item_count)) or not raw_offset.isascii() or not raw_offset.isdecimal():
            raise ToolError(INVALID_TOKEN)
        offset = int(raw_offset)
        if offset <= 0 or offset % PAGE_SIZE or offset >= item_count:
            raise ToolError(INVALID_TOKEN)
        return offset


def prepare_result(response: Any, request: PaginationRequest, token: str) -> Any:
    if not isinstance(response, dict) or not isinstance(response.get(request.field), list):
        return response
    if len(response[request.field]) <= PAGE_SIZE:
        return response
    # The snapshot is the only retained full copy. Jobs render page one on demand.
    return PaginationSnapshot(request, deepcopy(response), token)
