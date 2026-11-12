import numpy as np
from sentence_transformers import SentenceTransformer
from src.retrieve import dense_search
from src.rerank import Reranker
from src.ingest import build_chunks
from src.models import MODELS
from src.eval_specs import SPECS, QUESTIONS
from src.evaluate import matches

cfg = MODELS["bge-m3"]
chunks = build_chunks(model_key="e5-small")
E = np.load("cache/bge-m3_structural.npy")
embed = SentenceTransformer(cfg["name"], device="cpu")
rr = Reranker()

q = QUESTIONS["Q9"]
d = [i for i, _ in dense_search(E, embed.encode(cfg["query_prefix"] + q, normalize_embeddings=True), n=10)]
for heading in [False, True]:
    print(f"\n=== with_heading={heading} ===")
    for i, s in rr.rerank(q, chunks, d, with_heading=heading):
        c = chunks[i]
        flag = "  <-- TARGET" if matches(c, SPECS["Q9"]) else ""
        print(f"{s:7.3f}  [{c['delaftale']}] {c['section']}{flag}")
        print(f"         {c['text'][:110]!r}")