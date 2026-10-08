import numpy as np
from sentence_transformers import SentenceTransformer

from src.bm25 import BM25
from src.retrieve import dense_search, rrf
from src.ingest import build_chunks
from src.models import MODELS
#from src.eval_specs import SPECS, QUESTIONS
import sys
from src.eval_specs import SPECS, QUESTIONS, SPECS_W3, QUESTIONS_W3

if len(sys.argv) > 1 and sys.argv[1] == "w3":
    QUESTIONS, SPECS = QUESTIONS_W3, SPECS_W3
    
from src.evaluate import rank_of

cfg = MODELS["bge-m3"]
chunks = build_chunks(model_key="e5-small")
E = np.load("cache/bge-m3_structural.npy")
assert len(E) == len(chunks)
model = SentenceTransformer(cfg["name"], device="cpu")
bm25 = {"raw": BM25(chunks, stem=False), "stem": BM25(chunks, stem=True)}

variants = ["dense", "bm25-stem", "hybrid-raw", "hybrid-stem"]
ranks = {v: [] for v in variants}

print(f"{'Q':<5}" + "".join(f"{v:>13}" for v in variants))
for qid, question in QUESTIONS.items():
    q = model.encode(cfg["query_prefix"] + question, normalize_embeddings=True)
    d = dense_search(E, q, n=20)
    lists = {
        "dense":       d[:5],
        "bm25-stem":   bm25["stem"].search(question, n=5),
        "hybrid-raw":  rrf([d, bm25["raw"].search(question, n=20)]),
        "hybrid-stem": rrf([d, bm25["stem"].search(question, n=20)]),
    }
    row = []
    for v in variants:
        r = rank_of([chunks[i] for i, _ in lists[v]], SPECS[qid])
        ranks[v].append(r)
        row.append(r)
    n = int(str(qid).lstrip("Qq"))
    print(f"Q{n:<4}" + "".join(f"{str(r):>13}" for r in row))

def metrics(rs):
    n = len(rs)
    return {
        "MRR":   sum(1 / r for r in rs if r) / n,
        "hit@1": sum(1 for r in rs if r == 1) / n,
        "hit@3": sum(1 for r in rs if r and r <= 3) / n,
        "hit@5": sum(1 for r in rs if r) / n,
    }

print()
for v in variants:
    m = metrics(ranks[v])
    print(f"{v:<12}" + "  ".join(f"{k} {x:.3f}" for k, x in m.items()))