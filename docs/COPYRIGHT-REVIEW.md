# Copyright review

Reviewed 2026-11-05 against the upstream repositories and the files in
this tree. This is an engineering attribution record, not a legal opinion.

## Verdict

The program can be published. It is an independent reimplementation,
released under GPL-3.0-or-later because it includes one verbatim file
from Trombone. The bundled fonts stay under the SIL Open Font License
1.1 and are not covered by `LICENSE`.

Do not describe this project as Voyant Tools, an official port, or an
affiliated release. Cite Sinclair and Rockwell for Voyant Tools itself.

## Upstream

| work | current license evidence | use here |
|---|---|---|
| [Voyant](https://github.com/voyanttools/Voyant) | GitHub reports SPDX `GPL-3.0` for `LICENSE.txt` | not copied |
| [VoyantServer](https://github.com/voyanttools/VoyantServer) | GitHub reports SPDX `GPL-3.0` for `license-GPL3.txt` | not copied |
| [trombone](https://github.com/voyanttools/trombone) | GitHub reports SPDX `GPL-3.0`; README says GPLv3 | one verbatim stoplist |
| [Source Serif](https://github.com/adobe-fonts/source-serif) | OFL 1.1, Reserved Font Name "Source" | two unmodified WOFF2 files |
| [Source Sans](https://github.com/adobe-fonts/source-sans) | OFL 1.1, Reserved Font Name "Source" | two unmodified WOFF2 files |

GPL-3.0 permits verbatim and modified redistribution when copyright and
license notices are preserved and the whole program is offered under
GPL-3.0-or-later. That condition is why this repository cannot switch to
a permissive license while `voyant/stopwords.py` contains the Trombone
list.

## What was copied

`voyant/stopwords.py` is the word list from
`src/main/resources/org/voyanttools/trombone/stopwords/stop.en.txt`.
Its own header points to the TAPoRware Glasgow stoplist. Trombone's
copyright notice for the project names Stéfan Sinclair and Geoffrey
Rockwell, 2007-2012. The list is kept under GPL-3.0-or-later and is
identified in `NOTICE`.

Checked against upstream on 2026-11-05. The list is stored as a Python
set, so the original order and any repeated entry are not preserved.
One upstream entry, `#`, had been dropped and was restored before
publication. The words themselves otherwise match.

No Java source, JavaScript, HTML, CSS, icon, or documentation from
Voyant, VoyantServer, or Trombone is included. Relative frequency,
z-score, tf-idf, and Pearson correlation are calculated from their
published definitions.

## Fonts

The four files in `voyant/fonts/` are unmodified WOFF2 builds:

- Source Serif 4, weights 500 and 600, Copyright 2014-2023 Adobe
- Source Sans 3, weights 400 and 600, Copyright 2010-2024 Adobe

OFL 1.1 allows bundling them with software if the copyright notice and
full license travel with the files, the fonts are not sold alone, and
the Reserved Font Name "Source" is not reused for a modified font. The
license text is `voyant/fonts/OFL.txt`. OFL and GPL are incompatible, so
these files are not relicensed by the repository `LICENSE`. `voyant view`
copies `OFL.txt` into the `fonts/` directory beside every generated HTML
file. That HTML is an ordinary document and is not placed under the OFL
merely because it uses the fonts.

## Names

"Voyant" and "Voyant Tools" identify the original project. "Source" is
Adobe's Reserved Font Name and trademark. This repository uses those
names only to say what it reimplements and which fonts it bundles. It
does not claim endorsement.

## Kept out of the public tree

- `voyant-view.html` is generated output. It is not committed.
- `__pycache__/`, `.DS_Store`, and editor files are ignored.
- `samples/` was written for this repository. It contains no personal
  data and no text copied from Voyant's examples.

## Before pushing

1. Confirm GitHub shows `GPL-3.0-or-later` from `LICENSE`.
2. Keep `NOTICE`, `voyant/fonts/OFL.txt`, and the font files in the same
   commit as the code.
3. Do not add proprietary course readings to `samples/` without a
   separate right to redistribute them.
4. If the stoplist is replaced with an independently licensed list, the
   GPL choice can be reconsidered. Until then it stays.
