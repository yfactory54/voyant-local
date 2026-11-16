"""Lightweight Voyant-style text analysis.

Implements the core tools of Voyant Tools (https://voyant-tools.org), whose
server is https://github.com/voyanttools/VoyantServer and whose analysis
engine is trombone (https://github.com/voyanttools/trombone).

Statistics follow trombone's published definitions:

* relative frequency = raw count / tokens in scope
* per-document z-score = (term count - mean type count) / stdev of type counts
* tf-idf = (raw / doc tokens) * log10(corpus documents / documents containing term)
* term correlation = Pearson r of the two terms' per-document relative frequencies
* document correlation = Pearson r of the two documents' shared-term relative frequencies
"""

__version__ = "1.0.0"
