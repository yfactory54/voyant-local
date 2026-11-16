---
name: voyant-corpus-prep
description: Turn PDF, DOCX, HWPX, HWP, CP949-encoded text, or pasted writing into a folder of UTF-8 .txt files that voyant reads, by running the bundled converter script rather than extracting text by hand. Splits material so one file is one document, fixes the encoding, and removes noise such as running headers and page numbers. Use for requests such as "build a corpus", "convert to text files", "analyze these PDFs", "Hangul/hwp file", "docx", "the characters are garbled", "get this ready for voyant", their Korean equivalents ("코퍼스 만들기", "텍스트 파일로 바꿔줘", "한글 파일", "글자가 깨져"), or before voyant-analysis when the input is not plain text.
---

# Voyant corpus preparation

voyant reads only `.txt`, `.md`, and `.text` files in a folder, and counts each file as one document. This skill puts the user's material into that shape. It never modifies the source files; it writes to a new folder.

## 1. Decide the unit

The unit of comparison is the unit of files. Take it from the user's request; do not stop to ask.

- Default: one .txt per source file. Use this whenever the request does not say otherwise, and state the assumption in your report.
- The user wants to compare by author, speaker, or year: one file per unit
- The user wants the flow of chapters in one work: one file per chapter, or a single file with `trends --segments`

File names appear as document titles in every result. Use short names that sort well, such as `01-departure.txt` or `2023-kim.txt`. Documents in a folder are ordered by path.

## 2. Convert

```sh
python3 skills/voyant-corpus-prep/scripts/to_corpus.py <files or folders...> --output corpus/<project>
```

The script is in the `scripts/` folder beside this `SKILL.md`; outside the repository root, call it by that path. It uses only the Python standard library. Convert with this script. Do not read a PDF or DOCX yourself and retype or paste its text into a file.

| Input | Handling |
|---|---|
| `.txt`, `.md`, `.text` | Read as UTF-8 or CP949, saved as UTF-8 |
| `.docx` | Body paragraphs extracted in order |
| `.hwpx` | Paragraphs extracted section by section; paragraphs inside a table follow the paragraph that holds the table |
| `.pdf` | Extracted with an installed `pdftotext` (poppler); skipped if it is missing |
| `.hwp` | Not readable. Ask the user to use Save As in Hangul to make `.hwpx` or `.txt` |

`skip` lines in the output name each failed file and the reason. If any file is skipped, the exit status is 1. Tell the user which files were skipped and how to fix them. A scanned image PDF has no text and produces an empty result; tell the user it needs OCR.

On macOS, convert `.doc`, `.rtf`, and `.pages` with `textutil -convert txt <file>` first. For web pages or chat logs, have the user copy the body text into a .txt file.

## 3. Remove noise

Find repeated elements that would distort the analysis from command output, not by reading the converted files.

```sh
python3 -m voyant terms corpus/<project> --limit 30
python3 -m voyant phrases corpus/<project> --min-length 2 --max-length 6 --limit 30
```

A phrase whose count is close to the page count, or a top term that is a name or a title, is usually one of these:

- Headers, footers, page numbers, and institution names repeated on every page
- Words broken across PDF line ends (`analy-` / `sis`): they split one word's count in two
- References, tables of contents, appendices: drop them if the question does not need them
- Speaker labels in interview transcripts (`Interviewer:`): the speaker's name becomes the most frequent word

Confirm a suspect with `contexts --query <term>`. Report what you found and the command that showed it. Remove it only if the user agrees, with a search-and-replace on the exact repeated line in the corpus folder, never in the source files. Keep a note of what was removed and mention it in the limits section of the analysis report.

## 4. Check

```sh
python3 -m voyant summary corpus/<project>
python3 -m voyant documents corpus/<project>
```

Check that the document count matches expectations, that no document has 0 tokens, and that titles are as intended. If garbled characters (Latin combinations such as `ì` or `ê`) appear near the top of `terms --limit 20`, the encoding was misread; convert that file again.

Then continue with the `voyant-analysis` skill.
