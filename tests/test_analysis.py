"""Hand-computed values for each analysis tool, plus samples/ regression checks."""

from __future__ import annotations

import math
import unittest

from voyant import analysis
from voyant.corpus import load_paths
from voyant.stopwords import ENGLISH

from tests.support import SAMPLES, bag, corpus_from

LOG2 = math.log10(2)

# a: "the cat sat the cat ran"  -> 6 tokens: the=2 cat=2 sat=1 ran=1
# b: "a dog sat"               -> 3 tokens: a=1 dog=1 sat=1
# corpus: 9 tokens, 6 types (the cat sat ran a dog)
COUNTS = (("a", "The cat sat. The cat ran."), ("b", "A dog sat."))


def counts_corpus():
    return corpus_from(*COUNTS)


class StopwordTests(unittest.TestCase):
    def test_en_loads_the_bundled_list(self) -> None:
        self.assertIs(analysis.stopword_set("en"), ENGLISH)
        self.assertIs(analysis.stopword_set("EN"), ENGLISH)
        self.assertIn("the", ENGLISH)
        self.assertNotIn("cat", ENGLISH)

    def test_none_gives_no_stopwords(self) -> None:
        self.assertEqual(analysis.stopword_set("none"), frozenset())
        self.assertEqual(analysis.stopword_set("NONE"), frozenset())
        self.assertEqual(analysis.stopword_set(None), frozenset())

    def test_only_en_and_none_are_accepted(self) -> None:
        for name in ("off", "false", ""):
            with self.subTest(name=name), self.assertRaises(ValueError):
                analysis.stopword_set(name)

    def test_unknown_list_is_a_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown stopword list: foo"):
            analysis.stopword_set("foo")


class SegmentBoundsTests(unittest.TestCase):
    def test_five_tokens_two_segments_split_three_then_two(self) -> None:
        self.assertEqual(analysis.segment_bounds(5, 2), [0, 3, 5])

    def test_empty_document_has_empty_segments(self) -> None:
        self.assertEqual(analysis.segment_bounds(0, 3), [0, 0, 0, 0])

    def test_one_segment_covers_everything(self) -> None:
        self.assertEqual(analysis.segment_bounds(5, 1), [0, 5])

    def test_more_segments_than_tokens_leaves_empty_segments(self) -> None:
        # 2 tokens in 5 segments: tokens fall in segments 0 and 2; sizes are 1, 0, 1, 0, 0
        bounds = analysis.segment_bounds(2, 5)
        self.assertEqual(bounds, [0, 1, 1, 2, 2, 2])
        self.assertEqual([bounds[i + 1] - bounds[i] for i in range(5)], [1, 0, 1, 0, 0])

    def test_one_token_per_segment(self) -> None:
        self.assertEqual(analysis.segment_bounds(10, 10), list(range(11)))

    def test_uneven_split_puts_extra_tokens_early(self) -> None:
        self.assertEqual(analysis.segment_bounds(7, 3), [0, 3, 5, 7])

    def test_bounds_match_the_ceiling_formula_the_view_uses(self) -> None:
        # view.py computes segment starts as ceil(s * total / segments); trends must agree.
        for total in range(0, 25):
            for segments in range(1, 9):
                with self.subTest(total=total, segments=segments):
                    expected = [0] + [-(-s * total // segments) for s in range(1, segments)] + [total]
                    self.assertEqual(analysis.segment_bounds(total, segments), expected)

    def test_zero_segments_rejected(self) -> None:
        with self.assertRaises(ValueError):
            analysis.segment_bounds(5, 0)


class ParseQueryTests(unittest.TestCase):
    def test_commas_pipes_and_spaces_separate_terms(self) -> None:
        self.assertEqual(analysis.parse_query("Voyage, HARBOR|ship  sea"), ["voyage", "harbor", "ship", "sea"])

    def test_trailing_star_is_kept_as_the_prefix_marker(self) -> None:
        self.assertEqual(analysis.parse_query("voy*"), ["voy*"])
        self.assertEqual(analysis.parse_query("Voy*, harbor*"), ["voy*", "harbor*"])

    def test_empty_queries_give_no_terms(self) -> None:
        self.assertEqual(analysis.parse_query(None), [])
        self.assertEqual(analysis.parse_query("   "), [])
        self.assertEqual(analysis.parse_query(" , "), [])

    def test_trailing_star_matches_prefixes_in_corpus_terms(self) -> None:
        corpus = corpus_from(("v", "voyage voyager vow voy"))
        rows = analysis.corpus_terms(corpus, query="voy*", stopwords="none")
        self.assertEqual([row.term for row in rows], ["voy", "voyage", "voyager"])


class SummaryTests(unittest.TestCase):
    def test_counts_and_extremes(self) -> None:
        s = analysis.summary(counts_corpus())
        self.assertEqual((s.documents, s.tokens, s.types), (2, 9, 6))
        self.assertEqual((s.longest_title, s.longest_tokens), ("a", 6))
        self.assertEqual((s.shortest_title, s.shortest_tokens), ("b", 3))
        self.assertAlmostEqual(s.average_tokens, 4.5)

    def test_documents_report_type_token_ratio(self) -> None:
        rows = analysis.documents(counts_corpus())
        self.assertEqual([(r.index, r.title, r.tokens, r.types) for r in rows], [(0, "a", 6, 4), (1, "b", 3, 3)])
        self.assertAlmostEqual(rows[0].type_token_ratio, 4 / 6)
        self.assertAlmostEqual(rows[1].type_token_ratio, 1.0)

    def test_samples_regression(self) -> None:
        corpus = load_paths([str(SAMPLES)])
        s = analysis.summary(corpus)
        self.assertEqual((s.documents, s.tokens, s.types), (3, 304, 137))
        self.assertEqual((s.longest_title, s.longest_tokens), ("voyage", 118))
        rows = analysis.documents(corpus)
        self.assertEqual([r.title for r in rows], ["harbor", "market", "voyage"])
        self.assertEqual([r.tokens for r in rows], [93, 93, 118])
        self.assertEqual([r.types for r in rows], [57, 55, 70])


class CorpusTermsTests(unittest.TestCase):
    def test_relative_frequency_uses_all_corpus_tokens(self) -> None:
        rows = analysis.corpus_terms(counts_corpus(), stopwords="none")
        self.assertEqual(
            [(r.term, r.raw_freq) for r in rows],
            [("cat", 2), ("sat", 2), ("the", 2), ("a", 1), ("dog", 1), ("ran", 1)],
        )
        cat = rows[0]
        self.assertAlmostEqual(cat.relative_freq, 2 / 9)
        self.assertAlmostEqual(cat.ppm, 2 / 9 * 1_000_000)
        self.assertEqual(cat.distribution, [2, 0])
        self.assertEqual(cat.in_documents, 1)
        sat = rows[1]
        self.assertEqual(sat.distribution, [1, 1])
        self.assertEqual(sat.in_documents, 2)

    def test_english_stoplist_removes_function_words_but_not_from_the_denominator(self) -> None:
        rows = analysis.corpus_terms(counts_corpus(), stopwords="en")
        self.assertEqual([(r.term, r.raw_freq) for r in rows], [("cat", 2), ("sat", 2), ("dog", 1), ("ran", 1)])
        self.assertAlmostEqual(rows[0].relative_freq, 2 / 9)

    def test_min_raw_and_limit(self) -> None:
        rows = analysis.corpus_terms(counts_corpus(), stopwords="none", min_raw=2)
        self.assertEqual([r.term for r in rows], ["cat", "sat", "the"])
        rows = analysis.corpus_terms(counts_corpus(), stopwords="none", limit=2)
        self.assertEqual([r.term for r in rows], ["cat", "sat"])

    def test_query_exact_and_prefix_matching(self) -> None:
        corpus = counts_corpus()
        self.assertEqual([r.term for r in analysis.corpus_terms(corpus, query="ca*", stopwords="none")], ["cat"])
        self.assertEqual([r.term for r in analysis.corpus_terms(corpus, query="cat", stopwords="none")], ["cat"])
        self.assertEqual(analysis.corpus_terms(corpus, query="ca", stopwords="none"), [])
        self.assertEqual([r.term for r in analysis.corpus_terms(corpus, query="sat,dog", stopwords="none")], ["sat", "dog"])


class DocumentTermsTests(unittest.TestCase):
    def test_tfidf_follows_the_readme_formula(self) -> None:
        # tf-idf = (count / document tokens) * log10(documents / documents containing the term)
        rows = analysis.document_terms(counts_corpus(), stopwords="none", limit=50)
        by_key = {(r.title, r.term): r for r in rows}
        self.assertEqual(len(rows), 7)
        self.assertAlmostEqual(by_key[("a", "cat")].tfidf, (2 / 6) * LOG2)
        self.assertAlmostEqual(by_key[("a", "the")].tfidf, (2 / 6) * LOG2)
        self.assertAlmostEqual(by_key[("a", "ran")].tfidf, (1 / 6) * LOG2)
        self.assertEqual(by_key[("a", "sat")].tfidf, 0.0)  # in both documents: log10(2/2) = 0
        self.assertAlmostEqual(by_key[("b", "a")].tfidf, (1 / 3) * LOG2)
        self.assertAlmostEqual(by_key[("b", "dog")].tfidf, (1 / 3) * LOG2)
        self.assertEqual(by_key[("b", "sat")].tfidf, 0.0)

    def test_idf_with_three_documents(self) -> None:
        corpus = corpus_from(("x", "alpha alpha beta"), ("y", "beta"), ("z", "beta gamma"))
        by_key = {(r.title, r.term): r for r in analysis.document_terms(corpus, stopwords="none")}
        self.assertAlmostEqual(by_key[("x", "alpha")].tfidf, (2 / 3) * math.log10(3))
        self.assertEqual(by_key[("x", "beta")].tfidf, 0.0)
        self.assertAlmostEqual(by_key[("z", "gamma")].tfidf, (1 / 2) * math.log10(3))

    def test_zscore_uses_mean_and_population_stdev_of_type_counts(self) -> None:
        # document a: type counts 2, 2, 1, 1 -> mean 1.5, stdev 0.5
        by_key = {(r.title, r.term): r for r in analysis.document_terms(counts_corpus(), stopwords="none")}
        self.assertAlmostEqual(by_key[("a", "cat")].zscore, 1.0)
        self.assertAlmostEqual(by_key[("a", "the")].zscore, 1.0)
        self.assertAlmostEqual(by_key[("a", "ran")].zscore, -1.0)
        self.assertAlmostEqual(by_key[("a", "sat")].zscore, -1.0)
        # document b: every type count is 1, so stdev is 0 and z-score is undefined
        self.assertIsNone(by_key[("b", "dog")].zscore)

    def test_stopwords_and_single_document_filter(self) -> None:
        rows = analysis.document_terms(counts_corpus(), stopwords="en", doc=1)
        self.assertEqual(sorted(r.term for r in rows), ["dog", "sat"])
        self.assertTrue(all(r.title == "b" for r in rows))

    def test_query_restricts_terms(self) -> None:
        rows = analysis.document_terms(counts_corpus(), query="sat", stopwords="none")
        self.assertEqual(sorted((r.title, r.term) for r in rows), [("a", "sat"), ("b", "sat")])


class TrendsTests(unittest.TestCase):
    def setUp(self) -> None:
        # d1: 9 tokens, harbor at positions 3 and 7. d2: 3 tokens, harbor at position 0.
        self.corpus = corpus_from(("d1", "one two three harbor four five six harbor seven"), ("d2", "harbor alpha beta"))

    def test_two_segments_counts_and_relative_frequency(self) -> None:
        # d1 segments: tokens 0-4 (5 tokens) and 5-8 (4 tokens); d2 segments: 0-1 (2) and 2 (1)
        rows = analysis.trends(self.corpus, query="harbor", segments=2)
        self.assertEqual([(r.index, r.title, r.term, r.raw_freq) for r in rows], [(0, "d1", "harbor", 2), (1, "d2", "harbor", 1)])
        d1, d2 = rows
        self.assertEqual([s.raw_freq for s in d1.segments], [1, 1])
        self.assertEqual([s.relative_freq for s in d1.segments], [1 / 5, 1 / 4])
        self.assertEqual([s.raw_freq for s in d2.segments], [1, 0])
        self.assertEqual([s.relative_freq for s in d2.segments], [1 / 2, 0.0])
        self.assertEqual([s.bin for s in d1.segments], [0, 1])

    def test_three_segments(self) -> None:
        rows = {r.index: r for r in analysis.trends(self.corpus, query="harbor", segments=3)}
        self.assertEqual([s.raw_freq for s in rows[0].segments], [0, 1, 1])
        self.assertEqual([s.relative_freq for s in rows[0].segments], [0.0, 1 / 3, 1 / 3])
        self.assertEqual([s.relative_freq for s in rows[1].segments], [1.0, 0.0, 0.0])

    def test_several_terms_and_a_missing_term(self) -> None:
        rows = analysis.trends(self.corpus, query="harbor,seven", segments=2)
        self.assertEqual([(r.index, r.term, r.raw_freq) for r in rows], [(0, "harbor", 2), (0, "seven", 1), (1, "harbor", 1), (1, "seven", 0)])
        seven = rows[1]
        self.assertEqual([s.raw_freq for s in seven.segments], [0, 1])
        self.assertEqual([s.relative_freq for s in seven.segments], [0.0, 1 / 4])

    def test_empty_query_and_zero_segments_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one query term"):
            analysis.trends(self.corpus, query="")
        with self.assertRaisesRegex(ValueError, "segments must be at least 1"):
            analysis.trends(self.corpus, query="harbor", segments=0)


class ContextsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = corpus_from(("d1", "one two three harbor four five six harbor seven"), ("d2", "harbor alpha beta"))

    def test_left_and_right_windows(self) -> None:
        rows = analysis.contexts(self.corpus, query="harbor", context=2)
        self.assertEqual(
            [(r.index, r.title, r.position, r.left, r.term, r.right) for r in rows],
            [
                (0, "d1", 3, "two three", "harbor", "four five"),
                (0, "d1", 7, "five six", "harbor", "seven"),
                (1, "d2", 0, "", "harbor", "alpha beta"),
            ],
        )

    def test_context_zero_gives_bare_hits(self) -> None:
        rows = analysis.contexts(self.corpus, query="harbor", context=0)
        self.assertEqual([(r.left, r.right) for r in rows], [("", ""), ("", ""), ("", "")])

    def test_windows_stop_at_document_edges(self) -> None:
        rows = analysis.contexts(self.corpus, query="harbor", context=5)
        self.assertEqual(rows[2].right, "alpha beta")
        self.assertEqual(rows[0].left, "one two three")

    def test_several_terms_come_back_in_document_order(self) -> None:
        rows = analysis.contexts(self.corpus, query="harbor,seven", context=1)
        self.assertEqual([(r.index, r.position, r.term) for r in rows], [(0, 3, "harbor"), (0, 7, "harbor"), (0, 8, "seven"), (1, 0, "harbor")])

    def test_limit_truncates(self) -> None:
        rows = analysis.contexts(self.corpus, query="harbor", context=1, limit=2)
        self.assertEqual([r.position for r in rows], [3, 7])

    def test_query_matches_exactly_not_as_a_prefix(self) -> None:
        self.assertEqual(analysis.contexts(self.corpus, query="har*", context=2), [])

    def test_negative_context_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "context must be at least 0"):
            analysis.contexts(self.corpus, query="harbor", context=-1)


class CollocatesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.corpus = corpus_from(("d1", "one two three harbor four five six harbor seven"), ("d2", "harbor alpha beta"))

    def test_window_counts_without_stopwords(self) -> None:
        # window +-2 around harbor: d1 -> two three four five | five six seven; d2 -> alpha beta
        rows = analysis.collocates(self.corpus, query="harbor", context=2, stopwords="none", limit=30)
        self.assertEqual(
            [(r.context_term, r.context_raw_freq) for r in rows],
            [("five", 2), ("alpha", 1), ("beta", 1), ("four", 1), ("seven", 1), ("six", 1), ("three", 1), ("two", 1)],
        )
        self.assertTrue(all(r.term == "harbor" and r.term_raw_freq == 3 for r in rows))

    def test_limit_and_min_raw(self) -> None:
        rows = analysis.collocates(self.corpus, query="harbor", context=2, stopwords="none", limit=3)
        self.assertEqual([r.context_term for r in rows], ["five", "alpha", "beta"])
        rows = analysis.collocates(self.corpus, query="harbor", context=2, stopwords="none", min_raw=2)
        self.assertEqual([r.context_term for r in rows], ["five"])

    def test_english_stoplist_filters_context_words(self) -> None:
        corpus = corpus_from(("d", "the harbor and the ship"))
        self.assertEqual(
            [(r.context_term, r.context_raw_freq) for r in analysis.collocates(corpus, query="harbor", context=3, stopwords="en")],
            [("ship", 1)],
        )
        self.assertEqual(
            [(r.context_term, r.context_raw_freq) for r in analysis.collocates(corpus, query="harbor", context=3, stopwords="none")],
            [("the", 2), ("and", 1), ("ship", 1)],
        )

    def test_other_keyword_occurrences_are_not_counted_as_collocates(self) -> None:
        corpus = corpus_from(("d", "harbor harbor ship"))
        rows = analysis.collocates(corpus, query="harbor", context=2, stopwords="none")
        self.assertEqual([(r.context_term, r.context_raw_freq) for r in rows], [("ship", 2)])

    def test_query_matches_exactly_not_as_a_prefix(self) -> None:
        self.assertEqual(analysis.collocates(self.corpus, query="har*", context=2, stopwords="none"), [])


class PhrasesTests(unittest.TestCase):
    def setUp(self) -> None:
        # doc1 bigrams: big red x2, red fox x2, fox big x1; doc2: big red x1, red fox x1
        # trigram "big red fox": doc1 x2, doc2 x1. Four-grams occur once each and fall below min_raw.
        self.corpus = corpus_from(("doc1", "big red fox big red fox"), ("doc2", "big red fox"))

    def test_longer_phrase_shadows_shorter_phrases_with_the_same_count(self) -> None:
        rows = analysis.phrases(self.corpus, min_length=2, max_length=3, min_raw=2, stopwords="none")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row.phrase, row.length, row.raw_freq, row.distribution), ("big red fox", 3, 3, [2, 1]))

    def test_trigram_is_kept_when_four_grams_are_allowed(self) -> None:
        # Regression: a trigram used to shadow itself whenever max_length > 3, so the CLI defaults
        # (2..4) never reported a trigram.
        rows = analysis.phrases(self.corpus, min_length=2, max_length=4, min_raw=2, stopwords="none")
        self.assertEqual([(r.phrase, r.raw_freq) for r in rows], [("big red fox", 3)])

    def test_bigrams_only(self) -> None:
        rows = analysis.phrases(self.corpus, min_length=2, max_length=2, min_raw=2, stopwords="none")
        self.assertEqual(
            [(r.phrase, r.raw_freq, r.distribution) for r in rows],
            [("big red", 3, [2, 1]), ("red fox", 3, [2, 1])],
        )

    def test_phrases_made_only_of_stopwords_are_skipped(self) -> None:
        corpus = corpus_from(("d", "the and the and the"))
        self.assertEqual(analysis.phrases(corpus, min_length=2, max_length=2, min_raw=2, stopwords="en"), [])


class CorrelationTests(unittest.TestCase):
    # Four documents of 20 tokens each. Per-document counts of each term:
    #   alpha 1,2,3,4   twin 2,4,6,8 (r = +1 with alpha)   anti 4,3,2,1 (r = -1)
    #   beta 2,4,5,4    const 1,1,1,1 (no variance)        solo only in document 1
    def setUp(self) -> None:
        self.corpus = corpus_from(
            ("d1", bag({"alpha": 1, "beta": 2, "twin": 2, "anti": 4, "const": 1, "solo": 1, "pad": 9})),
            ("d2", bag({"alpha": 2, "beta": 4, "twin": 4, "anti": 3, "const": 1, "pad": 6})),
            ("d3", bag({"alpha": 3, "beta": 5, "twin": 6, "anti": 2, "const": 1, "pad": 3})),
            ("d4", bag({"alpha": 4, "beta": 4, "twin": 8, "anti": 1, "const": 1, "pad": 2})),
        )

    def test_pearson_r_for_constructed_term_pairs(self) -> None:
        result = analysis.correlations(self.corpus, query="alpha", stopwords="none")
        self.assertTrue(all(row.term1 == "alpha" for row in result.terms))
        scores = {row.term2: row.correlation for row in result.terms}
        self.assertAlmostEqual(scores["twin"], 1.0)
        self.assertAlmostEqual(scores["anti"], -1.0)
        # beta: sum((x - 2.5)(y - 3.75)) = 3.5, sum((x - 2.5)^2) = 5, sum((y - 3.75)^2) = 4.75
        self.assertAlmostEqual(scores["beta"], 3.5 / math.sqrt(5 * 4.75))

    def test_strongest_correlations_come_first(self) -> None:
        result = analysis.correlations(self.corpus, query="alpha", stopwords="none")
        magnitudes = [abs(row.correlation) for row in result.terms]
        self.assertEqual(magnitudes, sorted(magnitudes, reverse=True))
        self.assertEqual({row.term2 for row in result.terms[:2]}, {"twin", "anti"})

    def test_constant_and_single_document_terms_are_not_correlated(self) -> None:
        result = analysis.correlations(self.corpus, query="alpha", stopwords="none")
        partners = {row.term2 for row in result.terms}
        self.assertNotIn("const", partners)  # zero variance
        self.assertNotIn("solo", partners)  # occurs in fewer than min_docs documents

    def test_document_correlation_identical_profiles(self) -> None:
        corpus = corpus_from(("x", "alpha beta beta gamma"), ("y", "alpha alpha beta beta beta beta gamma gamma"))
        rows = analysis.correlations(corpus, stopwords="none").documents
        self.assertEqual([(r.index1, r.doc1, r.index2, r.doc2) for r in rows], [(0, "x", 1, "y")])
        self.assertAlmostEqual(rows[0].correlation, 1.0)

    def test_document_correlation_opposite_profiles(self) -> None:
        corpus = corpus_from(("x", "alpha alpha alpha beta"), ("y", "alpha beta beta beta"))
        rows = analysis.correlations(corpus, stopwords="none").documents
        self.assertAlmostEqual(rows[0].correlation, -1.0)


class SegmentCorrelationTests(unittest.TestCase):
    def setUp(self) -> None:
        # 8 tokens in 4 segments of 2: alpha 2,0,1,0 -> 1, 0, .5, 0 ; beta 0,1,0,1 -> 0, .5, 0, .5
        self.corpus = corpus_from(("d", "alpha alpha beta pad alpha pad pad beta"))

    def test_pearson_across_segments(self) -> None:
        rows = analysis.segment_correlations(self.corpus, query="alpha,beta", segments=4)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((row.index, row.title, row.term1, row.term2, row.segments), (0, "d", "alpha", "beta", 4))
        # cov = -0.375, var_alpha = 11/16, var_beta = 1/4  ->  r = -3 / sqrt(11)
        self.assertAlmostEqual(row.correlation, -3 / math.sqrt(11))

    def test_zero_variance_gives_none(self) -> None:
        rows = analysis.segment_correlations(self.corpus, query="alpha,zzz", segments=4)
        self.assertIsNone(rows[0].correlation)

    def test_needs_two_terms_and_two_segments(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least two query terms"):
            analysis.segment_correlations(self.corpus, query="alpha", segments=4)
        with self.assertRaisesRegex(ValueError, "at least two segments"):
            analysis.segment_correlations(self.corpus, query="alpha,beta", segments=1)


class FrequenciesTests(unittest.TestCase):
    def test_raw_relative_and_per_document_counts(self) -> None:
        rows = analysis.frequencies(counts_corpus(), query="cat,sat")
        cat = rows[0]
        self.assertEqual((cat.term, cat.raw_freq), ("cat", 2))
        self.assertAlmostEqual(cat.relative_freq, 2 / 9)
        self.assertAlmostEqual(cat.ppm, 2 / 9 * 1_000_000)
        self.assertEqual([(d.title, d.raw_freq) for d in cat.documents], [("a", 2), ("b", 0)])
        self.assertAlmostEqual(cat.documents[0].relative_freq, 2 / 6)
        sat = rows[1]
        self.assertEqual(sat.raw_freq, 2)
        self.assertEqual([d.raw_freq for d in sat.documents], [1, 1])

    def test_query_matches_exactly_not_as_a_prefix(self) -> None:
        rows = analysis.frequencies(counts_corpus(), query="ca*")
        self.assertEqual((rows[0].term, rows[0].raw_freq), ("ca*", 0))


if __name__ == "__main__":
    unittest.main()
