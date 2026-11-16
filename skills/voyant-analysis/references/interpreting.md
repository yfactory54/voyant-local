# Reading the numbers

## Definitions

- relative frequency = count / tokens in the same scope (document, segment, or corpus)
- per million (PPM) = relative frequency × 1,000,000. Use it instead of counts to compare documents of different lengths.
- z-score = (term count − mean term count in that document) / standard deviation. Larger for terms that are unusually frequent within the document.
- tf-idf = (count / document tokens) × log10(documents / documents containing the term). A term found in every document scores 0.
- correlation = Pearson r of relative-frequency vectors. Near +1 the terms rise and fall together; near −1 one is frequent where the other is rare.

## Comparing

- When documents differ in length, compare `relative_freq` or `ppm`, not `raw_freq`.
- `trends` divides each document separately. The same segment number means the same relative position (for example, the first 10%), not the same number of tokens.
- Collocates count how often two terms appear close together; correlations measure how they rise and fall together across documents or segments. They answer different questions.

## Easy to overstate

- Small corpus: below a few thousand tokens, one or two occurrences swing the per-million figure. Report counts alongside it.
- Segments too fine: with fewer than about 100 tokens per segment, a trend line flips between 0 and its peak as noise. Keep `--segments` at or below the document's token count / 100.
- Correlations over few documents: `correlations` uses one point per document. With three or four documents, ±0.9 can happen by chance. The same holds for `segment-correlations` with few segments.
- Correlation is not cause: a high r only says the terms move together. Why they do is shown by the sentences you check with `contexts`.
- Stoplist effects: the default removes English stopwords. If function words are the subject of study, rerun with `--stopwords none`.
- Korean particles: one word spread across several forms makes each form look rarer than the word is. Combine the forms before interpreting.
