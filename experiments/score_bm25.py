from src.bm25 import BM25
from src.ingest import build_chunks
from src.eval_specs import SPECS, QUESTIONS
from src.evaluate import rank_of, score
import numpy as np
from src.bm25 import BM25, tokenize

DENSE = {1: 1, 2: 5, 5: 1, 6: 1, 7: 1, 8: 1, 9: 4, 10: 2, 11: 1, 12: 2, 13: 1}
chunks = build_chunks(model_key="e5-small")

for stem in [False, True]:
    bm25 = BM25(chunks, stem=stem)
    results = []
    print(f"\n=== BM25 {'stemmed' if stem else 'raw'} ===")
    for qid, question in QUESTIONS.items():
        scores = bm25.index.get_scores(tokenize(question, stem))
        order = np.argsort(-scores)
        hits = [(int(i), float(scores[i])) for i in order[:5]]
        r = rank_of([chunks[i] for i, _ in hits], SPECS[qid])
        full = rank_of([chunks[i] for i in order], SPECS[qid])   # rank among all 113
        target = next(i for i in order if rank_of([chunks[i]], SPECS[qid]))
        qtok = set(tokenize(question, stem))
        shared = sorted(qtok & set(tokenize(chunks[target]["text"], stem)))
        n = int(str(qid).lstrip("Qq"))
        print(f"Q{n:<3} rank {r}  (of 113: {full})  dense {DENSE[n]}  "
              f"top {hits[0][1]:.2f}  target {scores[target]:.2f}  shared {shared}")
        results.append((qid, r))
    print(score(results))
    
print("\n=== Q12 top 3, stemmed ===")
bm25 = BM25(chunks, stem=True)
q = QUESTIONS[[k for k in QUESTIONS if str(k).lstrip("Qq") == "12"][0]]
qtok = set(tokenize(q, True))
for i, s in bm25.search(q, n=3):
    c = chunks[i]
    print(f"{s:.2f}  {c['source']} p{c['page']}  {c['section']}")
    print(f"      shared {sorted(qtok & set(tokenize(c['text'], True)))}")
    print(f"      {c['text'][:150]!r}")    