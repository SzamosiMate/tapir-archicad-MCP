"""Bounded JSON rendering and the delivery decision for a completed result."""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from mcp.types import CallToolResult, ImageContent, TextContent

from tapir_archicad_mcp.metadata_types import CommandMetadata, Presentation
from tapir_archicad_mcp.result_budget import JSON_ENCODER, ResultBudget, token_count
from tapir_archicad_mcp.result_data import StoredResult, is_sequence


class ResultMode(StrEnum):
    AUTO = "auto"
    INLINE = "inline"
    HANDLE = "handle"


class ByteLimitExceeded(Exception):
    pass


@dataclass(frozen=True)
class Encoded:
    text: str
    images: tuple[ImageContent, ...]

    def mcp(self) -> CallToolResult:
        return CallToolResult(
            content=[TextContent(type="text", text=self.text), *self.images],
            structured_content=json.loads(self.text),
        )


def encode(value: Any, limit: int | None = None, *, max_images: int | None = None) -> Encoded:
    """Stop at the byte limit without materializing unbounded views or large strings."""
    chunks: list[str] = []
    images: list[ImageContent] = []
    remaining = limit

    def emit(part: str):
        nonlocal remaining
        if remaining is not None:
            remaining -= len(part.encode("utf-8"))
            if remaining < 0:
                raise ByteLimitExceeded
        chunks.append(part)

    def write(item: Any):
        if isinstance(item, ImageContent):
            if max_images is not None and len(images) >= max_images:
                raise ByteLimitExceeded
            images.append(item)
            write(f"returned as MCP image content #{len(images)}")
        elif isinstance(item, Mapping):
            emit("{")
            for index, (key, child) in enumerate(item.items()):
                if index:
                    emit(",")
                write(key)
                emit(":")
                write(child)
            emit("}")
        elif is_sequence(item):
            emit("[")
            for index, child in enumerate(item):
                if index:
                    emit(",")
                write(child)
            emit("]")
        else:
            if isinstance(item, str) and remaining is not None and len(item) > remaining:
                raise ByteLimitExceeded
            emit(JSON_ENCODER.encode(item))

    write(value)
    return Encoded("".join(chunks), tuple(images))


@dataclass(frozen=True)
class Completion:
    result: StoredResult
    handle_reason: str | None
    notices: dict


def complete(result: StoredResult, metadata: CommandMetadata, mode: ResultMode, budget: ResultBudget) -> Completion:
    root = result.root()
    reason = delivery_reason(root, metadata, mode, budget)
    notices = {}
    if reason is not None:
        for field in metadata.summary_fields:
            if field in root:
                try:
                    notices[field] = json.loads(encode(root[field], 768).text)
                except ByteLimitExceeded:
                    notices[field] = _notice_sample(root[field])
    return Completion(result, reason, notices)


def _notice_sample(value: Any) -> dict:
    if isinstance(value, str):
        return {"sample": value[:160], "truncated": True}
    if is_sequence(value):
        first = value[0] if value else None
        summary = {"count": len(value), "truncated": True}
        if isinstance(first, str):
            summary["sample"] = first[:160]
        return summary
    if isinstance(value, Mapping) and isinstance(value.get("message"), str):
        return {"sample": value["message"][:160], "truncated": True}
    return {"truncated": True}


def delivery_reason(root: Mapping, metadata: CommandMetadata, mode: ResultMode, budget: ResultBudget) -> str | None:
    if mode is ResultMode.HANDLE:
        return "requested"
    if (
        mode is ResultMode.AUTO
        and metadata.presentation is Presentation.HANDLE_PREFERRED
        and (metadata.inline_if_true is None or root.get(metadata.inline_if_true) is not True)
        and (metadata.handle_if_list is None or is_sequence(root.get(metadata.handle_if_list)))
    ):
        return "command_preference"
    try:
        encoded = encode(root, budget.max_bytes)
    except ByteLimitExceeded:
        return "byte_limit"
    limit = budget.auto_tokens if mode is ResultMode.AUTO else budget.inline_tokens
    return "token_limit" if token_count(encoded.text) > limit else None


def deliver(completion: Completion, result_handle: str, *, job_handle: str | None = None) -> CallToolResult:
    envelope = {"status": "completed"}
    if job_handle is not None:
        envelope["jobHandle"] = job_handle
    if completion.handle_reason is None:
        data = completion.result.root()
        return encode(data if job_handle is None else {**envelope, "result": data}).mcp()
    return encode(
        {
            **envelope,
            "resultHandle": result_handle,
            "summary": completion.result.summary,
            "deliveryReason": completion.handle_reason,
            **({"notices": completion.notices} if completion.notices else {}),
            "next": 'Use result_read to inspect, or pass {"$handle": resultHandle} with an optional path to a command.',
        },
    ).mcp()
