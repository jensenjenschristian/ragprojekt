import numpy as np
from sentence_transformers import SentenceTransformer

from src.retrieve import dense_search
from src.rerank import CohereReranker
from src.ingest import build_chunks
from src.models import MODELS
from src.eval_specs import SPECS, QUESTIONS, SPECS_W3, QUESTIONS_W3
from src.evaluate import rank_of

cfg = MODELS["bge-m3"]
chunks = build_chunks(model_key="e5-small")
E = np.load("cache/bge-m3_structural.npy")
assert len(E) == len(chunks)
embed = SentenceTransformer(cfg["name"], device="cpu")

LOCAL_HD10 = {1: 1, 2: 2, 5: 1, 6: 2, 7: 1, 8: 1, 9: 2, 10: 1, 11: 1, 12: 2, 13: 1,
              14: 1, 15: 1, 16: 1, 17: 1}       # §8 results, local bge-reranker-v2-m3

models = {"pro": CohereReranker("rerank-v5.0-pro"), "fast": CohereReranker("rerank-v5.0-fast")}
ranks = {k: {} for k in models}
lat = {k: [] for k in models}

print(f"{'Q':<5}{'local':>7}{'pro':>7}{'fast':>7}")
for Q, S in [(QUESTIONS, SPECS), (QUESTIONS_W3, SPECS_W3)]:
    for qid, question in Q.items():
        q = embed.encode(cfg["query_prefix"] + question, normalize_embeddings=True)
        d = [i for i, _ in dense_search(E, q, n=10)]
        for k, rr in models.items():
            out = [i for i, _ in rr.rerank(question, chunks, d,
                                           with_heading=True, with_delaftale=True)]
            ranks[k][qid] = rank_of([chunks[i] for i in out], S[qid])
            lat[k].append(rr.last_latency)
        n = int(str(qid).lstrip("Qq"))
        print(f"Q{n:<4}{str(LOCAL_HD10[n]):>7}{str(ranks['pro'][qid]):>7}"
              f"{str(ranks['fast'][qid]):>7}", flush=True)

mrr = lambda rs: sum(1 / r for r in rs if r) / len(rs)
num = lambda k: int(str(k).lstrip("Qq"))
for k in models:
    orig = [ranks[k][q] for q in ranks[k] if num(q) <= 13]
    w3 = [ranks[k][q] for q in ranks[k] if num(q) >= 14]
    print(f"{k:<5} MRR original {mrr(orig):.3f}  W3 {mrr(w3):.3f}  "
          f"latency median {np.median(lat[k]):.2f}s  max {max(lat[k]):.2f}s")