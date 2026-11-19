"""Bounded command discovery with a client-held record of previously returned results."""

import base64
import hashlib
import json
import re
from itertools import zip_longest
from typing import Annotated, Literal

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from tapir_archicad_mcp.tools.custom.command_discovery import (
    GroupDirectory,
    _command_group,
    _groups,
    _overview,
    _rank_keywords,
)
from tapir_archicad_mcp.tools.custom.models import CommandOverview
from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG

PAGE_BYTES = 28 * 1024
SEARCH_RESULTS = 12
_IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")


class ExactMatch(BaseModel):
    keyword_index: int
    status: Literal["found", "missing", "outside_groups"]


class CataloguePage(BaseModel):
    names: str | None = None
    matches: list[CommandOverview] | None = None
    exact_matches: list[ExactMatch]
    remaining: int
    query_id: str


class CatalogueSnapshot:
    def __init__(self, catalog_names: list[str]):
        self.indices = {name: index for index, name in enumerate(catalog_names)}
        self.fingerprint = hashlib.sha256("\n".join(catalog_names).encode()).hexdigest()[:16]
        self.mask_bytes = (len(catalog_names) + 7) // 8

    def read(self, query_id: str) -> tuple[int, int]:
        if not query_id:
            return 0, 0
        fingerprint, _, payload = query_id.partition(".")
        try:
            bits = base64.b64decode(payload, altchars=b"-_", validate=True)
        except ValueError:
            bits = b""
        if fingerprint != self.fingerprint or len(bits) != self.mask_bytes * 2:
            raise ToolError("Invalid query_id for this catalogue. Omit query_id to start a fresh chain.")
        compact = int.from_bytes(bits[: self.mask_bytes], "little")
        full = int.from_bytes(bits[self.mask_bytes :], "little")
        return compact, full

    def write(self, compact: int, full: int) -> str:
        bits = compact.to_bytes(self.mask_bytes, "little") + full.to_bytes(self.mask_bytes, "little")
        return f"{self.fingerprint}.{base64.urlsafe_b64encode(bits).decode('ascii')}"

    def bit(self, name: str) -> int:
        return 1 << self.indices[name]


def _merge_ranks(lexical: list[str], vector: list[str]) -> list[str]:
    scores: dict[str, float] = {}
    for ranking in (lexical, vector):
        for rank, name in enumerate(ranking, start=1):
            scores[name] = scores.get(name, 0) + 1 / (20 + rank)
    return sorted(scores, key=lambda name: (-scores[name], name))


def _rank_batch(keywords, scope, snapshot, vector_index):
    rankings = []
    exact_matches = []
    scoped = set(scope)
    approximate = []
    for index, keyword in enumerate(keywords):
        identifier = keyword.casefold()
        if _IDENTIFIER.fullmatch(identifier):
            status = (
                "found" if identifier in scoped else "outside_groups" if identifier in snapshot.indices else "missing"
            )
            exact_matches.append(ExactMatch(keyword_index=index, status=status))
        if identifier in scoped:
            rankings.append([identifier])
        else:
            approximate.append((index, keyword))
            rankings.append(_rank_keywords(keyword, scope))

    if approximate and vector_index is not None:
        semantic = vector_index.ranks([query for _, query in approximate], scope)
        for (index, _), ranking in zip(approximate, semantic, strict=True):
            rankings[index] = _merge_ranks(rankings[index], ranking)

    # Interleave independent intents before the result limit is applied.
    combined = dict.fromkeys(name for row in zip_longest(*rankings) for name in row if name is not None)
    return list(combined), exact_matches


def _page(candidates, exact_matches, compact, full, detail, snapshot, has_keywords):
    seen = full if detail == "full" else compact | full
    available = [name for name in candidates if not seen & snapshot.bit(name)]
    page = CataloguePage(exact_matches=exact_matches, remaining=len(available), query_id=snapshot.write(compact, full))
    # Leave space for the MCP SDK's structured result envelope.
    budget = PAGE_BYTES - len(page.model_dump_json().encode()) - 32
    selected: list[str] = []
    matches: list[CommandOverview] = []
    for name in available[:SEARCH_RESULTS] if has_keywords else available:
        if detail == "full":
            overview = _overview(name)
            size = len(overview.model_dump_json().encode()) + 1
        else:
            size = len(json.dumps(name, ensure_ascii=False).encode())
        if size > budget:
            break
        budget -= size
        selected.append(name)
        if detail == "full":
            matches.append(overview)
            full |= snapshot.bit(name)
        else:
            compact |= snapshot.bit(name)
    if available and not selected:
        raise ToolError("A command description exceeds the catalogue page size. Request compact results.")
    page.names = "\n".join(selected) if detail == "compact" else None
    page.matches = matches if detail == "full" else None
    page.remaining -= len(selected)
    page.query_id = snapshot.write(compact, full)
    return page


def chain_tool(hybrid: bool):
    vector_index = None
    if hybrid:
        try:
            from tapir_archicad_mcp.tools.custom.discovery_vectors import prepare_index
        except ModuleNotFoundError as error:
            raise RuntimeError("Install fastembed==0.9.1 to use chain-hybrid discovery.") from error

        vector_index = prepare_index()

    def discover_commands(
        groups: Annotated[list[str] | None, Field(description="Group IDs to search or browse together.")] = None,
        keywords: Annotated[
            list[Annotated[str, Field(max_length=256)]] | None,
            Field(
                max_length=8, description="Independent phrases or exact command names. Batch distinct workflow steps."
            ),
        ] = None,
        query_id: Annotated[
            str,
            Field(max_length=4096, description="Latest query_id to continue this chain while skipping seen results."),
        ] = "",
        detail: Annotated[
            Literal["compact", "full"] | None,
            Field(description="Defaults to full with keywords, compact for browsing."),
        ] = None,
        list_groups: Annotated[bool, Field(description="Return the directory and command counts.")] = False,
    ) -> CataloguePage | GroupDirectory:
        """Search for commands by passing several keyword phrases or exact names in one call. Use groups to narrow scope.

        Without keywords, browse compact names. Use detail=full to see descriptions, or list_groups=true for the group
        directory. Pass the latest query_id on each follow-up, including refinements with new groups or keywords. A name
        already returned in compact form can still be returned with its full description. Repeat the same arguments with
        the latest query_id to retrieve remaining results. Omit query_id to start a fresh search.
        """
        if list_groups:
            return _groups()
        keywords = [value.strip() for value in keywords or [] if value.strip()]
        group_ids = {group.strip().casefold() for group in groups or [] if group.strip()}
        unknown = group_ids - {entry.group for entry in _groups().groups}
        if unknown:
            raise ToolError(f"Unknown catalogue groups: {', '.join(sorted(unknown))}. Use list_groups=true.")
        snapshot = CatalogueSnapshot(list(TOOL_DISCOVERY_CATALOG))
        compact, full = snapshot.read(query_id)
        scope = [name for name in snapshot.indices if not group_ids or _command_group(name) in group_ids]
        ranked, exact = _rank_batch(keywords, scope, snapshot, vector_index) if keywords else (scope, [])
        return _page(
            ranked, exact, compact, full, detail or ("full" if keywords else "compact"), snapshot, bool(keywords)
        )

    return discover_commands
