import re
import snowballstemmer
import numpy as np
from rank_bm25 import BM25Okapi

# A word is a run of letters/digits, optionally joined by . or , to more letters/digits.
# Keeps 1.728, 0,38 and 12.2 as single tokens; a sentence-final period is dropped.
_TOKEN = re.compile(r"\w+(?:[.,]\w+)*")
_stemmer = snowballstemmer.stemmer("danish")

def tokenize(text, stem=False):
    tokens = _TOKEN.findall(text.lower())
    if stem:
        tokens = _stemmer.stemWords(tokens)
    return tokens

class BM25:
    """BM25 over chunk text only - metadata is never indexed (W2 §1)."""

    def __init__(self, chunks, stem=False):
        self.stem = stem
        self.index = BM25Okapi([tokenize(c["text"], stem) for c in chunks])

    def search(self, query, n=5):
        """Ranked list of (chunk_index, score), best first."""
        scores = self.index.get_scores(tokenize(query, self.stem))
        top = np.argsort(-scores)[:n]
        return [(int(i), float(scores[i])) for i in top]