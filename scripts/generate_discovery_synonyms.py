"""Compile catalogue-specific aliases from the pinned Open English WordNet release."""

import ast
import gzip
import hashlib
import json
import logging
import urllib.request
from collections import defaultdict
from pathlib import Path
from xml.etree.ElementTree import iterparse

from tapir_archicad_mcp.search_terms import search_terms

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
WORDNET_VERSION = "2025"
WORDNET_FILENAME = f"english-wordnet-{WORDNET_VERSION}.xml.gz"
WORDNET_URL = f"https://en-word.net/static/{WORDNET_FILENAME}"
WORDNET_SHA256 = "9ca6d1dcb75f822fdd66617f7d9da48142ace38dd544d6ad5e2feca1674ad3fe"
WORDNET_CACHE = ROOT / ".tmp" / "discovery-wordnet" / WORDNET_FILENAME
TOOLS = ROOT / "src" / "tapir_archicad_mcp" / "tools"
OUTPUT = TOOLS / "generated" / "discovery_synonyms.json"


def generate_synonyms(source: Path) -> None:
    vocabulary = {term for name in command_names() for term in search_terms(name)}
    aliases = compile_synonyms(source, vocabulary)
    data = {
        "source": WORDNET_URL,
        "source_sha256": WORDNET_SHA256,
        "license_notice": "WORDNET-LICENSE.txt",
        "aliases": aliases,
    }
    OUTPUT.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    log.info("Generated %d discovery aliases for %d command-name terms.", len(aliases), len(vocabulary))


def command_names() -> set[str]:
    names = set()
    for directory in (TOOLS / "generated", TOOLS / "custom"):
        for path in directory.rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "register_tool_for_dispatch"
                ):
                    name = next(kw.value for kw in node.keywords if kw.arg == "name")
                    names.add(ast.literal_eval(name))
    return names


def wordnet_source() -> Path:
    if WORDNET_CACHE.is_file() and hashlib.sha256(WORDNET_CACHE.read_bytes()).hexdigest() == WORDNET_SHA256:
        return WORDNET_CACHE
    log.info("Fetching Open English WordNet %s.", WORDNET_VERSION)
    with urllib.request.urlopen(WORDNET_URL, timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != WORDNET_SHA256:
        raise ValueError(f"Unexpected checksum for the pinned WordNet source at {WORDNET_URL}.")
    WORDNET_CACHE.parent.mkdir(parents=True, exist_ok=True)
    WORDNET_CACHE.write_bytes(data)
    return WORDNET_CACHE


def compile_synonyms(source: Path, vocabulary: set[str]) -> dict[str, str]:
    words, related = read_synsets(source)
    direct: dict[str, set[str]] = defaultdict(set)
    derived: dict[str, set[str]] = defaultdict(set)
    anchors = {synset: members & vocabulary for synset, members in words.items()}
    for synset, members in words.items():
        targets = anchors[synset]
        derived_targets = {term for other in related.get(synset, ()) for term in anchors.get(other, ())}
        if not targets and not derived_targets:
            continue
        for alias in members - vocabulary:
            direct[alias].update(targets)
            derived[alias].update(derived_targets)

    # Prefer direct synsets and retain aliases only when they point to one catalogue term.
    aliases = {}
    for alias, targets in direct.items():
        candidates = targets or derived[alias]
        if len(candidates) == 1:
            aliases[alias] = next(iter(candidates))
    return aliases


def read_synsets(source: Path) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    words: dict[str, set[str]] = defaultdict(set)
    sense_synsets: dict[str, str] = {}
    derivations: list[tuple[str, str]] = []
    with gzip.open(source, "rb") as stream:
        for _, node in iterparse(stream, events=("end",)):
            if node.tag == "LexicalEntry":
                lemma = node.find("Lemma")
                if lemma is not None and lemma.attrib["partOfSpeech"] in {"n", "v"}:
                    spelling = lemma.attrib["writtenForm"].casefold()
                    normalized = search_terms(spelling) if spelling.isalpha() else set()
                    for sense in node.findall("Sense"):
                        synset = sense.attrib["synset"]
                        sense_synsets[sense.attrib["id"]] = synset
                        words[synset].update(normalized)
                        derivations.extend(
                            (synset, relation.attrib["target"])
                            for relation in sense.findall("SenseRelation")
                            if relation.attrib["relType"] == "derivation"
                        )
                node.clear()
            elif node.tag == "Synset":
                node.clear()

    related: dict[str, set[str]] = defaultdict(set)
    for source_synset, target_sense in derivations:
        target_synset = sense_synsets.get(target_sense)
        if target_synset is not None:
            related[source_synset].add(target_synset)
            related[target_synset].add(source_synset)
    return words, related


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_synonyms(wordnet_source())
