import numpy as np
from sentence_transformers import CrossEncoder


class Reranker:
    """Cross-encoder: reads (query, chunk) together and scores the pair.
    Nothing can be precomputed, so it only runs on a short candidate list."""

    def __init__(self, name="BAAI/bge-reranker-v2-m3", device="cpu", max_length=512):
        self.model = CrossEncoder(name, device=device, max_length=max_length)

    def rerank(self, query, chunks, candidates, n=5):
        """candidates: chunk indices. Returns [(chunk_index, score)], best first."""
        pairs = [(query, chunks[i]["text"]) for i in candidates]
        scores = np.asarray(self.model.predict(pairs, batch_size=8))
        order = np.argsort(-scores)[:n]
        return [(candidates[j], float(scores[j])) for j in order]