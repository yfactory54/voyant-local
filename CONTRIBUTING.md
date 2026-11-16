# Contributing

Bug reports, fixes, and small focused features are welcome. For larger
changes, open an issue first so the approach can be agreed before you
write the code.

## Ground rules

- **Standard library only.** voyant has no third-party runtime
  dependencies. Keep it that way.
- **Python 3.10 or newer.** Do not use syntax or library features that
  3.10 lacks (for example `except*`, `tomllib`, or `typing.Self`).
- **Write from definitions, not from Voyant source.** The analysis code
  follows published statistical definitions. Do not copy code from
  Voyant, VoyantServer, or Trombone into this repository. If a change
  needs material from those projects, say so in the pull request so
  `NOTICE` can be updated.
- **Leave `voyant/stopwords.py` verbatim.** It is Trombone's English
  stoplist. Changes to the list belong upstream.
- **Keep `view` offline.** The generated HTML must not fetch anything
  from the network.

## Checking a change

Run the test suite from the repository root. It uses only the
standard-library `unittest` module, and CI runs it on Linux, macOS, and
Windows for Python 3.10 through 3.13:

```sh
python3 -m unittest discover -s tests -t .
```

Then run the commands from the README against `samples/` and confirm
each exits with status 0:

```sh
python3 -m voyant summary samples/
python3 -m voyant terms samples/ --limit 15
python3 -m voyant contexts samples/ --query voyage --context 5
python3 -m voyant collocates samples/ --query voyage
python3 -m voyant phrases samples/
python3 -m voyant correlations samples/ --query voyage
python3 -m voyant trends samples/ --query voyage,harbor --segments 12
python3 -m voyant segment-correlations samples/ --query voyage,harbor --segments 12
python3 -m voyant view samples/ --output view.html
```

If you change a statistic, show the expected value in the pull request
and how you derived it. If you change `view`, open the generated file
in a browser in both light and dark mode.

Add or update tests in `tests/` for any behavior you change.

## Pull requests

- One logical change per pull request.
- Describe what changed and why. Update the README when command-line
  behavior changes.
- Follow the existing style: 4-space indentation, type hints, and
  docstrings on public functions.

## License

By contributing, you agree that your contribution is licensed under
GPL-3.0-or-later, the same license as the project. See `LICENSE`.
