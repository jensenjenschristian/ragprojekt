import time
import numpy as np
from sentence_transformers import SentenceTransformer

from src.bm25 import BM25
from src.retrieve import dense_search
from src.rerank import Reranker
from src.ingest import build_chunks
from src.models import MODELS
from src.eval_specs import SPECS, QUESTIONS, SPECS_W3, QUESTIONS_W3
from src.evaluate import rank_of

cfg = MODELS["bge-m3"]
chunks = build_chunks(model_key="e5-small")
E = np.load("cache/bge-m3_structural.npy")
assert len(E) == len(chunks)
embed = SentenceTransformer(cfg["name"], device="cpu")
bm25 = BM25(chunks, stem=True)
rr = Reranker()
rr.rerank("opvarmning", chunks, [0, 1])          # warm-up: first call pays one-off setup


def rank_in(idxs, spec):
    return rank_of([chunks[i] for i in idxs], spec)


def metrics(rs):
    n = len(rs)
    return (f"MRR {sum(1 / r for r in rs if r) / n:.3f}  "
            f"hit@1 {sum(r == 1 for r in rs) / n:.2f}  "
            f"hit@3 {sum(bool(r) and r <= 3 for r in rs) / n:.2f}  "
            f"hit@5 {sum(bool(r) for r in rs) / n:.2f}")


timings = []
for label, Q, S in [("original 11", QUESTIONS, SPECS), ("W3 Q14-Q17", QUESTIONS_W3, SPECS_W3)]:
    print(f"\n=== {label} ===")
    print(f"{'Q':<5}{'dense':>7}{'rr-dense':>10}{'rr-union':>10}   in pool (dense-20 / union)")
    cols = {"dense": [], "rr-dense": [], "rr-union": []}
    for qid, question in Q.items():
        q = embed.encode(cfg["query_prefix"] + question, normalize_embeddings=True)
        d = [i for i, _ in dense_search(E, q, n=20)]
        b = [i for i, _ in bm25.search(question, n=20)]
        union = d + [i for i in b if i not in d]

        t = time.perf_counter()
        rd = [i for i, _ in rr.rerank(question, chunks, d)]
        timings.append((len(d), time.perf_counter() - t))
        t = time.perf_counter()
        ru = [i for i, _ in rr.rerank(question, chunks, union)]
        timings.append((len(union), time.perf_counter() - t))

        row = {"dense": rank_in(d[:5], S[qid]), "rr-dense": rank_in(rd, S[qid]),
               "rr-union": rank_in(ru, S[qid])}
        for k, v in row.items():
            cols[k].append(v)
        pool = (f"{'yes' if rank_in(d, S[qid]) else 'no':>4} / "
                f"{'yes' if rank_in(union, S[qid]) else 'no'} ({len(union)})")
        n = int(str(qid).lstrip("Qq"))
        print(f"Q{n:<4}" + "".join(f"{str(v):>{w}}" for v, w in
                                   zip(row.values(), (7, 10, 10))) + f"   {pool}")
    print()
    for k, v in cols.items():
        print(f"{k:<9} {metrics(v)}")

secs = [s for _, s in timings]
per_cand = [s / n for n, s in timings]
print(f"\nCPU rerank latency: median {np.median(secs):.2f}s per query, "
      f"{1000 * np.median(per_cand):.0f} ms per candidate")