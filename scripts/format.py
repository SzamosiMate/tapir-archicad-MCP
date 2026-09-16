import json
import logging
import subprocess
from pathlib import Path
from textwrap import wrap
import tomllib


log = logging.getLogger(__name__)


def _find_ruff_config_file() -> Path | None:
    """Traverse up directory tree to locate pyproject.toml or ruff.toml."""
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        pyproject = parent / "pyproject.toml"
        if pyproject.is_file():
            return pyproject
        ruff_toml = parent / "ruff.toml"
        if ruff_toml.is_file():
            return ruff_toml
    return None


def get_max_line_length(default: int = 120) -> int:
    """Read line-length directly from pyproject.toml [tool.ruff], falling back to default."""
    if tomllib is None:
        return default

    config_path = _find_ruff_config_file()
    if not config_path:
        return default

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        # 1. Check [tool.ruff] line-length in pyproject.toml
        line_length = data.get("tool", {}).get("ruff", {}).get("line-length")
        if line_length is not None:
            return int(line_length)

        # 2. Check root line-length in ruff.toml
        line_length = data.get("line-length")
        if line_length is not None:
            return int(line_length)
    except Exception as e:
        log.warning(f"Could not read line-length from {config_path}: {e}")

    return default


MAX_LINE_LENGTH = get_max_line_length()


def format_docstring(
    description: str,
    addendum: str = "",
    max_line_length: int = MAX_LINE_LENGTH,
    indent_spaces: int = 4,
) -> str:
    """
    Format a function docstring. Keeps it on a single line if it fits within max_line_length;
    otherwise wraps paragraphs so that no line exceeds max_line_length once indented.
    """
    available_width = max_line_length - indent_spaces
    clean_desc = " ".join(description.strip().split())
    has_addendum = bool(addendum.strip())

    # Fits on a single line: indent + 3 quotes + text + 3 quotes <= max_line_length
    if not has_addendum and (indent_spaces + 6 + len(clean_desc) <= max_line_length):
        return f'"""{clean_desc}"""'

    paragraphs = [clean_desc]
    if has_addendum:
        paragraphs.append(" ".join(addendum.strip().split()))

    wrapped_lines = []
    for i, para in enumerate(paragraphs):
        if i > 0:
            wrapped_lines.append("")
        wrapped_lines.extend(wrap(para, width=available_width))

    body = "\n".join(wrapped_lines)
    return f'"""\n{body}\n"""'


def format_string_literal(
    text: str,
    indent_spaces: int = 4,
    max_line_length: int = MAX_LINE_LENGTH,
) -> str:
    """
    Format a string argument. If it exceeds max_line_length, wrap it into
    implicit parenthesized string concatenations so that no line exceeds the limit.
    """
    clean_text = " ".join(text.strip().split())
    # indent + 16 chars for '    description=' + 1 trailing comma
    if indent_spaces + 17 + len(json.dumps(clean_text)) <= max_line_length:
        return json.dumps(clean_text)

    chunk_indent = " " * (indent_spaces + 4)
    max_chunk_width = max_line_length - len(chunk_indent) - 3

    words = clean_text.split(" ")
    lines = []
    current_words = []
    current_len = 0

    for word in words:
        addition = len(word) + (1 if current_words else 0)
        if current_words and (current_len + addition > max_chunk_width):
            lines.append(" ".join(current_words) + " ")
            current_words = [word]
            current_len = len(word)
        else:
            current_words.append(word)
            current_len += addition

    if current_words:
        lines.append(" ".join(current_words))

    chunks = [f"{chunk_indent}{json.dumps(line)}" for line in lines]
    closing_indent = " " * indent_spaces
    return "(\n" + "\n".join(chunks) + f"\n{closing_indent})"


def run_ruff_format(*dirs: Path) -> None:
    """Format target directories using Ruff."""
    target_dirs = [str(d) for d in dirs if d.exists()]
    if not target_dirs:
        return

    log.info(f"Running ruff format on: {', '.join(target_dirs)}...")
    subprocess.run(["ruff", "format", *target_dirs], check=True)