"""Command line behaviour: JSON output, exit status 2 on bad input, no tracebacks."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from voyant import cli

from tests.support import SAMPLES, run_cli

S = str(SAMPLES)


class CliJsonTests(unittest.TestCase):
    def test_summary_json_is_valid(self) -> None:
        result = run_cli("summary", S, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual((data["documents"], data["tokens"], data["types"]), (3, 304, 137))
        self.assertEqual(data["longest_title"], "voyage")
        self.assertAlmostEqual(data["average_tokens"], 304 / 3, places=5)

    def test_summary_json_in_process(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            status = cli.main(["summary", S, "--json"])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(buffer.getvalue())["documents"], 3)

    def test_documents_json_rows_carry_index_in_input_order(self) -> None:
        rows = json.loads(run_cli("documents", S, "--json").stdout)
        self.assertEqual([row["index"] for row in rows], [0, 1, 2])
        self.assertEqual([row["title"] for row in rows], ["harbor", "market", "voyage"])
        self.assertEqual([row["tokens"] for row in rows], [93, 93, 118])

    def test_duplicate_titles_get_separate_indexes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for folder, text in (("one", "alpha beta"), ("two", "gamma")):
                (Path(tmp) / folder).mkdir()
                (Path(tmp) / folder / "report.txt").write_text(text, encoding="utf-8")
            result = run_cli("documents", tmp, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)
        self.assertEqual([(row["index"], row["title"], row["tokens"]) for row in rows], [(0, "report", 2), (1, "report", 1)])

    def test_trends_json_rows_carry_index(self) -> None:
        rows = json.loads(run_cli("trends", S, "--query", "harbor", "--segments", "4", "--json").stdout)
        self.assertEqual([row["index"] for row in rows], [0, 1, 2])
        self.assertEqual(len(rows[0]["segments"]), 4)


class CliErrorTests(unittest.TestCase):
    def assertBadInput(self, result: subprocess.CompletedProcess, message: str) -> None:
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn(message, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_unknown_stopword_list_exits_2(self) -> None:
        self.assertBadInput(run_cli("summary", S, "--stopwords", "foo"), "error: unknown stopword list: foo")

    def test_limit_zero_exits_2(self) -> None:
        self.assertBadInput(run_cli("terms", S, "--limit", "0"), "error: limit must be at least 1")

    def test_other_bad_values_exit_2_without_traceback(self) -> None:
        cases = [
            (("trends", S, "--query", "voyage", "--segments", "0"), "segments must be at least 1"),
            (("contexts", S, "--query", "voyage", "--context", "-1"), "context must be at least 0"),
            (("phrases", S, "--min-length", "0"), "min_length must be at least 1"),
            (("terms", S, "--limit", "many"), "invalid int value"),
            (("summary", str(Path(S) / "missing.txt")), "no such file or directory"),
            (("segment-correlations", S, "--query", "voyage"), "at least two query terms"),
            (("document-terms", S, "--doc", "9"), "error:"),
        ]
        for args, message in cases:
            with self.subTest(args=args):
                self.assertBadInput(run_cli(*args), message)

    def test_context_zero_is_accepted(self) -> None:
        result = run_cli("contexts", S, "--query", "harbor", "--context", "0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 14)  # harbor occurs 14 times in samples/


class ReadmeContractTests(unittest.TestCase):
    """Command-line behavior the README promises."""

    def test_document_terms_json_rows_carry_index(self) -> None:
        # README: "JSON rows that belong to one document include `index`".
        rows = json.loads(run_cli("document-terms", S, "--json", "--limit", "3").stdout)
        self.assertIn("index", rows[0])

    def test_segment_correlation_rows_carry_index(self) -> None:
        rows = json.loads(run_cli("segment-correlations", S, "--query", "voyage,harbor", "--json").stdout)
        self.assertEqual([row["index"] for row in rows], list(range(len(rows))))

    def test_frequencies_per_document_rows_carry_index(self) -> None:
        rows = json.loads(run_cli("frequencies", S, "--query", "voyage", "--json").stdout)
        self.assertEqual([doc["index"] for doc in rows[0]["documents"]], [0, 1, 2])

    def test_stopwords_other_than_en_or_none_exit_2(self) -> None:
        # README: "`--stopwords` accepts `en` or `none`; any other value exits with status 2."
        for value in ("off", "false", ""):
            with self.subTest(value=value):
                result = run_cli("summary", S, "--stopwords", value)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
