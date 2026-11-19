"""Lexical search and bounded continuations for the command catalogue."""

import json
import math
import re
from collections import Counter, OrderedDict
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from secrets import token_urlsafe
from threading import Lock
from time import monotonic
from typing import Annotated, Literal

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import BaseModel, Field

from tapir_archicad_mcp.search_terms import search_terms, search_words
from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG

PAGE_BYTES = 28 * 1024
HITS_PER_PHRASE = 3
QUERY_TTL_SECONDS = 30 * 60
MAX_QUERY_STATES = 1024
_QUERY_ID_LENGTH = 12
_MULTIWORD_GROUPS = ("custom_data", "design_options", "project_data", "solid_ops")
_IDENTIFIER = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+")


class PhraseMatches(BaseModel):
    keyword_index: int
    commands: list[str]
    remaining: int
    exact_status: Literal["found", "missing", "outside_groups"] | None = None


class SearchPage(BaseModel):
    matches: list[PhraseMatches]
    descriptions: dict[str, str]
    query_id: str


class BrowsePage(BaseModel):
    names: str
    remaining: int
    query_id: str


class CatalogueResult(BaseModel):
    result: SearchPage | BrowsePage


@dataclass(frozen=True)
class SeenCommands:
    compact: frozenset[str] = frozenset()
    full: frozenset[str] = frozenset()


def archicad_list_commands(
    groups: Annotated[list[str] | None, Field(description="Group IDs to search or browse together.")] = None,
    keywords: Annotated[
        list[Annotated[str, Field(max_length=256)]] | None,
        Field(max_length=8, description="Independent phrases or exact command names. Batch distinct workflow steps."),
    ] = None,
    query_id: Annotated[
        str, Field(description="Latest query_id from the previous response. Reuse it on every follow-up for this task.")
    ] = "",
) -> CatalogueResult:
    """Search by keyword phrases or exact command names. Batch separate workflow steps and narrow by groups as needed.

    For every follow-up on the same user request, pass the latest query_id from the previous response, even when
    replacing all keywords or changing groups. Omit query_id to start a new task or restart an unavailable chain.

    Each entry in matches returns up to three command names for its keyword_index. Ranked hits share the descriptions
    map keyed by command name. An exact name in scope returns that name and its status. Omit keywords to browse names."""
    phrases = [(index, keyword.strip()) for index, keyword in enumerate(keywords or []) if keyword.strip()]
    group_ids = {group.strip().casefold() for group in groups or [] if group.strip()}
    scope = list(TOOL_DISCOVERY_CATALOG)
    if group_ids:
        unknown = group_ids.difference(command_groups())
        if unknown:
            unknown_groups = ", ".join(sorted(unknown))
            raise ToolError(f"Unknown catalogue groups: {unknown_groups}. See the tool description for group IDs.")
        scope = [name for name in scope if _command_group(name) in group_ids]
    seen = _continuations.read(query_id)
    page = _search_page(phrases, scope, seen, query_id) if phrases else _browse_page(scope, seen, query_id)
    return CatalogueResult(result=page)


def command_groups() -> list[str]:
    return sorted({_command_group(name) for name in TOOL_DISCOVERY_CATALOG})


def _command_group(name: str) -> str:
    return next((group for group in _MULTIWORD_GROUPS if name.startswith(f"{group}_")), name.split("_", 1)[0])


def _search_page(phrases: list[tuple[int, str]], scope: list[str], seen: SeenCommands, query_id: str) -> SearchPage:
    scoped = set(scope)
    seen_names = seen.compact | seen.full
    matches: list[PhraseMatches] = []
    descriptions: dict[str, str] = {}
    exact_names: set[str] = set()
    ranked_matches: list[tuple[PhraseMatches, list[str]]] = []
    for index, phrase in phrases:
        identifier = phrase.casefold()
        if identifier in scoped:
            names = [] if identifier in seen_names else [identifier]
            exact_names.update(names)
            matches.append(PhraseMatches(keyword_index=index, commands=names, remaining=0, exact_status="found"))
            continue

        exact_status = None
        if _IDENTIFIER.fullmatch(identifier):
            exact_status = "outside_groups" if identifier in TOOL_DISCOVERY_CATALOG else "missing"
        candidates = [name for name in _rank_keywords(phrase, scope) if name not in seen.full]
        names = candidates[:HITS_PER_PHRASE]
        match = PhraseMatches(keyword_index=index, commands=names, remaining=0, exact_status=exact_status)
        matches.append(match)
        ranked_matches.append((match, candidates))
        descriptions.update((name, TOOL_DISCOVERY_CATALOG[name]["description"]) for name in names)

    # A description returned for one phrase has also been seen by the other phrases on the page.
    for match, candidates in ranked_matches:
        match.remaining = sum(name not in descriptions for name in candidates)
    updated = SeenCommands(seen.compact.union(exact_names).difference(descriptions), seen.full.union(descriptions))
    next_id = _continuations.write(updated) if descriptions or exact_names or not query_id else query_id
    return SearchPage(matches=matches, descriptions=descriptions, query_id=next_id)


def _rank_keywords(query: str, names: list[str]) -> list[str]:
    query_terms = search_terms(query)
    synonym_terms = _synonym_terms(query) - query_terms
    document_frequency: Counter[str] = Counter()
    matches: list[tuple[str, set[str], set[str], set[str]]] = []
    for name in names:
        name_terms = search_terms(name)
        name_hits = query_terms & name_terms
        description_hits = query_terms & search_terms(TOOL_DISCOVERY_CATALOG[name]["description"])
        hits = name_hits | description_hits
        synonym_hits = synonym_terms & name_terms
        if hits or synonym_hits:
            document_frequency.update(hits | synonym_hits)
            matches.append((name, name_hits, hits, synonym_hits))

    # Rarer terms carry more information, and identifier matches have higher weight.
    weights = {term: math.log1p(len(names) / frequency) for term, frequency in document_frequency.items()}

    def rank(match: tuple[str, set[str], set[str], set[str]]) -> tuple[float, str]:
        name, name_hits, hits, synonym_hits = match
        score = math.fsum(weights[term] for term in hits) + 2 * math.fsum(weights[term] for term in name_hits)
        score += 2 * math.fsum(weights[term] for term in synonym_hits)
        return -score, name

    matches.sort(key=rank)
    return [name for name, *_ in matches]


def _synonym_terms(query: str) -> set[str]:
    aliases = _synonyms()
    targets = set()
    for word in search_words(query):
        target = aliases.get(word) or aliases.get(word.removesuffix("s"))
        if target is None and word.endswith(("ches", "shes", "sses", "xes", "zes")):
            target = aliases.get(word[:-2])
        if target is not None:
            targets.add(target)
    return targets


@cache
def _synonyms() -> dict[str, str]:
    path = files("tapir_archicad_mcp.tools.generated").joinpath("discovery_synonyms.json")
    return json.loads(path.read_text(encoding="utf-8"))["aliases"]


def _browse_page(scope: list[str], seen: SeenCommands, query_id: str) -> BrowsePage:
    excluded = seen.compact | seen.full
    available = [name for name in scope if name not in excluded]
    page = BrowsePage(names="", remaining=len(available), query_id="0" * _QUERY_ID_LENGTH)
    # Leave room for the structured result envelope and JSON separators.
    budget = PAGE_BYTES - len(page.model_dump_json().encode()) - 32
    selected: list[str] = []
    for name in available:
        # Command identifiers contain only ASCII letters, digits and underscores.
        size = len(name) + 2
        if size > budget:
            break
        budget -= size
        selected.append(name)
    if available and not selected:
        raise ToolError("A command name exceeds the catalogue page size.")
    page.names = "\n".join(selected)
    updated = SeenCommands(seen.compact.union(selected), seen.full)
    page.remaining -= len(selected)
    page.query_id = _continuations.write(updated) if selected or not query_id else query_id
    return page


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
