# Skills for AI assistants

Two Agent Skills that teach AI coding assistants such as Claude Code how to use this tool. Once installed, a request in plain words, such as "show the most frequent words in this folder", lets the assistant pick the right command and answer with numbers and source contexts.

| Skill | What it does |
|---|---|
| `voyant-corpus-prep` | Turns PDF, DOCX, HWPX, and CP949 text into a UTF-8 .txt corpus folder |
| `voyant-analysis` | Runs the voyant command that fits a question, reports numbers with contexts, and handles Korean particles |

## Installing

Any assistant that reads `AGENTS.md` or `CLAUDE.md` at the repository root is already told to run the CLI through these skills, so opening the repository is enough for a request like "read the skills and analyze this file".

Claude Code finds them through the links in `.claude/skills/`, which point at this folder, as soon as the repository is open. On Windows, where a clone may not create the links, copy the two folders into `.claude/skills/` instead.

To use them in every project, install the command and link the skills into your home folder:

```sh
python3 -m pip install -e .
ln -s "$PWD/skills/voyant-corpus-prep" "$PWD/skills/voyant-analysis" ~/.claude/skills/
```

With the `voyant` command installed, the assistant does not need to know where the repository is.

For other assistants that support skill folders, put the same two folders in that assistant's skills directory. For an assistant without skill support, start the conversation with "Read `skills/voyant-analysis/SKILL.md` first and follow it."

The skills tell the assistant to run commands and report their output, not to read your text and count for itself. If an assistant answers without showing a `voyant` command, ask it to rerun the analysis with the CLI.

## Example requests

```text
Turn the three PDFs in docs/readings into a corpus voyant can analyze.
Name each document after its author.
```

```text
List the 20 most frequent words in corpus/essays and show
the sentences where the top three are used.
```

```text
How differently does "freedom" appear at the beginning and the end of the text?
Show the trend over 10 segments.
```

```text
Among these five authors' essays, which two are most alike and which differ most?
Include the correlation evidence and the limits of that judgment.
```

```text
Build the HTML view for corpus/interviews. The text is sensitive,
so do not read it; just write the file and tell me the path.
```

## Notes

- voyant commands run only on your computer. When an assistant reads the results or the source text, that content goes to the assistant's model provider. For text that must not leave your machine, have the assistant only build the HTML, as in the last example, and open it yourself.
- Korean is counted by spaces, so `항구는` and `항구를` are different words. The `voyant-analysis` skill tells the assistant to combine forms, but check the result table yourself.
- When citing results, keep the commands the assistant showed you next to them so anyone can reproduce them.
