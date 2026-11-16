"""Tokenization, normalization, document loading, and per-document statistics."""

from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path

from voyant import analysis
from voyant.corpus import load_paths, load_text, normalize, tokenize

from tests.support import corpus_from


class TokenizeTests(unittest.TestCase):
    def test_lowercases_and_drops_punctuation(self) -> None:
        tokens, offsets = tokenize("The Harbor, the HARBOR!")
        self.assertEqual(tokens, ["the", "harbor", "the", "harbor"])
        self.assertEqual(offsets, [(0, 3), (4, 10), (12, 15), (16, 22)])

    def test_apostrophes_inside_words_are_kept(self) -> None:
        tokens, _ = tokenize("Don't stop, DON'T! 'quoted' rock'n'roll")
        self.assertEqual(tokens, ["don't", "stop", "don't", "quoted", "rock'n'roll"])

    def test_digits_are_tokens_and_underscores_split(self) -> None:
        tokens, _ = tokenize("version 2.0 rocks_now")
        self.assertEqual(tokens, ["version", "2", "0", "rocks", "now"])

    def test_accents_are_folded(self) -> None:
        tokens, _ = tokenize("Café naïve Ångström")
        self.assertEqual(tokens, ["cafe", "naive", "angstrom"])

    def test_text_without_words_gives_no_tokens(self) -> None:
        self.assertEqual(tokenize(""), ([], []))
        self.assertEqual(tokenize("... --- !!!"), ([], []))

    def test_offsets_slice_back_to_the_original_words(self) -> None:
        text = "Ships sail; the Harbor waits."
        _, offsets = tokenize(text)
        self.assertEqual([text[start:end] for start, end in offsets], ["Ships", "sail", "the", "Harbor", "waits"])


class NormalizeTests(unittest.TestCase):
    def test_lowercases_and_removes_combining_marks(self) -> None:
        self.assertEqual(normalize("École"), "ecole")
        self.assertEqual(normalize("plain"), "plain")


class DocumentAndCorpusTests(unittest.TestCase):
    def test_load_text_defaults_title_to_id(self) -> None:
        doc = load_text("alpha beta", doc_id="7")
        self.assertEqual((doc.id, doc.title, doc.source), ("7", "7", ""))
        self.assertEqual(doc.tokens, ["alpha", "beta"])

    def test_type_counts_and_token_count(self) -> None:
        doc = load_text("a b a c", doc_id="1")
        self.assertEqual(doc.token_count, 4)
        self.assertEqual(doc.type_counts, Counter({"a": 2, "b": 1, "c": 1}))

    def test_corpus_totals_count_tokens_and_distinct_types(self) -> None:
        corpus = corpus_from(("one", "a b a"), ("two", "b c"))
        self.assertEqual(len(corpus), 2)
        self.assertEqual(corpus.tokens, 5)
        self.assertEqual(corpus.types, 3)

    def test_type_mean_and_population_stdev_per_document(self) -> None:
        # "the cat sat the cat ran": type counts 2, 2, 1, 1 -> mean 1.5, stdev 0.5
        corpus = corpus_from(("a", "the cat sat the cat ran"), ("b", "dog dog dog"), ("c", "!!!"))
        self.assertAlmostEqual(corpus.type_mean(0), 1.5)
        self.assertAlmostEqual(corpus.type_stdev(0), 0.5)
        self.assertAlmostEqual(corpus.type_mean(1), 3.0)
        self.assertEqual(corpus.type_stdev(1), 0.0)
        self.assertEqual((corpus.type_mean(2), corpus.type_stdev(2)), (0.0, 0.0))


class LoadPathsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, relative: str, data: bytes | str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8")
        return path

    def test_directory_keeps_only_text_suffixes_in_sorted_order(self) -> None:
        for name in ["b.md", "a.txt", "c.TEXT", "d.html", "e.csv", ".hidden.txt"]:
            self.write(name, "word")
        self.write("sub/z.txt", "word")
        corpus = load_paths([str(self.root)])
        self.assertEqual([doc.title for doc in corpus.documents], ["a", "b", "c", "z"])
        self.assertEqual([doc.id for doc in corpus.documents], ["1", "2", "3", "4"])

    def test_duplicate_file_names_stay_separate_documents(self) -> None:
        self.write("one/report.txt", "alpha")
        self.write("two/report.txt", "beta")
        corpus = load_paths([str(self.root)])
        self.assertEqual([doc.title for doc in corpus.documents], ["report", "report"])
        self.assertEqual([doc.tokens for doc in corpus.documents], [["alpha"], ["beta"]])
        self.assertEqual([stats.index for stats in analysis.documents(corpus)], [0, 1])

    def test_utf8_bom_is_stripped_and_latin1_is_the_fallback(self) -> None:
        bom = self.write("bom.txt", b"\xef\xbb\xbfcaf\xc3\xa9 ok")
        latin = self.write("latin.txt", b"caf\xe9 ok")
        corpus = load_paths([str(bom), str(latin)])
        self.assertEqual(corpus.documents[0].text, "café ok")
        self.assertEqual(corpus.documents[1].text, "café ok")
        self.assertEqual(corpus.documents[1].tokens, ["cafe", "ok"])

    def test_missing_path_raises_file_not_found(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_paths([str(self.root / "missing.txt")])

    def test_directory_without_text_files_is_an_error(self) -> None:
        self.write("notes.html", "<p>word</p>")
        with self.assertRaisesRegex(ValueError, "corpus is empty"):
            load_paths([str(self.root)])


if __name__ == "__main__":
    unittest.main()
