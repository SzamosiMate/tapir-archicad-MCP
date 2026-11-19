"""Lexical search and bounded continuations for the command catalogue."""

import math
import re
from collections import Counter, OrderedDict
from dataclasses import dataclass
from itertools import zip_longest
from secrets import token_urlsafe
from threading import Lock
from time import monotonic
from typing import Annotated, Literal

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from tapir_archicad_mcp.tools.custom.models import CommandOverview
from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG

PAGE_BYTES = 28 * 1024
SEARCH_RESULTS = 12
QUERY_TTL_SECONDS = 30 * 60
MAX_QUERY_STATES = 1024
_QUERY_ID_LENGTH = 12
_MULTIWORD_GROUPS = ("custom_data", "design_options", "project_data", "solid_ops")
_IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")
_WORD = re.compile(r"[^\W_]+", re.UNICODE)
Detail = Literal["compact", "full"]


class CommandGroup(BaseModel):
    group: str
    command_count: int


class GroupDirectory(BaseModel):
    groups: list[CommandGroup]


class ExactMatch(BaseModel):
    keyword_index: int
    status: Literal["found", "missing", "outside_groups"]


class CataloguePage(BaseModel):
    names: str | None = None
    matches: list[CommandOverview] | None = None
    exact_matches: list[ExactMatch]
    remaining: int
    query_id: str


@dataclass(frozen=True)
class SeenCommands:
    compact: frozenset[str] = frozenset()
    full: frozenset[str] = frozenset()


class QueryContinuations:
    """Bound the number and lifetime of immutable search snapshots."""

    def __init__(self) -> None:
        self._snapshots: OrderedDict[str, tuple[float, SeenCommands]] = OrderedDict()
        self._lock = Lock()

    def read(self, query_id: str) -> SeenCommands:
        if not query_id:
            return SeenCommands()
        with self._lock:
            snapshot = self._snapshots.pop(query_id, None)
            now = monotonic()
            if snapshot is None or snapshot[0] <= now:
                raise ToolError("Invalid or expired query_id. Omit query_id to start a fresh search.")
            self._snapshots[query_id] = (now + QUERY_TTL_SECONDS, snapshot[1])
            return snapshot[1]

    def write(self, seen: SeenCommands) -> str:
        with self._lock:
            query_id = token_urlsafe(9)
            while query_id in self._snapshots:
                query_id = token_urlsafe(9)
            if len(self._snapshots) >= MAX_QUERY_STATES:
                self._snapshots.popitem(last=False)
            self._snapshots[query_id] = (monotonic() + QUERY_TTL_SECONDS, seen)
            return query_id


_continuations = QueryContinuations()


def _command_group(name: str) -> str:
    return next((group for group in _MULTIWORD_GROUPS if name.startswith(f"{group}_")), name.split("_", 1)[0])


def command_group_directory() -> GroupDirectory:
    counts = Counter(map(_command_group, TOOL_DISCOVERY_CATALOG))
    return GroupDirectory(groups=[CommandGroup(group=name, command_count=counts[name]) for name in sorted(counts)])


def _terms(text: str) -> set[str]:
    return {
        word.removesuffix("s") if len(word) > 3 and not word.endswith("ss") else word
        for word in _WORD.findall(text.casefold())
    }


def _rank_keywords(query: str, names: list[str]) -> list[str]:
    query_terms = _terms(query)
    document_frequency: Counter[str] = Counter()
    matches: list[tuple[str, set[str], set[str]]] = []
    for name in names:
        name_hits = query_terms & _terms(name)
        description_hits = query_terms & _terms(TOOL_DISCOVERY_CATALOG[name]["description"])
        hits = name_hits | description_hits
        if hits:
            document_frequency.update(hits)
            matches.append((name, name_hits, hits))

    # Rarer terms carry more information, and identifier matches have higher weight.
    weights = {term: math.log1p(len(names) / frequency) for term, frequency in document_frequency.items()}

    def rank(match: tuple[str, set[str], set[str]]) -> tuple[float, str]:
        name, name_hits, hits = match
        score = math.fsum(weights[term] for term in hits) + 2 * math.fsum(weights[term] for term in name_hits)
        return -score, name

    matches.sort(key=rank)
    return [name for name, _, _ in matches]


def _rank_batch(keywords: list[tuple[int, str]], scope: list[str]) -> tuple[list[str], list[ExactMatch]]:
    scoped = set(scope)
    rankings = []
    exact_matches = []
    for index, keyword in keywords:
        identifier = keyword.casefold()
        if _IDENTIFIER.fullmatch(identifier):
            if identifier in scoped:
                status = "found"
            elif identifier in TOOL_DISCOVERY_CATALOG:
                status = "outside_groups"
            else:
                status = "missing"
            exact_matches.append(ExactMatch(keyword_index=index, status=status))
        rankings.append([identifier] if identifier in scoped else _rank_keywords(keyword, scope))

    # Interleave independent intents before applying the result limit.
    combined = dict.fromkeys(name for row in zip_longest(*rankings) for name in row if name is not None)
    return list(combined), exact_matches


def _page(
    candidates: list[str],
    exact_matches: list[ExactMatch],
    seen: SeenCommands,
    query_id: str,
    detail: Detail,
    has_keywords: bool,
) -> CataloguePage:
    excluded = seen.full if detail == "full" else seen.compact | seen.full
    available = [name for name in candidates if name not in excluded]
    page = CataloguePage(exact_matches=exact_matches, remaining=len(available), query_id="0" * _QUERY_ID_LENGTH)
    # Leave room for the structured result envelope and JSON separators.
    budget = PAGE_BYTES - len(page.model_dump_json().encode()) - 32
    selected: list[str] = []
    matches: list[CommandOverview] = []
    for name in available[:SEARCH_RESULTS] if has_keywords else available:
        if detail == "full":
            overview = CommandOverview(name=name, description=TOOL_DISCOVERY_CATALOG[name]["description"])
            size = len(overview.model_dump_json().encode()) + 1
        else:
            # Command identifiers contain only ASCII letters, digits and underscores.
            size = len(name) + 2
        if size > budget:
            break
        budget -= size
        selected.append(name)
        if detail == "full":
            matches.append(overview)

    if available and not selected:
        raise ToolError("A command description exceeds the catalogue page size. Request compact results.")
    if detail == "compact":
        page.names = "\n".join(selected)
        updated = SeenCommands(seen.compact.union(selected), seen.full)
    else:
        page.matches = matches
        updated = SeenCommands(seen.compact.difference(selected), seen.full.union(selected))
    page.remaining -= len(selected)
    page.query_id = _continuations.write(updated) if selected or not query_id else query_id
    return page


def archicad_list_commands(
    groups: Annotated[list[str] | None, Field(description="Group IDs to search or browse together.")] = None,
    keywords: Annotated[
        list[Annotated[str, Field(max_length=256)]] | None,
        Field(max_length=8, description="Independent phrases or exact command names. Batch distinct workflow steps."),
    ] = None,
    query_id: Annotated[
        str, Field(description="Latest query_id to continue the search while skipping previously returned commands.")
    ] = "",
    detail: Annotated[Detail | None, Field(description="Defaults to full with keywords, compact for browsing.")] = None,
    list_groups: Annotated[bool, Field(description="Return the group directory and command counts.")] = False,
) -> CataloguePage | GroupDirectory:
    """Search by keyword phrases or exact command names. Batch separate workflow steps and narrow by groups as needed.

    Omit keywords to browse names, set detail=full for descriptions, or use list_groups=true for the group directory.
    Pass the latest query_id for more results or to refine groups or keywords without repeats. Compact names can be
    returned again with descriptions. Omit query_id to start a fresh search."""
    if list_groups:
        return command_group_directory()

    phrases = [(index, keyword.strip()) for index, keyword in enumerate(keywords or []) if keyword.strip()]
    group_ids = {group.strip().casefold() for group in groups or [] if group.strip()}
    scope = list(TOOL_DISCOVERY_CATALOG)
    if group_ids:
        unknown = group_ids - {entry.group for entry in command_group_directory().groups}
        if unknown:
            raise ToolError(f"Unknown catalogue groups: {', '.join(sorted(unknown))}. Use list_groups=true.")
        scope = [name for name in scope if _command_group(name) in group_ids]
    seen = _continuations.read(query_id)
    ranked, exact_matches = _rank_batch(phrases, scope) if phrases else (scope, [])
    return _page(ranked, exact_matches, seen, query_id, detail or ("full" if phrases else "compact"), bool(phrases))
