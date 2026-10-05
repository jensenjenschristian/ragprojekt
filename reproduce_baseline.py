import time
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

from src.ingest import build_chunks
from src.models import MODELS
from src.eval_specs import SPECS, QUESTIONS
from src.evaluate import rank_of, score

MODEL = "bge-m3"
CACHE = Path("cache") / f"{MODEL}_structural.npy"
EXPECTED = {1: 1, 2: 5, 5: 1, 6: 1, 7: 1, 8: 1, 9: 4, 10: 2, 11: 1, 12: 2, 13: 1}

cfg = MODELS[MODEL]
chunks = build_chunks(model_key="e5-small")          # same tokenizer as Week 2
print(f"{len(chunks)} chunks")

model = SentenceTransformer(cfg["name"], device="cpu")

if CACHE.exists():
    E = np.load(CACHE)
    assert len(E) == len(chunks), "cache does not match chunks - delete it"
    print("loaded cached embeddings")
else:
    t = time.time()
    E = model.encode([cfg["passage_prefix"] + c["text"] for c in chunks],
                     batch_size=32, normalize_embeddings=True,
                     show_progress_bar=True)
    CACHE.parent.mkdir(exist_ok=True)
    np.save(CACHE, E)
    print(f"embedded in {time.time() - t:.0f}s")

results = []
for qid, question in QUESTIONS.items():               # as the notebook did
    q = model.encode(cfg["query_prefix"] + question, normalize_embeddings=True)
    sims = E @ q
    top = np.argsort(-sims)[:5]
    r = rank_of([chunks[i] for i in top], SPECS[qid])
    n = int(str(qid).lstrip("Qq"))
    flag = "" if r == EXPECTED.get(n) else "   <-- differs"
    print(f"Q{n:<3} rank {r}  (week 2: {EXPECTED.get(n)}){flag}")
    results.append((qid, r))

print(f"{len(results)} questions scored")
print(score(results))