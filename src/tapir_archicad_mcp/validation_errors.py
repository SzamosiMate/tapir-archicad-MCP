"""Compact validation errors: grouped by error type, without the rejected input values."""

from pydantic import ValidationError


def format_validation_error(
    command_name: str, error: ValidationError, max_types: int = 5, max_locations: int = 3
) -> str:
    """
    One line per error type with its count and first few locations, so a rejected
    bulk call stays short however many items fail the same way.
    """
    errors = error.errors(include_input=False, include_url=False)
    groups: dict[str, list[dict]] = {}
    for item in errors:
        groups.setdefault(item["type"], []).append(item)

    lines = [
        f"Invalid arguments provided for tool '{command_name}': "
        f"{_count(len(errors), 'error')} of {_count(len(groups), 'type')}."
    ]
    for error_type, items in list(groups.items())[:max_types]:
        locations = [".".join(str(part) for part in item["loc"]) for item in items[:max_locations]]
        more = ", …" if len(items) > max_locations else ""
        lines.append(f"- {error_type} ({len(items)}): {items[0]['msg']} at {', '.join(locations)}{more}")
    if len(groups) > max_types:
        lines.append(f"...and {_count(len(groups) - max_types, 'more error type')}.")
    lines.append(f"Call archicad_get_command_schema('{command_name}') for the exact schema.")
    return "\n".join(lines)


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"
