"""Shared word normalization for discovery and its generated vocabulary."""

import re

_WORD = re.compile(r"[^\W_]+", re.UNICODE)


def search_words(text: str) -> list[str]:
    return _WORD.findall(text.casefold())


def search_terms(text: str) -> set[str]:
    return {
        word.removesuffix("s") if len(word) > 3 and not word.endswith("ss") else word for word in search_words(text)
    }
