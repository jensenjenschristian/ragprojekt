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