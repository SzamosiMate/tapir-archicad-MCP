"""Compact JSON and the offline o200k_base reference-token budget.

The expression and vocabulary are the o200k_base encoding published by
OpenAI's tiktoken project. See TIKTOKEN-LICENSE.txt.
"""

import json
from base64 import b64decode
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from threading import Lock

from tiktoken import Encoding

_PATTERN = (
    r"[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*[\p{Ll}\p{Lm}\p{Lo}\p{M}]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?"
    r"|[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?"
    r"|\p{N}{1,3}"
    r"| ?[^\s\p{L}\p{N}]+[\r\n/]*"
    r"|\s*[\r\n]+"
    r"|\s+(?!\S)"
    r"|\s+"
)
_TOKENIZER_LOCK = Lock()


@cache
def _encoding() -> Encoding:
    with files(__package__).joinpath("o200k_base.tiktoken").open("rb") as vocabulary:
        ranks = {b64decode(token): int(rank) for token, rank in map(bytes.split, vocabulary)}
    return Encoding(
        "o200k_base",
        pat_str=_PATTERN,
        mergeable_ranks=ranks,
        special_tokens={"<|endoftext|>": 199999, "<|endofprompt|>": 200018},
    )


def token_count(text: str) -> int:
    # functools.cache alone can build the encoding twice on simultaneous misses.
    with _TOKENIZER_LOCK:
        tokenizer = _encoding()
    return len(tokenizer.encode_ordinary(text))


JSON_ENCODER = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class ResultBudget:
    auto_tokens: int = 8_000
    inline_tokens: int = 32_000
    max_bytes: int = 128 * 1024

    def __post_init__(self) -> None:
        if not 0 < self.auto_tokens <= self.inline_tokens or self.max_bytes <= 0:
            raise ValueError("Result limits must be positive, and the auto token limit cannot exceed the inline limit.")
