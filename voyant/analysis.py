"""Core Voyant tools.

relativeFreq = rawFreq / tokens in scope
zscore = (rawFreq - mean type frequency) / stdev of type frequencies, per document
tfidf = (rawFreq / document tokens) * log10(documents / document frequency)
correlation = Pearson r of per-document relative frequencies
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

from .corpus import Corpus, normalize
from .stopwords import ENGLISH

_QUERY = re.compile(r"\s+")


def stopword_set(name: str | None) -> frozenset[str]:
    if name is None or name.lower() == "none":
        return frozenset()
    if name.lower() == "en":
        return ENGLISH
    raise ValueError(f"unknown stopword list: {name}")


def segment_bounds(total: int, segments: int) -> list[int]:
    """Token indexes where each segment starts, plus the exclusive end.

    Membership matches segment_index. Five tokens and two segments split
    3 + 2, not 2 + 3.
    """
    if segments < 1:
        raise ValueError("segments must be at least 1")
    bounds = [0]
    for position in range(total):
        segment = segment_index(position, total, segments)
        while len(bounds) <= segment:
            bounds.append(position)
    while len(bounds) < segments:
        bounds.append(total)
    bounds.append(total)
    return bounds


def segment_index(position: int, total: int, segments: int) -> int:
    if total <= 0 or segments < 1:
        return 0
    return min(segments - 1, position * segments // total)


def parse_query(query: str | None) -> list[str]:
    if not query or not query.strip():
        return []
    terms: list[str] = []
    for part in re.split(r"[,|]", query):
        for word in _QUERY.split(part.strip()):
            if word:
                terms.append(normalize(word))
    return terms


def _matches(term: str, queries: list[str]) -> bool:
    if not queries:
        return True
    return any(term == q or (q.endswith("*") and term.startswith(q[:-1])) for q in queries)


def _relative(raw: int, total: int) -> float:
    return raw / total if total else 0.0


def _ppm(raw: int, total: int) -> float:
    return _relative(raw, total) * 1_000_000


_SPARK = "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"


def sparkline(values: list[float], *, scale: float | None = None) -> str:
    if not values:
        return ""
    peak = max(values) if scale is None else scale
    if peak <= 0:
        return _SPARK[0] * len(values)
    return "".join(_SPARK[min(7, int(value / peak * 8))] if value > 0 else _SPARK[0] for value in values)


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2 or n != len(ys):
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


@dataclass
class Summary:
    documents: int
    tokens: int
    types: int
    longest_title: str
    longest_tokens: int
    shortest_title: str
    shortest_tokens: int
    average_tokens: float


@dataclass
class DocumentStats:
    index: int
    title: str
    tokens: int
    types: int
    type_token_ratio: float


@dataclass
class CorpusTermRow:
    term: str
    raw_freq: int
    relative_freq: float
    ppm: float
    in_documents: int
    distribution: list[int]


@dataclass
class DocumentTermRow:
    index: int
    title: str
    term: str
    raw_freq: int
    relative_freq: float
    zscore: float | None
    tfidf: float


@dataclass
class Segment:
    bin: int
    raw_freq: int
    relative_freq: float


@dataclass
class TrendRow:
    index: int
    title: str
    term: str
    raw_freq: int
    segments: list[Segment]


@dataclass
class ContextRow:
    index: int
    title: str
    position: int
    left: str
    term: str
    right: str


@dataclass
class CollocateRow:
    term: str
    term_raw_freq: int
    context_term: str
    context_raw_freq: int


@dataclass
class PhraseRow:
    phrase: str
    length: int
    raw_freq: int
    distribution: list[int]


@dataclass
class TermCorrelation:
    term1: str
    term2: str
    correlation: float


@dataclass
class DocumentCorrelation:
    index1: int
    doc1: str
    index2: int
    doc2: str
    correlation: float


@dataclass
class Correlations:
    terms: list[TermCorrelation]
    documents: list[DocumentCorrelation]


@dataclass
class FrequencyDoc:
    index: int
    title: str
    raw_freq: int
    relative_freq: float
    ppm: float


@dataclass
class FrequencyRow:
    term: str
    raw_freq: int
    relative_freq: float
    ppm: float
    documents: list[FrequencyDoc]


@dataclass(frozen=True)
class SegmentCorrelation:
    index: int
    title: str
    term1: str
    term2: str
    segments: int
    correlation: float | None


def summary(corpus: Corpus) -> Summary:
    longest = max(corpus.documents, key=lambda doc: doc.token_count)
    shortest = min(corpus.documents, key=lambda doc: doc.token_count)
    return Summary(
        documents=len(corpus),
        tokens=corpus.tokens,
        types=corpus.types,
        longest_title=longest.title,
        longest_tokens=longest.token_count,
        shortest_title=shortest.title,
        shortest_tokens=shortest.token_count,
        average_tokens=corpus.tokens / len(corpus) if corpus else 0.0,
    )


def documents(corpus: Corpus) -> list[DocumentStats]:
    return [
        DocumentStats(
            index=index,
            title=doc.title,
            tokens=doc.token_count,
            types=len(doc.type_counts),
            type_token_ratio=_relative(len(doc.type_counts), doc.token_count),
        )
        for index, doc in enumerate(corpus.documents)
    ]


def corpus_terms(
    corpus: Corpus,
    *,
    query: str | None = None,
    stopwords: str | None = "en",
    limit: int = 50,
    min_raw: int = 1,
) -> list[CorpusTermRow]:
    stops = stopword_set(stopwords)
    queries = parse_query(query)
    per_doc = [doc.type_counts for doc in corpus.documents]
    totals: Counter[str] = Counter()
    for counts in per_doc:
        totals.update(counts)
    rows: list[CorpusTermRow] = []
    for term, raw in totals.items():
        if raw < min_raw or term in stops or not _matches(term, queries):
            continue
        distribution = [counts[term] for counts in per_doc]
        rows.append(
            CorpusTermRow(
                term=term,
                raw_freq=raw,
                relative_freq=_relative(raw, corpus.tokens),
                ppm=_ppm(raw, corpus.tokens),
                in_documents=sum(1 for value in distribution if value),
                distribution=distribution,
            )
        )
    rows.sort(key=lambda row: (-row.raw_freq, row.term))
    return rows[:limit]


def document_terms(
    corpus: Corpus,
    *,
    query: str | None = None,
    stopwords: str | None = "en",
    limit: int = 50,
    doc: int | None = None,
) -> list[DocumentTermRow]:
    stops = stopword_set(stopwords)
    queries = parse_query(query)
    doc_freq: Counter[str] = Counter()
    for document in corpus.documents:
        doc_freq.update(document.type_counts.keys())
    doc_count = len(corpus)
    selected = range(doc_count) if doc is None else [doc]
    rows: list[DocumentTermRow] = []
    for index in selected:
        document = corpus.documents[index]
        mean = corpus.type_mean(index)
        stdev = corpus.type_stdev(index)
        for term, raw in document.type_counts.items():
            if term in stops or not _matches(term, queries):
                continue
            idf = math.log10(doc_count / doc_freq[term]) if doc_freq[term] else 0.0
            rows.append(
                DocumentTermRow(
                    index=index,
                    title=document.title,
                    term=term,
                    raw_freq=raw,
                    relative_freq=_relative(raw, document.token_count),
                    zscore=(raw - mean) / stdev if stdev else None,
                    tfidf=_relative(raw, document.token_count) * idf,
                )
            )
    rows.sort(key=lambda row: (-row.raw_freq, row.index, row.term))
    return rows[:limit]


def trends(corpus: Corpus, *, query: str, segments: int = 10) -> list[TrendRow]:
    terms = parse_query(query)
    if not terms:
        raise ValueError("trends needs at least one query term")
    if segments < 1:
        raise ValueError("segments must be at least 1")
    rows: list[TrendRow] = []
    for doc_index, document in enumerate(corpus.documents):
        bounds = segment_bounds(document.token_count, segments)
        bins: list[Counter[str]] = [Counter() for _ in range(segments)]
        for position, token in enumerate(document.tokens):
            bins[segment_index(position, document.token_count, segments)][token] += 1
        sizes = [bounds[i + 1] - bounds[i] for i in range(segments)]
        for term in terms:
            counts = [b[term] for b in bins]
            rows.append(
                TrendRow(
                    index=doc_index,
                    title=document.title,
                    term=term,
                    raw_freq=sum(counts),
                    segments=[
                        Segment(bin=i, raw_freq=counts[i], relative_freq=_relative(counts[i], sizes[i]))
                        for i in range(segments)
                    ],
                )
            )
    return rows


def contexts(corpus: Corpus, *, query: str, context: int = 5, limit: int = 50) -> list[ContextRow]:
    wanted = set(parse_query(query))
    if not wanted:
        return []
    if context < 0:
        raise ValueError("context must be at least 0")
    rows: list[ContextRow] = []
    for doc_index, document in enumerate(corpus.documents):
        for position, token in enumerate(document.tokens):
            if token not in wanted:
                continue
            rows.append(
                ContextRow(
                    index=doc_index,
                    title=document.title,
                    position=position,
                    left=" ".join(document.tokens[max(0, position - context) : position]),
                    term=token,
                    right=" ".join(document.tokens[position + 1 : position + 1 + context]),
                )
            )
            if len(rows) >= limit:
                return rows
    return rows


def collocates(
    corpus: Corpus,
    *,
    query: str,
    context: int = 5,
    stopwords: str | None = "en",
    limit: int = 30,
    min_raw: int = 1,
) -> list[CollocateRow]:
    keywords = set(parse_query(query))
    if not keywords:
        return []
    stops = stopword_set(stopwords) | keywords
    context_counts: Counter[str] = Counter()
    keyword_hits = 0
    for document in corpus.documents:
        positions = [i for i, token in enumerate(document.tokens) if token in keywords]
        keyword_hits += len(positions)
        for position in positions:
            start = max(0, position - context)
            end = min(len(document.tokens), position + context + 1)
            for index in range(start, end):
                if index == position:
                    continue
                token = document.tokens[index]
                if token not in stops:
                    context_counts[token] += 1
    label = ", ".join(sorted(keywords))
    rows = [
        CollocateRow(term=label, term_raw_freq=keyword_hits, context_term=term, context_raw_freq=raw)
        for term, raw in context_counts.items()
        if raw >= min_raw
    ]
    rows.sort(key=lambda row: (-row.context_raw_freq, row.context_term))
    return rows[:limit]


def _contains(haystack: tuple[str, ...], needle: tuple[str, ...]) -> bool:
    span = len(needle)
    return any(haystack[i : i + span] == needle for i in range(len(haystack) - span + 1))


def phrases(
    corpus: Corpus,
    *,
    min_length: int = 2,
    max_length: int = 4,
    min_raw: int = 2,
    stopwords: str | None = "en",
    limit: int = 40,
) -> list[PhraseRow]:
    stops = stopword_set(stopwords)
    counts: dict[int, Counter[tuple[str, ...]]] = {n: Counter() for n in range(min_length, max_length + 1)}
    distribution: dict[tuple[int, tuple[str, ...]], list[int]] = defaultdict(lambda: [0] * len(corpus))
    for doc_index, document in enumerate(corpus.documents):
        tokens = document.tokens
        for n in counts:
            for i in range(len(tokens) - n + 1):
                gram = tuple(tokens[i : i + n])
                if not any(token not in stops for token in gram):
                    continue
                counts[n][gram] += 1
                distribution[(n, gram)][doc_index] += 1
    candidates: list[tuple[int, tuple[str, ...], int]] = []
    for n, counter in counts.items():
        for gram, raw in counter.items():
            if raw >= min_raw:
                candidates.append((n, gram, raw))
    longer = {(gram, raw) for n, gram, raw in candidates if n > min_length}
    kept: list[tuple[int, tuple[str, ...], int]] = []
    for n, gram, raw in candidates:
        shadowed = n < max_length and any(
            len(other) > n and other_raw == raw and _contains(other, gram) for other, other_raw in longer
        )
        if not shadowed:
            kept.append((n, gram, raw))
    kept.sort(key=lambda item: (-item[2], -item[0], item[1]))
    return [
        PhraseRow(phrase=" ".join(gram), length=n, raw_freq=raw, distribution=distribution[(n, gram)])
        for n, gram, raw in kept[:limit]
    ]


def correlations(
    corpus: Corpus,
    *,
    query: str | None = None,
    stopwords: str | None = "en",
    limit: int = 20,
    min_docs: int = 2,
) -> Correlations:
    stops = stopword_set(stopwords)
    queries = parse_query(query)
    per_doc = [doc.type_counts for doc in corpus.documents]
    sizes = [doc.token_count for doc in corpus.documents]
    totals: Counter[str] = Counter()
    for counts in per_doc:
        totals.update(counts)
    vocabulary = [
        term
        for term, _raw in totals.most_common()
        if term not in stops and sum(1 for counts in per_doc if counts[term]) >= min_docs
    ]
    targets = [term for term in vocabulary if _matches(term, queries)] if queries else vocabulary[:limit]

    def series(term: str) -> list[float]:
        return [_relative(counts[term], size) for counts, size in zip(per_doc, sizes)]

    term_rows: list[TermCorrelation] = []
    seen: set[tuple[str, str]] = set()
    for left in targets[:limit]:
        left_series = series(left)
        for right in vocabulary[: max(limit * 4, 80)]:
            if left == right:
                continue
            pair = (left, right) if left < right else (right, left)
            if pair in seen:
                continue
            score = _pearson(left_series, series(right))
            if score is None:
                continue
            seen.add(pair)
            term_rows.append(TermCorrelation(left, right, score))
    term_rows.sort(key=lambda row: -abs(row.correlation))

    shared = vocabulary[:200]
    doc_series = [[_relative(counts[term], sizes[index]) for term in shared] for index, counts in enumerate(per_doc)]
    doc_rows: list[DocumentCorrelation] = []
    for i in range(len(corpus)):
        for j in range(i + 1, len(corpus)):
            score = _pearson(doc_series[i], doc_series[j])
            if score is None:
                continue
            doc_rows.append(DocumentCorrelation(i, corpus.documents[i].title, j, corpus.documents[j].title, score))
    doc_rows.sort(key=lambda row: -row.correlation)
    return Correlations(terms=term_rows[:limit], documents=doc_rows)


def frequencies(corpus: Corpus, *, query: str) -> list[FrequencyRow]:
    rows: list[FrequencyRow] = []
    for term in parse_query(query):
        docs = [
            FrequencyDoc(
                index=doc_index,
                title=document.title,
                raw_freq=document.type_counts[term],
                relative_freq=_relative(document.type_counts[term], document.token_count),
                ppm=_ppm(document.type_counts[term], document.token_count),
            )
            for doc_index, document in enumerate(corpus.documents)
        ]
        total = sum(item.raw_freq for item in docs)
        rows.append(FrequencyRow(term, total, _relative(total, corpus.tokens), _ppm(total, corpus.tokens), docs))
    return rows


def segment_correlations(corpus: Corpus, *, query: str, segments: int = 10) -> list[SegmentCorrelation]:
    terms = parse_query(query)
    if len(terms) < 2:
        raise ValueError("segment correlation needs at least two query terms")
    if segments < 2:
        raise ValueError("segment correlation needs at least two segments")
    rows: list[SegmentCorrelation] = []
    observed = trends(corpus, query=query, segments=segments)
    for doc_index, document in enumerate(corpus.documents):
        series = {
            row.term: [segment.relative_freq for segment in row.segments]
            for row in observed
            if row.index == doc_index
        }
        for index, left in enumerate(terms):
            for right in terms[index + 1 :]:
                rows.append(
                    SegmentCorrelation(
                        index=doc_index,
                        title=document.title,
                        term1=left,
                        term2=right,
                        segments=segments,
                        correlation=_pearson(series[left], series[right]),
                    )
                )
    return rows
