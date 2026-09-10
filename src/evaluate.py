def matches(chunk, spec):
    """Does this chunk satisfy the match spec? All fields must hold."""
    if spec is None:
        return False
    if "source" in spec and chunk["source"] != spec["source"]:
        return False
    if "page" in spec:
        pages = chunk.get("pages") or [chunk.get("page")]
        if spec["page"] not in pages:
            return False
    if "delaftale" in spec and chunk.get("delaftale") != spec["delaftale"]:
        return False
    if "contains" in spec and spec["contains"] not in chunk["text"]:
        return False
    return True


def rank_of(retrieved, spec):
    """1-based rank of the first matching chunk, or None if absent."""
    for i, c in enumerate(retrieved, start=1):
        if matches(c, spec):
            return i
    return None


def score(results):
    """results: list of (qid, rank_or_None). Returns hit rate and MRR."""
    n = len(results)
    hits = sum(1 for _, r in results if r is not None)
    mrr = sum(1 / r for _, r in results if r is not None) / n
    return {"n": n, "hit_rate": hits / n, "mrr": mrr}