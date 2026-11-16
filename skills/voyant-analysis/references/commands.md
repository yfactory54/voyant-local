# Command reference

Every command has the form `python3 -m voyant <command> <files or folders...> [options]`. When the package is installed, `voyant <command> ...` is the same thing. A single file is a valid input.

Common options:

- `--json`: print JSON instead of a table (not for `view`). Use it when numbers will be recomputed or moved into a table.
- `--stopwords en|none`: the default `en` removes 487 English stopwords. `none` counts everything. Any other value exits with status 2.

A bad value (`--limit 0`, a missing path) prints `error: ...` and exits with status 2. Document `index` counts from 0 in input order; files inside a folder are ordered by path. A `title` is the file name without its extension and can repeat, so use `index` to tell documents apart.

## summary

Size of the whole corpus.

Output: `documents`, `tokens`, `types`, `longest_title`, `longest_tokens`, `shortest_title`, `shortest_tokens`, `average_tokens`

## documents

Length and vocabulary per document.

Output: `index`, `title`, `tokens`, `types`, `type_token_ratio`

## terms

Term frequencies across the corpus; the data behind Cirrus and Terms.

Options: `--query` (comma-separated terms, a trailing `*` is a prefix), `--limit` (default 30), `--min-raw` (default 1)

Output: `term`, `raw_freq`, `relative_freq`, `ppm`, `in_documents`, `distribution` (count per document, in input order)

## document-terms

The terms that stand out in each document.

Options: `--query`, `--limit` (default 30), `--doc N` (one document only)

Output: `index`, `title`, `term`, `raw_freq`, `relative_freq`, `zscore`, `tfidf`

## frequencies

Count and per-document relative frequency of the listed terms.

Options: `--query` (required, exact match)

Output: `term`, `raw_freq`, `relative_freq`, `ppm`, `documents` (`index`, `title`, `raw_freq`, `relative_freq`, `ppm` per document)

## trends

Relative frequency in equal-sized token segments of each document. The table output is a sparkline on one vertical scale shared by all documents.

Options: `--query` (required, exact match), `--segments` (default 10)

JSON output: `index`, `title`, `term`, `raw_freq`, `segments` (`bin`, `raw_freq`, `relative_freq`)

## contexts

Words on either side of a keyword (KWIC). The context is normalized, lowercase tokens without punctuation. For the original wording, point the user to the Contexts panel of `view`; open the source file only if the user asks you to quote a passage exactly.

Options: `--query` (required, exact match), `--context` (tokens on each side, default 5, may be 0), `--limit` (default 30)

JSON output: `index`, `title`, `position` (token position in the document), `left`, `term`, `right`

## collocates

Terms that occur within `--context` tokens on either side of a keyword. Stopwords and the keyword itself are excluded.

Options: `--query` (required, exact match), `--context` (default 5), `--limit` (default 30)

Output: `term`, `term_raw_freq` (keyword occurrences), `context_term`, `context_raw_freq` (co-occurrences inside the window)

## phrases

Word sequences repeated at least twice. Sequences made only of stopwords are dropped. Rows are ordered by count, and longer phrases come first on a tie. A shorter phrase inside a longer one with the same count is omitted.

Options: `--min-length` (default 2), `--max-length` (default 4), `--min-raw` (default 2), `--limit` (default 30)

Output: `phrase`, `length`, `raw_freq`, `distribution`

## correlations

Pearson correlation over per-document relative frequencies, reported separately for term pairs and document pairs. Only terms found in at least two documents are compared, and fewer than three documents gives no meaningful value.

Options: `--query` (`*` allowed), `--limit` (default 20)

Output: a `# terms` table (`term1`, `term2`, `correlation`) and a `# documents` table (`index1`, `doc1`, `index2`, `doc2`, `correlation`)

## segment-correlations

Pearson correlation of two terms over the segment relative frequencies inside one document. Works with a single document.

Options: `--query` (required, at least two terms), `--segments` (default 10)

Output: `index`, `title`, `term1`, `term2`, `segments`, `correlation` (blank when one term is 0 in every segment)

## view

Writes one offline HTML file and a `fonts/` folder beside it. Open it directly in a browser. The Cirrus, TermsBerry, Reader, Trends, Links, Contexts, and Correlations panels share one selection, and the segment count and co-occurrence window are sliders inside the page.

Options: `--output` (required), `--segments` (default 12), `--window` (default 5)

Output: one line with the path of the HTML file
