import numpy as np
from sentence_transformers import CrossEncoder


class Reranker:
    """Cross-encoder: reads (query, chunk) together and scores the pair.
    Nothing can be precomputed, so it only runs on a short candidate list."""

    def __init__(self, name="BAAI/bge-reranker-v2-m3", device="cpu", max_length=512):
        self.model = CrossEncoder(name, device=device, max_length=max_length)

    #def rerank(self, query, chunks, candidates, n=5):
    #    """candidates: chunk indices. Returns [(chunk_index, score)], best first."""
    #    pairs = [(query, chunks[i]["text"]) for i in candidates]
    #    scores = np.asarray(self.model.predict(pairs, batch_size=8))
    #    order = np.argsort(-scores)[:n]
    #    return [(candidates[j], float(scores[j])) for j in order]
    ##def rerank(self, query, chunks, candidates, n=5, with_heading=False):
    ##    """candidates: chunk indices. Returns [(chunk_index, score)], best first."""
    ##    pairs = [(query, self._text(chunks[i], with_heading)) for i in candidates]
    ##    scores = np.asarray(self.model.predict(pairs, batch_size=8))
    ##    order = np.argsort(-scores)[:n]
    ##    return [(candidates[j], float(scores[j])) for j in order]

    ##@staticmethod
    ##def _text(chunk, with_heading):
    ##    if with_heading and chunk.get("section"):
    ##        return f"{chunk['section']}\n{chunk['text']}"
    ##    return chunk["text"]
    def rerank(self, query, chunks, candidates, n=5, with_heading=False, with_delaftale=False):
        """candidates: chunk indices. Returns [(chunk_index, score)], best first."""
        pairs = [(query, self._text(chunks[i], with_heading, with_delaftale))
                 for i in candidates]
        scores = np.asarray(self.model.predict(pairs, batch_size=8))
        order = np.argsort(-scores)[:n]
        return [(candidates[j], float(scores[j])) for j in order]

    @staticmethod
    def _text(chunk, with_heading=False, with_delaftale=False):
        head = []
        if with_delaftale and chunk.get("delaftale"):
            head.append(f"Delaftale {chunk['delaftale']}")
        if with_heading and chunk.get("section"):
            head.append(chunk["section"])
        return "\n".join(head + [chunk["text"]])