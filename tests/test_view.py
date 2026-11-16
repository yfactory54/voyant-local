"""The offline HTML view: file layout, no remote loads, escaping, and the embedded payload."""

from __future__ import annotations

import html
import json
import re
import tempfile
import unittest
from pathlib import Path

from voyant.corpus import load_paths
from voyant.view import build_view, write_view

from tests.support import FONT_FILES, REPO_ROOT, SAMPLES, corpus_from

FONT_SOURCE = REPO_ROOT / "voyant" / "fonts"

# A load of a stylesheet, script, image, or font from a remote host: attribute or CSS url() with http(s)://
# or protocol-relative //, or an @import rule.
REMOTE_LOAD = re.compile(
    r"""\b(?:src|href)\s*=\s*["']?\s*(?:https?:)?//|url\(\s*["']?\s*(?:https?:)?//|@import""",
    re.IGNORECASE,
)
DATA_BLOCK = re.compile(r'<script id="data" type="application/json">(.*?)</script>', re.DOTALL)


class ViewFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.corpus = load_paths([str(SAMPLES)])

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_writes_html_and_copies_fonts_beside_it(self) -> None:
        out = write_view(self.corpus, str(self.dir / "reading" / "view.html"))
        self.assertEqual(out, self.dir / "reading" / "view.html")
        self.assertTrue(out.is_file())
        fonts = self.dir / "reading" / "fonts"
        for name in (*FONT_FILES, "OFL.txt"):
            with self.subTest(name=name):
                self.assertEqual((fonts / name).read_bytes(), (FONT_SOURCE / name).read_bytes())

    def test_html_references_fonts_relatively(self) -> None:
        out = write_view(self.corpus, str(self.dir / "view.html"))
        page = out.read_text(encoding="utf-8")
        self.assertIn('src:url("fonts/source-serif-4-500.woff2")', page)
        self.assertIn('src:url("fonts/source-sans-3-400.woff2")', page)

    def test_no_remote_resource_loads(self) -> None:
        page = write_view(self.corpus, str(self.dir / "view.html")).read_text(encoding="utf-8")
        self.assertEqual(REMOTE_LOAD.findall(page), [])
        self.assertNotIn("<link", page.lower())
        # The only http(s) URL left in the page is the SVG namespace identifier in the script, which is not fetched.
        self.assertEqual(set(re.findall(r"https?://[^\s\"'<>)]+", page)), {"http://www.w3.org/2000/svg"})

    def test_title_is_taken_from_the_output_name_and_escaped(self) -> None:
        page = write_view(self.corpus, str(self.dir / "Tom & Jerry.html")).read_text(encoding="utf-8")
        self.assertIn("<title>Tom &amp; Jerry</title>", page)
        self.assertIn("<h1>Tom &amp; Jerry</h1>", page)


class ViewEscapingTests(unittest.TestCase):
    def test_script_in_document_text_is_escaped_and_round_trips(self) -> None:
        text = 'Tom said <script>alert("pwned")</script> then </script><img src=x onerror=alert(1)> harbor'
        corpus = corpus_from(("evil", text))
        with tempfile.TemporaryDirectory() as tmp:
            page = write_view(corpus, str(Path(tmp) / "view.html")).read_text(encoding="utf-8")
        self.assertEqual(page.count("</script>"), 2)  # one closes the data block, one closes the viewer script
        self.assertEqual(page.count("<script"), 2)
        self.assertNotIn('<script>alert("pwned")', page)
        self.assertNotIn("<img src=x", page)
        match = DATA_BLOCK.search(page)
        self.assertIsNotNone(match)
        payload = json.loads(match.group(1))
        self.assertEqual(payload["documents"][0]["text"], text)
        self.assertEqual(html.unescape("&lt;script&gt;"), "<script>")


class ViewPayloadTests(unittest.TestCase):
    def test_vocabulary_and_stop_flags(self) -> None:
        payload = build_view(corpus_from(("d", "the cat sat the")), stopwords="en")
        self.assertEqual(payload["vocab"], ["the", "cat", "sat"])  # by count, then alphabetically
        self.assertEqual(payload["stop"], [1, 0, 0])
        self.assertEqual(payload["terms"], ["cat", "sat"])
        self.assertEqual(payload["documents"][0]["ids"], [0, 1, 2, 0])
        self.assertEqual(payload["summary"]["tokens"], 4)
        self.assertEqual(payload["settings"], {"segments": 12, "window": 5, "stopwords": "en"})

    def test_offsets_are_utf16_units_for_javascript(self) -> None:
        # The emoji is one code point but two UTF-16 units, so "harbor" starts at unit 3, not 2.
        text = "\U0001F600 harbor"
        payload = build_view(corpus_from(("emoji", text)))
        start, end = payload["documents"][0]["offsets"]
        self.assertEqual((start, end), (3, 9))
        self.assertEqual(text.encode("utf-16-le")[start * 2 : end * 2].decode("utf-16-le"), "harbor")

    def test_invalid_settings_are_rejected(self) -> None:
        corpus = corpus_from(("d", "one two"))
        with self.assertRaisesRegex(ValueError, "at least two segments"):
            build_view(corpus, segments=1)
        with self.assertRaisesRegex(ValueError, "at least one token"):
            build_view(corpus, window=0)

    def test_invalid_settings_write_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "view.html"
            with self.assertRaises(ValueError):
                write_view(corpus_from(("d", "one two")), str(target), segments=1)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
