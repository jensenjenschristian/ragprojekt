import time
import numpy as np
from sentence_transformers import SentenceTransformer

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
rr = Reranker()
rr.rerank("opvarmning", chunks, [0, 1])          # warm-up

PLAIN_20 = {1: 1, 2: 2, 5: 1, 6: 2, 7: 1, 8: 1, 9: 5, 10: 1, 11: 1, 12: 2, 13: 3,
            14: None, 15: 1, 16: 1, 17: 1}       # §6 results, for comparison

rank_in = lambda idxs, spec: rank_of([chunks[i] for i in idxs], spec)
times = {"hd10": [], "h10": []}
ranks = {"hd10": {}, "h10": {}}

print(f"{'Q':<5}{'plain-20':>9}{'h+del-10':>10}{'head-10':>9}   dense rank (of 20)")
for Q, S in [(QUESTIONS, SPECS), (QUESTIONS_W3, SPECS_W3)]:
    for qid, question in Q.items():
        q = embed.encode(cfg["query_prefix"] + question, normalize_embeddings=True)
        d = [i for i, _ in dense_search(E, q, n=20)]
        for key, pool, dl in [("h10", d[:10], False), ("hd10", d[:10], True)]:
            t = time.perf_counter()
            out = [i for i, _ in rr.rerank(question, chunks, pool, with_heading=True, with_delaftale=dl)]
            times[key].append(time.perf_counter() - t)
            ranks[key][qid] = rank_in(out, S[qid])
        n = int(str(qid).lstrip("Qq"))
        print(f"Q{n:<4}{str(PLAIN_20[n]):>9}{str(ranks['hd10'][qid]):>9}"
              f"{str(ranks['h10'][qid]):>9}   {rank_in(d, S[qid])}")

orig = [k for k in ranks["hd10"] if int(str(k).lstrip("Qq")) <= 13]
w3 = [k for k in ranks["hd10"] if int(str(k).lstrip("Qq")) >= 14]
mrr = lambda rs: sum(1 / r for r in rs if r) / len(rs)
for key in ["hd10", "h10"]:
    print(f"{key}: MRR original {mrr([ranks[key][k] for k in orig]):.3f}  "
          f"W3 {mrr([ranks[key][k] for k in w3]):.3f}  "
          f"median latency {np.median(times[key]):.1f}s")