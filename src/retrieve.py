import numpy as np


def dense_search(E, q_vec, n=20):
    """Exact cosine search over normalised vectors. [(chunk_index, score)], best first."""
    sims = E @ q_vec
    top = np.argsort(-sims)[:n]
    return [(int(i), float(sims[i])) for i in top]


def rrf(ranked_lists, k=60, n=5):
    """Reciprocal Rank Fusion. Uses ranks only - the scores in each list are ignored,
    so BM25's unbounded scores and cosine's 0-1 range never have to be compared.

    Ties are broken by first appearance, i.e. by the order of `ranked_lists`
    (put dense first and it wins ties)."""
    fused = {}
    for lst in ranked_lists:
        for rank, (i, _) in enumerate(lst, start=1):
            fused[i] = fused.get(i, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda x: -x[1])[:n]