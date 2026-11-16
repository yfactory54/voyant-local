<div align="center">

# voyant

[![CI](https://github.com/yfactory54/voyant-local/actions/workflows/ci.yml/badge.svg)](https://github.com/yfactory54/voyant-local/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)
[![License: GPL-3.0-or-later](https://img.shields.io/badge/license-GPL--3.0--or--later-blue)](LICENSE)

Core [Voyant Tools](https://voyant-tools.org) text analyses, run locally from the command line.<br>
No Java runtime, no server, no third-party packages: just Python and your text files.

[Overview](#overview) • [Getting started](#getting-started) • [Commands](#commands) • [Offline HTML view](#offline-html-view) • [AI assistants](#using-it-through-an-ai-assistant) • [Statistics](#statistics)

</div>

## Overview

`voyant` is a Python reimplementation of the core analyses in Voyant Tools: term frequencies, keyword in context, collocates, phrases, trends, and correlations. It reads `.txt`, `.md`, and `.text` files with the standard library only, prints plain tables or JSON, and can write a single offline HTML page that links all the views together.

The statistical definitions follow Voyant's analysis engine, [trombone](https://github.com/voyanttools/trombone).

> [!NOTE]
> This project is not Voyant Tools and is not affiliated with Stéfan Sinclair, Geoffrey Rockwell, or the Voyant project. Voyant Tools remains the original web application.

### Features

- **Zero dependencies**: Python 3.10 or newer is all you need. Tested on Linux, macOS, and Windows with Python 3.10 to 3.13.
- **Twelve analyses** comparable to Voyant's Summary, Terms, Trends, Contexts, Collocates, Phrases, and Correlations views.
- **Scriptable output**: every command prints a readable table, or JSON with `--json`.
- **Offline reading view**: one self-contained HTML file that never touches the network.
- **AI assistant skills**: ready-made Agent Skills let assistants like Claude Code prepare a corpus and run the right analysis for a plain-language question.

## Getting started

Clone the repository and run the module from its root. There is nothing to install.

```sh
git clone https://github.com/yfactory54/voyant-local.git
cd voyant-local
python3 -m voyant summary samples/
```

```text
documents  tokens  types  longest_title  longest_tokens  shortest_title  shortest_tokens  average_tokens
---------  ------  -----  -------------  --------------  --------------  ---------------  --------------
3          304     137    voyage         118             harbor          93               101.333
```

To run it from any directory as `voyant`, install it from the repository root. This adds no dependencies:

```sh
python3 -m pip install -e .
voyant summary path/to/essay.txt
```

A few more examples using the bundled samples:

```sh
python3 -m voyant terms samples/ --limit 15
python3 -m voyant contexts samples/ --query voyage --context 5
python3 -m voyant collocates samples/ --query voyage
python3 -m voyant phrases samples/
python3 -m voyant correlations samples/ --query voyage
python3 -m voyant trends samples/ --query voyage,harbor --segments 12
python3 -m voyant segment-correlations samples/ --query voyage,harbor --segments 12
python3 -m voyant view samples/ --output view.html
```

Run `python3 -m voyant <command> --help` for every option of a command.

> [!TIP]
> Point any command at your own files or folders. Directories are read for `.txt`, `.md`, and `.text` files only, so a generated HTML file in the same folder is not ingested.

## Commands

| Command | Comparable Voyant view | Reports |
|---|---|---|
| `summary` | Summary | documents, tokens, types, longest and shortest |
| `documents` | Documents | tokens, types, and type/token ratio |
| `terms` | Cirrus, Terms | frequency, relative frequency, document distribution |
| `document-terms` | document terms | frequency, z-score, and tf-idf |
| `frequencies` | Trends counts | raw and relative frequency of selected terms |
| `trends` | Trends | relative frequency across equal segments |
| `contexts` | Contexts | tokens on either side of a hit |
| `collocates` | Collocates | terms inside a fixed token window |
| `phrases` | Phrases | repeated sequences, longer phrases first |
| `correlations` | Correlations | Pearson r between terms or documents |
| `segment-correlations` | Correlations | Pearson r across equal segments |
| `view` | linked reading view | one offline HTML page for the reports above |

### Common options

| Option | Behavior |
|---|---|
| `--json` | Print machine-readable output instead of a table. |
| `--stopwords` | `en` (default, the bundled English stoplist) or `none`. Any other value exits with status 2. |
| `--query` | Comma-separated terms. A trailing `*` works as a prefix on commands that filter a vocabulary. `contexts`, `collocates`, `frequencies`, and `trends` match the listed terms exactly. |
| `--limit`, `--window`, `--min-length`, `--max-length` | Must be at least 1. |
| `--segments` | At least 1 for `trends`; at least 2 for `segment-correlations` and `view`, which correlate across segments. |
| `--context` | May be 0. |

A bad option value exits with status 2 and does not print a traceback.

### JSON document indexes

JSON rows that belong to one document include `index`, counting from 0 in input order. Document pairs from `correlations` carry `index1` and `index2`.

> [!IMPORTANT]
> Titles are display names and are not unique: two files named `report.txt` remain documents 0 and 1. Use `index` to identify documents in scripts.

## Offline HTML view

```sh
python3 -m voyant view samples/ --output view.html
```

`view` writes one HTML file and copies the font files and `OFL.txt` into a `fonts/` directory beside it. Open the HTML directly in a browser; it does not fetch anything from the network.

Every listed term has its distribution, contexts, and co-occurrence. Selecting a segment shows the same token range counted by `trends`.

## Using it through an AI assistant

The [`skills/`](skills/) folder holds two Agent Skills for assistants such as Claude Code:

| Skill | What it does |
|---|---|
| `voyant-corpus-prep` | Turns PDF, DOCX, HWPX, and CP949 text into a UTF-8 corpus folder |
| `voyant-analysis` | Picks the right command for a question and reports the numbers with their contexts |

[`AGENTS.md`](AGENTS.md) tells any assistant opened in this repository to run the CLI through these skills and not to read and count the text itself. Claude Code also finds them through the links in `.claude/skills/` as soon as the repository is open. To use them in every project, install the command and link both folders into `~/.claude/skills/`:

```sh
python3 -m pip install -e .
ln -s "$PWD/skills/voyant-corpus-prep" "$PWD/skills/voyant-analysis" ~/.claude/skills/
```

Then ask in plain words, for example: *"List the 20 most frequent words in corpus/essays and show the sentences where the top three are used."*

> [!WARNING]
> The commands run only on your computer, but when an assistant reads the results or the source text, that content goes to the assistant's model provider. For sensitive text, have the assistant only build the HTML view and open it yourself.

See [`skills/README.md`](skills/README.md) for setup notes and more example requests.

## Statistics

| Measure | Definition |
|---|---|
| relative frequency | count / tokens in the same document, segment, or corpus |
| per-million figure | relative frequency × 1,000,000 |
| z-score | (count − mean type frequency) / standard deviation of type frequencies, per document |
| tf-idf | (count / document tokens) × log10(documents / documents containing the term) |
| correlation | Pearson r of relative frequencies |

## Project layout

```text
voyant/corpus.py       loading and tokenization
voyant/analysis.py     the tools
voyant/cli.py          the command line
voyant/view.py         the offline HTML view
voyant/stopwords.py    bundled English stoplist
voyant/fonts/          SIL OFL font files used by the HTML view
samples/               three short documents written for this project
skills/                Agent Skills for AI assistants that run these tools
tests/                 unittest suite
AGENTS.md              instructions for AI assistants opened in this repository
pyproject.toml         packaging; provides the `voyant` command
```

Run the test suite from the repository root:

```sh
python3 -m unittest discover -s tests -t .
```

## Acknowledgments

`voyant/stopwords.py` contains Trombone's English stoplist, converted to a Python set; copyright for that list belongs to Stéfan Sinclair and Geoffrey Rockwell. The other analysis code was written from published statistical definitions and does not copy Voyant or Trombone source.

The files in `voyant/fonts/` remain under the SIL Open Font License 1.1 (see `voyant/fonts/OFL.txt`); the project's GPL license does not relicense them. [`NOTICE`](NOTICE) states the third-party copyrights, and [`docs/COPYRIGHT-REVIEW.md`](docs/COPYRIGHT-REVIEW.md) records the publication check.

When referring to the original project, please cite Voyant Tools itself:

> Sinclair, Stéfan, and Geoffrey Rockwell. *Voyant Tools* (2016), https://voyant-tools.org.
