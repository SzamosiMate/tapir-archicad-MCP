"""Alternative presentations of the registered command catalogue."""

import math
import re
from collections import Counter
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, Field

from tapir_archicad_mcp.tools.custom.functions import archicad_list_commands
from tapir_archicad_mcp.tools.custom.models import CommandOverview
from tapir_archicad_mcp.tools.tool_registry import TOOL_DISCOVERY_CATALOG

_TOOL_NAME = "archicad_list_commands"
_MULTIWORD_GROUPS = ("custom_data", "design_options", "project_data", "solid_ops")
_KEYWORD_RESULT_LIMIT = 12
_WORD = re.compile(r"[^\W_]+", re.UNICODE)


class CommandGroup(BaseModel):
    group: str
    command_count: int


class GroupDirectory(BaseModel):
    groups: list[CommandGroup]


class CommandMatches(BaseModel):
    matches: list[CommandOverview]
    total_matches: int


def _command_group(name: str) -> str:
    return next((group for group in _MULTIWORD_GROUPS if name.startswith(f"{group}_")), name.split("_", 1)[0])


def _groups() -> GroupDirectory:
    counts = Counter(map(_command_group, TOOL_DISCOVERY_CATALOG))
    return GroupDirectory(groups=[CommandGroup(group=name, command_count=counts[name]) for name in sorted(counts)])


def _group_commands(group: str) -> list[str]:
    names = [name for name in TOOL_DISCOVERY_CATALOG if _command_group(name) == group]
    if not names:
        raise ToolError(f"Unknown command group '{group}'. Omit group to list the available groups.")
    return names


def _overview(name: str) -> CommandOverview:
    return CommandOverview(name=name, description=TOOL_DISCOVERY_CATALOG[name]["description"])


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


def _find_commands(query: str, names: list[str]) -> CommandMatches:
    exact_name = "_".join(_WORD.findall(query.casefold()))
    if exact_name in names:
        return CommandMatches(matches=[_overview(exact_name)], total_matches=1)

    matches = _rank_keywords(query, names)
    return CommandMatches(
        matches=[_overview(name) for name in matches[:_KEYWORD_RESULT_LIMIT]], total_matches=len(matches)
    )


Group = Annotated[
    str, Field(description="Exact group identifier from the directory. Omit or leave empty to list groups.")
]
Query = Annotated[
    str, Field(description="An exact command name or keywords describing a command, such as 'get layers'.")
]


def list_grouped_commands(group: Group = "") -> GroupDirectory | list[CommandOverview]:
    """List command groups, or list the exact names and descriptions of the commands in one group."""
    group = group.strip().casefold()
    return [_overview(name) for name in _group_commands(group)] if group else _groups()


def list_keyword_commands(query: Query = "") -> CommandMatches | list[CommandOverview]:
    """Search globally by exact command name or keywords. The result reports the total matches and returns up to 12.

    Try different keywords if the results are incomplete. Omit the query for the full catalogue.
    """
    query = query.strip()
    return _find_commands(query, list(TOOL_DISCOVERY_CATALOG)) if query else archicad_list_commands()


def list_grouped_keyword_commands(
    group: Group = "", query: Query = ""
) -> GroupDirectory | CommandMatches | list[CommandOverview]:
    """List groups, browse one group, or search by exact command name or keywords.

    Pass query alone to search globally. Pass query and group to search within one group. Search results report the
    total matches and return up to 12. Try different keywords or browse a group if the results are incomplete.
    """
    group = group.strip().casefold()
    query = query.strip()
    if query:
        return _find_commands(query, _group_commands(group) if group else list(TOOL_DISCOVERY_CATALOG))
    return list_grouped_commands(group)


def list_command_names() -> str:
    """List all available Archicad command names, one exact name per line. Use the schema tool for a specific command."""
    return "\n".join(TOOL_DISCOVERY_CATALOG)


def configure_command_discovery(server: MCPServer, variant: str) -> None:
    """Swap the public discovery tool during startup for an alternate implementation."""
    if variant == "full":
        return
    implementations = {
        "groups": list_grouped_commands,
        "keyword": list_keyword_commands,
        "groups-keyword": list_grouped_keyword_commands,
        "names": list_command_names,
    }
    description = None
    if variant in {"chain-lexical", "chain-hybrid"}:
        from tapir_archicad_mcp.tools.custom.discovery_chain import chain_tool

        implementation = chain_tool(variant == "chain-hybrid")
        groups = ", ".join(item.group for item in _groups().groups)
        description = f"{implementation.__doc__.strip()}\n\nAvailable groups: {groups}."
    else:
        implementation = implementations[variant]
    server.remove_tool(_TOOL_NAME)
    server.add_tool(
        implementation,
        name=_TOOL_NAME,
        title="List Available Archicad Commands",
        description=description,
        annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False),
        structured_output=False if variant == "names" else None,
    )
