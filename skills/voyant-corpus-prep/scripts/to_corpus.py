"""Convert documents into a folder of UTF-8 .txt files that voyant reads.

    python3 to_corpus.py <file or folder>... --output corpus/
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

SUPPORTED = {".txt", ".md", ".text", ".docx", ".hwpx", ".pdf", ".hwp"}
SPACERS = {"tab", "br", "lineBreak"}


def decode(raw: bytes) -> str:
    # Korean Windows tools still save plain text as CP949; voyant itself would misread it as Latin-1.
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("neither UTF-8 nor CP949; save the file again as UTF-8")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _collect(node: ElementTree.Element, out: list[str]) -> str:
    # Returns the text a paragraph owns and appends nested paragraphs (HWPX table cells) after it, in reading order.
    own: list[str] = []
    for child in node:
        name = _local(child.tag)
        if name == "p":
            slot = len(out)
            out.append("")
            out[slot] = _collect(child, out)
        elif name == "t":
            own.append(child.text or "")
            for inner in child:
                own.append(" " if _local(inner.tag) in SPACERS else "")
                own.append(inner.tail or "")
        elif name in SPACERS:
            own.append(" ")
        else:
            own.append(_collect(child, out))
    return "".join(own)


def xml_text(data: bytes) -> list[str]:
    lines: list[str] = []
    _collect(ElementTree.fromstring(data), lines)
    return lines


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return "\n".join(xml_text(archive.read("word/document.xml")))


def hwpx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        sections = [name for name in archive.namelist() if re.fullmatch(r"Contents/section\d+\.xml", name)]
        sections.sort(key=lambda name: int(re.sub(r"\D", "", name)))
        return "\n".join(line for name in sections for line in xml_text(archive.read(name)))


def pdf_text(path: Path) -> str:
    tool = shutil.which("pdftotext")
    if tool is None:
        raise ValueError("pdftotext is not installed (poppler); install it or export the PDF as text")
    result = subprocess.run([tool, "-enc", "UTF-8", str(path), "-"], capture_output=True, check=False)
    if result.returncode != 0:
        raise ValueError(result.stderr.decode("utf-8", errors="replace").strip() or "pdftotext failed")
    return result.stdout.decode("utf-8")


def extract(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".text"}:
        return decode(path.read_bytes())
    if suffix == ".docx":
        return docx_text(path)
    if suffix == ".hwpx":
        return hwpx_text(path)
    if suffix == ".pdf":
        return pdf_text(path)
    raise ValueError("binary .hwp is not readable; in Hangul use Save As .hwpx or .txt")


def tidy(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def sources(paths: list[str], output: Path) -> tuple[list[Path], int]:
    found: list[Path] = []
    missing = 0
    for raw in paths:
        path = Path(raw).expanduser()
        if path.is_dir():
            found.extend(
                sorted(
                    p
                    for p in path.rglob("*")
                    if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in SUPPORTED and output not in p.parents
                )
            )
        elif path.is_file():
            found.append(path)
        else:
            print(f"skip  {path}: no such file or directory")
            missing += 1
    return found, missing


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert .txt/.md/.docx/.hwpx/.pdf files into a UTF-8 .txt corpus for voyant.")
    parser.add_argument("paths", nargs="+", help="files or folders to convert")
    parser.add_argument("--output", required=True, help="corpus folder to write")
    args = parser.parse_args(argv)
    output = Path(args.output).expanduser().resolve()
    files, failed = sources(list(args.paths), output)
    output.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    written = 0
    for path in files:
        try:
            text = tidy(extract(path))
        except (ValueError, OSError, zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
            print(f"skip  {path}: {exc}")
            failed += 1
            continue
        stem, number = path.stem, 2
        while stem.lower() in used:
            stem, number = f"{path.stem}-{number}", number + 1
        used.add(stem.lower())
        target = output / f"{stem}.txt"
        target.write_text(text, encoding="utf-8")
        print(f"ok    {path} -> {target} ({len(text):,} characters)")
        written += 1
    print(f"{written} written, {failed} skipped")
    return 1 if failed or not written else 0


if __name__ == "__main__":
    sys.exit(main())
