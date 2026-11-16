"""Corpus loading, tokenization, and the counts every tool reads from."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

# A word is a run of letters or digits, apostrophes inside a word included,
# so "don't" stays one token the way Voyant's word tokenizer keeps it.
_TOKEN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)


def normalize(token: str) -> str:
    folded = unicodedata.normalize("NFD", token.lower())
    return "".join(ch for ch in folded if unicodedata.category(ch) != "Mn")


@dataclass
class Document:
    id: str
    title: str
    source: str
    text: str
    tokens: list[str]
    offsets: list[tuple[int, int]]

    @property
    def token_count(self) -> int:
        return len(self.tokens)

    @property
    def type_counts(self) -> Counter[str]:
        return Counter(self.tokens)


@dataclass
class Corpus:
    documents: list[Document]
    _type_mean: list[float] = field(default_factory=list, repr=False)
    _type_stdev: list[float] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        for doc in self.documents:
            counts = doc.type_counts
            if not counts:
                self._type_mean.append(0.0)
                self._type_stdev.append(0.0)
                continue
            values = list(counts.values())
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            self._type_mean.append(mean)
            self._type_stdev.append(math.sqrt(variance))

    def __len__(self) -> int:
        return len(self.documents)

    @property
    def tokens(self) -> int:
        return sum(doc.token_count for doc in self.documents)

    @property
    def types(self) -> int:
        return len({token for doc in self.documents for token in doc.tokens})

    def type_mean(self, doc_index: int) -> float:
        return self._type_mean[doc_index]

    def type_stdev(self, doc_index: int) -> float:
        return self._type_stdev[doc_index]


def tokenize(text: str) -> tuple[list[str], list[tuple[int, int]]]:
    tokens: list[str] = []
    offsets: list[tuple[int, int]] = []
    for match in _TOKEN.finditer(text):
        tokens.append(normalize(match.group()))
        offsets.append((match.start(), match.end()))
    return tokens, offsets


def load_text(text: str, doc_id: str, title: str = "", source: str = "") -> Document:
    tokens, offsets = tokenize(text)
    return Document(
        id=doc_id,
        title=title or doc_id,
        source=source,
        text=text,
        tokens=tokens,
        offsets=offsets,
    )


def _read(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def load_paths(paths: list[str]) -> Corpus:
    documents: list[Document] = []
    seen: list[Path] = []
    for raw in paths:
        path = Path(raw).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"no such file or directory: {path}")
        if path.is_dir():
            seen.extend(sorted(p for p in path.rglob("*") if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in {".txt", ".md", ".text"}))
        else:
            seen.append(path)
    if not seen:
        raise ValueError("corpus is empty: no files found")
    for index, path in enumerate(seen, start=1):
        text = _read(path)
        documents.append(load_text(text, doc_id=str(index), title=path.stem, source=str(path)))
    return Corpus(documents)
