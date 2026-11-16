"""Command line for the Voyant-style tools.

    python -m voyant summary texts/
    python -m voyant terms texts/ --limit 20
    python -m voyant contexts texts/ --query love --context 6
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from typing import Any

from . import __version__, analysis
from .corpus import Corpus, load_paths


def _add_paths(parser: argparse.ArgumentParser) -> None:
    _ = parser.add_argument("paths", nargs="+", help="text files or directories of text files")
    _ = parser.add_argument("--stopwords", default="en", help="stopword list: 'en' (default) or 'none'")


def _add_corpus(parser: argparse.ArgumentParser) -> None:
    _add_paths(parser)
    _ = parser.add_argument("--json", action="store_true", help="print JSON instead of a table")


def _add_filter(parser: argparse.ArgumentParser) -> None:
    _ = parser.add_argument("--query", default=None, help="terms to keep; commas separate terms, * is a prefix")
    _ = parser.add_argument("--limit", type=int, default=30)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="voyant", description="Lightweight Voyant Tools analysis for local text files.")
    parser.add_argument("--version", action="version", version=f"voyant {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    _add_corpus(sub.add_parser("summary", help="documents, tokens, types"))
    _add_corpus(sub.add_parser("documents", help="per-document length and vocabulary"))

    terms = sub.add_parser("terms", help="corpus terms, the data behind Cirrus and Terms")
    _add_corpus(terms)
    _add_filter(terms)
    _ = terms.add_argument("--min-raw", type=int, default=1)

    doc_terms = sub.add_parser("document-terms", help="per-document terms with z-score and tf-idf")
    _add_corpus(doc_terms)
    _add_filter(doc_terms)
    _ = doc_terms.add_argument("--doc", type=int, default=None, help="restrict to one document index")

    freqs = sub.add_parser("frequencies", help="raw and relative frequency of query terms")
    _add_corpus(freqs)
    _ = freqs.add_argument("--query", required=True)

    trend = sub.add_parser("trends", help="term frequency across equal segments of each document")
    _add_corpus(trend)
    _ = trend.add_argument("--query", required=True)
    _ = trend.add_argument("--segments", type=int, default=10)

    ctx = sub.add_parser("contexts", help="keyword in context")
    _add_corpus(ctx)
    _ = ctx.add_argument("--query", required=True)
    _ = ctx.add_argument("--context", type=int, default=5)
    _ = ctx.add_argument("--limit", type=int, default=30)

    col = sub.add_parser("collocates", help="terms that occur near a query term")
    _add_corpus(col)
    _ = col.add_argument("--query", required=True)
    _ = col.add_argument("--context", type=int, default=5)
    _ = col.add_argument("--limit", type=int, default=30)

    phr = sub.add_parser("phrases", help="repeated multi-word sequences")
    _add_corpus(phr)
    _ = phr.add_argument("--min-length", type=int, default=2)
    _ = phr.add_argument("--max-length", type=int, default=4)
    _ = phr.add_argument("--min-raw", type=int, default=2)
    _ = phr.add_argument("--limit", type=int, default=30)

    corr = sub.add_parser("correlations", help="Pearson correlation between terms and between documents")
    _add_corpus(corr)
    _add_filter(corr)

    segment_corr = sub.add_parser("segment-correlations", help="Pearson correlation across equal segments inside each document")
    _add_paths(segment_corr)
    _ = segment_corr.add_argument("--query", required=True, help="at least two comma-separated terms")
    _ = segment_corr.add_argument("--segments", type=int, default=10)
    _ = segment_corr.add_argument("--json", action="store_true")

    view = sub.add_parser("view", help="write one offline HTML file with linked analysis views")
    _add_paths(view)
    _ = view.add_argument("--output", required=True, help="HTML file to write")
    _ = view.add_argument("--segments", type=int, default=12)
    _ = view.add_argument("--window", type=int, default=5, help="tokens on either side counted as co-occurrence")
    return parser


def _cell(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                parts.append(_cell(item.get("relative_freq", item.get("raw_freq", ""))))
            else:
                parts.append(_cell(item))
        return ",".join(parts)
    if value is None:
        return ""
    return str(value)


def _color_enabled() -> bool:
    return sys.stdout.isatty()


def _print_contexts(rows: list[dict[str, object]]) -> None:
    if not rows:
        print("(no results)")
        return
    left_width = min(48, max(len(str(row["left"])) for row in rows))
    color = _color_enabled()
    for row in rows:
        left = str(row["left"]).rjust(left_width)
        term = str(row["term"])
        if color:
            term = f"\033[1;33m{term}\033[0m"
        print(f"{str(row['title'])[:16]:<16}  {left}  {term}  {row['right']}")


def _segment_values(row: dict[str, object]) -> list[float]:
    segments = row["segments"]
    if not isinstance(segments, list):
        return []
    return [float(segment["relative_freq"]) for segment in segments if isinstance(segment, dict)]


def _print_trends(rows: list[dict[str, object]]) -> None:
    if not rows:
        print("(no results)")
        return
    grouped: dict[str, list[dict[str, object]]] = {}
    peak = 0.0
    for row in rows:
        grouped.setdefault(str(row["term"]), []).append(row)
        peak = max([peak, *_segment_values(row)])
    for term, group in grouped.items():
        print(f"# {term}  (shared relative-frequency scale, peak {peak:.6g})")
        for row in group:
            label = str(row["index"])
            print(f"{label:>3} {str(row['title'])[:16]:<16}  {analysis.sparkline(_segment_values(row), scale=peak)}  raw {row['raw_freq']}")
        print()


def _print_table(rows: list[dict[str, object]], columns: list[str]) -> None:
    if not rows:
        print("(no results)")
        return
    rendered = [{col: _cell(row.get(col)) for col in columns} for row in rows]
    widths = {col: max([len(col), *[len(cells[col]) for cells in rendered]]) for col in columns}
    widths = {col: min(width, 48) for col, width in widths.items()}
    print("  ".join(col.ljust(widths[col]) for col in columns))
    print("  ".join("-" * widths[col] for col in columns))
    for cells in rendered:
        print("  ".join(cells[col][: widths[col]].ljust(widths[col]) for col in columns))


def _dump(value: object) -> None:
    json.dump(_plain(value), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


def _plain(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {key: _plain(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    if isinstance(value, float):
        return round(value, 6)
    return value


def _rows(value: object) -> list[dict[str, object]]:
    plain = _plain(value)
    if isinstance(plain, list):
        return [row for row in plain if isinstance(row, dict)]
    return []


def _require_positive(name: str, value: int, *, allow_zero: bool = False) -> None:
    if value < 0 or (value == 0 and not allow_zero):
        least = "0" if allow_zero else "1"
        raise ValueError(f"{name} must be at least {least}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        for name in ("segments", "window", "context", "limit", "min_raw", "min_length", "max_length"):
            if getattr(args, name, None) is not None:
                _require_positive(name, int(getattr(args, name)), allow_zero=name == "context")
        if getattr(args, "doc", None) is not None and int(args.doc) < 0:
            raise ValueError("doc must be at least 0")
        if getattr(args, "stopwords", None) is not None:
            _ = analysis.stopword_set(str(args.stopwords))
        corpus = load_paths(list(args.paths))
        return _dispatch(args, corpus)
    except (FileNotFoundError, ValueError, IndexError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


def _dispatch(args: argparse.Namespace, corpus: Corpus) -> int:
    command = str(args.command)
    as_json = bool(getattr(args, "json", False))
    if command == "view":
        from .view import write_view

        path = write_view(corpus, str(args.output), segments=int(args.segments), window=int(args.window), stopwords=str(args.stopwords))
        print(path)
        return 0
    if command == "summary":
        result = analysis.summary(corpus)
        if as_json:
            _dump(result)
        else:
            _print_table([_plain(result)], list(asdict(result).keys()))
        return 0
    if command == "documents":
        result = analysis.documents(corpus)
    elif command == "terms":
        result = analysis.corpus_terms(corpus, query=args.query, stopwords=args.stopwords, limit=int(args.limit), min_raw=int(args.min_raw))
    elif command == "document-terms":
        result = analysis.document_terms(corpus, query=args.query, stopwords=args.stopwords, limit=int(args.limit), doc=args.doc)
    elif command == "frequencies":
        result = analysis.frequencies(corpus, query=str(args.query))
    elif command == "trends":
        result = analysis.trends(corpus, query=str(args.query), segments=int(args.segments))
        if not as_json:
            _print_trends(_rows(result))
            return 0
    elif command == "contexts":
        result = analysis.contexts(corpus, query=str(args.query), context=int(args.context), limit=int(args.limit))
        if not as_json:
            _print_contexts(_rows(result))
            return 0
    elif command == "collocates":
        result = analysis.collocates(corpus, query=str(args.query), context=int(args.context), stopwords=args.stopwords, limit=int(args.limit))
    elif command == "phrases":
        result = analysis.phrases(corpus, min_length=int(args.min_length), max_length=int(args.max_length), min_raw=int(args.min_raw), stopwords=args.stopwords, limit=int(args.limit))
    elif command == "segment-correlations":
        result = analysis.segment_correlations(corpus, query=str(args.query), segments=int(args.segments))
    elif command == "correlations":
        result = analysis.correlations(corpus, query=args.query, stopwords=args.stopwords, limit=int(args.limit))
        if as_json:
            _dump(result)
            return 0
        print("# terms")
        _print_table(_rows(result.terms), ["term1", "term2", "correlation"])
        print("\n# documents")
        _print_table(_rows(result.documents), ["index1", "doc1", "index2", "doc2", "correlation"])
        return 0
    else:
        raise AssertionError(command)
    if as_json:
        _dump(result)
    else:
        rows = _rows(result)
        columns = list(rows[0].keys()) if rows else []
        _print_table(rows, columns)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
