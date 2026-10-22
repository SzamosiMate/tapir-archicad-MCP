"""Compact validation errors: grouped by error type, without the rejected input values."""

from pydantic import ValidationError

MAX_LOCATION_CHARS = 80
MAX_MESSAGE_CHARS = 200


def format_validation_error(
    command_name: str, error: ValidationError, max_types: int = 5, max_locations: int = 3
) -> str:
    """
    One line per error type with its count, the message of its first error and its
    first few locations, so a rejected bulk call stays short however many items fail
    the same way. Locations name the failing fields (including unexpected keys) but
    never their values; both locations and messages are shortened.
    """
    errors = error.errors(include_input=False, include_url=False, include_context=False)
    groups: dict[str, list[dict]] = {}
    for item in errors:
        groups.setdefault(item["type"], []).append(item)

    lines = [
        f"Invalid arguments provided for tool '{command_name}': "
        f"{_count(len(errors), 'error')} of {_count(len(groups), 'type')}."
    ]
    for error_type, items in list(groups.items())[:max_types]:
        line = f"- {error_type} ({len(items)}): {_shorten(items[0]['msg'], MAX_MESSAGE_CHARS)}"
        locations = [_location(item["loc"]) for item in items[:max_locations] if item["loc"]]
        if locations:
            more = ", …" if len(items) > max_locations else ""
            line += f" at {', '.join(locations)}{more}"
        lines.append(line)
    if len(groups) > max_types:
        lines.append(f"…and {_count(len(groups) - max_types, 'more error type')}.")
    lines.append(f"Call archicad_get_command_schema('{command_name}') for the exact schema.")
    return "\n".join(lines)


def _location(loc: tuple) -> str:
    # Unexpected keys come from the caller; escape control characters so a key cannot add lines.
    path = ".".join(str(part) for part in loc).encode("unicode_escape").decode("ascii")
    return _shorten(path, MAX_LOCATION_CHARS)


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"
