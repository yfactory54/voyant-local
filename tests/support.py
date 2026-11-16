"""Shared helpers for the voyant test suite (standard library only)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from voyant.corpus import Corpus, load_text

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES = REPO_ROOT / "samples"
FONT_FILES = (
    "source-sans-3-400.woff2",
    "source-sans-3-600.woff2",
    "source-serif-4-500.woff2",
    "source-serif-4-600.woff2",
)


def corpus_from(*pairs: tuple[str, str]) -> Corpus:
    """Build an in-memory Corpus from (title, text) pairs; ids are "1", "2", ... as in load_paths."""
    return Corpus(
        [load_text(text, doc_id=str(number), title=title) for number, (title, text) in enumerate(pairs, start=1)]
    )


def bag(counts: dict[str, int]) -> str:
    """Text holding each word the given number of times, in no particular order."""
    return " ".join(word for word, n in counts.items() for _ in range(n))


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Run `python -m voyant ARGS` from the repository root and capture stdout and stderr."""
    return subprocess.run(
        [sys.executable, "-m", "voyant", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
