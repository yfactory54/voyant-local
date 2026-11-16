# Instructions for AI agents

This repository is a command-line text analysis tool. When a user asks you to analyze, count, compare, or summarize the words in a text file or folder, you run the tool. You do not do the analysis yourself.

## Analysis requests

1. Read `skills/voyant-analysis/SKILL.md` and follow it. If the input is not plain UTF-8 text (PDF, DOCX, HWPX, CP949), read `skills/voyant-corpus-prep/SKILL.md` first.
2. Your first action on the user's text is a command, not a file read:

   ```sh
   python3 -m voyant summary <file or folder>
   ```

3. Every number and every quoted passage in your answer comes from the output of a `python3 -m voyant` command that you ran in this session.

Do not open the user's text with a file-reading tool, `cat`, or `head` to analyze it. Do not write your own script to count words. Do not answer from your impression of the text. If a command fails, show the error and fix the invocation; do not fall back to reading the text.

"Read the skills and analyze this file" means: read the two `SKILL.md` files, then run the CLI on that file.

## Working on the code

- Python 3.10 or newer, standard library only. Do not add runtime dependencies.
- Run the tests with `python3 -m unittest discover -s tests -t .`
- `skills/` is the source of the Agent Skills; `.claude/skills/voyant-*`, where present, are symlinks to it. Edit the files under `skills/`.
