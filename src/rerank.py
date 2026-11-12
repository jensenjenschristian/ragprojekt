import numpy as np
from sentence_transformers import CrossEncoder
import os
import time

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

class CohereReranker:
    """Hosted reranker with the same rerank() interface as Reranker, so a script swaps
    one object for the other and nothing else changes."""

    def __init__(self, model="rerank-v5.0-pro", min_interval=6.5):
        import cohere                       # imported here so the local reranker
        from dotenv import load_dotenv      # works without the cohere package installed
        load_dotenv()
        self.client = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])
        self.model = model
        self.min_interval = min_interval    # trial key: 10 calls/min -> one per 6 s, plus margin
        self._last_call = 0.0
        self.last_latency = None            # time of the API call only, excluding the wait

    def rerank(self, query, chunks, candidates, n=5, with_heading=False, with_delaftale=False):
        wait = self.min_interval - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        docs = [Reranker._text(chunks[i], with_heading, with_delaftale) for i in candidates]
        t = time.perf_counter()
        resp = self.client.rerank(model=self.model, query=query, documents=docs, top_n=n)
        self.last_latency = time.perf_counter() - t
        self._last_call = time.monotonic()
        return [(candidates[r.index], float(r.relevance_score)) for r in resp.results]