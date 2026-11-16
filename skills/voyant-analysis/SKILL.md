---
name: voyant-analysis
description: Run the voyant command-line tool on a local text file or folder (manuscripts, articles, interview transcripts, fiction) and report term frequencies, keyword-in-context lines, collocates, segment trends, and correlations from its output. Always runs the CLI; never reads, counts, or summarizes the text directly. Use whenever the user asks to analyze a text file or folder, including requests such as "voyant", "text analysis", "word frequency", "most common words", "word cloud", "KWIC", "collocates", "trends", "correlation", "corpus analysis", or their Korean equivalents ("텍스트 분석", "단어 빈도", "자주 나오는 단어", "워드클라우드", "문맥", "공기어", "트렌드", "상관관계").
---

# Voyant text analysis

Answer the user's question about a text file or folder by running `python3 -m voyant` and reporting what it prints. The tool uses only the Python standard library and makes no network requests.

## How this skill works

This skill is a procedure for running a command-line tool. The analysis is done by the tool, not by you.

- Your first action on the user's text is `python3 -m voyant summary <path>`. Run it before anything else.
- Do not open the text being analyzed with a file-reading tool, `cat`, `head`, or an editor. To see how a word is used, run `contexts`.
- Do not write your own script or one-liner to count, tokenize, or compare. If no command answers the question, say so and offer the closest command.
- If a command fails, read the error, fix the path or option, and run it again. Report the error if you cannot fix it. Do not fall back to reading the text and analyzing it yourself.
- Read the source text only when the user explicitly asks for the original wording of a passage, and then only that passage.

## Rules

- Take every number from command output. Do not estimate or re-round. Report the command you ran so the user can run it again.
- Do not conclude meaning from a frequency or a correlation alone. Check the actual sentences with `contexts` before interpreting, and mark interpretations as hypotheses.
- Do not upload the text to web Voyant or any other external service. The tool runs locally, but whatever output or source text you read is sent to your model provider. If the user says the text is sensitive, tell them so and let them open the HTML from `view` themselves.

## Getting started

1. Find a way to run the tool, in this order, and use the first that works. Python 3.10 or newer is required.
   - `voyant --help` succeeds: the tool is installed. Use `voyant <command> ...` wherever this skill writes `python3 -m voyant <command> ...`.
   - The current directory has a `voyant/` folder with `cli.py`: run `python3 -m voyant ...` from here.
   - Otherwise find the repository. This `SKILL.md` normally sits at `<repo>/skills/voyant-analysis/SKILL.md`, possibly through a symlink, so resolve its real path and go up two levels. Then run `PYTHONPATH=<repo> python3 -m voyant ...`, or install once with `python3 -m pip install -e <repo>`.
   - If none of these works, ask the user for the repository path. Do not analyze the text another way.
2. The input is any mix of files and folders; each file is one document. A single file works: `python3 -m voyant summary notes/essay.txt`. Folders are read for `.txt`, `.md`, and `.text` only. If the input includes PDF, DOCX, HWP, or CP949-encoded text, prepare it first with the `voyant-corpus-prep` skill.
3. Always start with `summary` to see the document and token counts. Those numbers set the scale for every later interpretation.

```sh
python3 -m voyant summary corpus/
python3 -m voyant documents corpus/
```

In the commands below, `corpus/` stands for whatever files or folders the user gave you.

If the user only says "analyze this" without a question, run `summary`, `documents`, `terms --limit 30`, and `phrases`, then `contexts` for the top three content words, and report those.

## Questions and commands

| The user asks | Command |
|---|---|
| Which words are most frequent | `terms corpus/ --limit 30` |
| Which words characterize each document | `document-terms corpus/ --limit 20` (tf-idf, z-score) |
| How a word is used in sentences | `contexts corpus/ --query word --context 6` |
| Which words appear near a word | `collocates corpus/ --query word --context 5` |
| Which expressions repeat | `phrases corpus/ --min-length 2 --max-length 4` |
| How a word changes from beginning to end | `trends corpus/ --query word1,word2 --segments 10` |
| Counts and rates per document | `frequencies corpus/ --query word1,word2` |
| Words that rise and fall together, similar documents | `correlations corpus/ --query word` |
| Whether two words move together inside one document | `segment-correlations corpus/ --query word1,word2 --segments 10` |
| Explore interactively | `view corpus/ --output result.html` |

Options and output columns are in `references/commands.md`. Read `references/interpreting.md` before interpreting numbers.

## Korean text

Tokens are split on spaces and punctuation. There is no morphological analysis, so particles and endings stay attached: `항구는`, `항구를`, and `항구의` are three different words.

1. Find the forms that share a stem. `*` works as a prefix only in the `--query` of `terms`, `document-terms`, and `correlations`.

   ```sh
   python3 -m voyant terms corpus/ --query '항구*' --limit 50
   ```

2. Pass the forms you found, comma-separated, to the exact-match commands. `contexts`, `collocates`, `frequencies`, and `trends` do not support `*`.

   ```sh
   python3 -m voyant contexts corpus/ --query 항구는,항구를,항구의 --context 6
   ```

3. If a total is needed, add the `raw_freq` of each form and say in the report that you did.

The stoplist is English only. In Korean text, function words such as `것`, `수`, `등`, and `있다` stay at the top. Say that you excluded them from the report and skip them.

## Report format

1. Question: what the user wants to know, in one line
2. Commands: a code block
3. Key numbers: a small table (term, count, relative frequency or per-million figure, document distribution)
4. Evidence: two or three lines from `contexts` output
5. Reading: what the numbers and the contexts point to together, stated as a hypothesis
6. Limits: conditions that affected this result, such as corpus size, attached particles, or the stoplist

When results are written up, include the commands and options used so that others can reproduce them.
