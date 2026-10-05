# Week 3 — findings

Hybrid search and reranking over the Week 2 baseline (BGE-M3 + structural chunking).
Read alongside `notes/week2-findings.md` and `notes/week3-plan.md`.

*In progress. Started 5 October 2026.*

---

## 0. Baseline reproduced on the 16 GB machine

BGE-M3 + structural, CPU, exact search (NumPy dot product, as in the Week 2 notebook):
**hit rate 1.00, MRR 0.768**, every per-question rank identical to Week 2. The GPU→CPU move
changed nothing.

Two checks before the run:

- `build_chunks` takes its tokenizer from the model config; Week 2 chunked with e5-small's.
  Tested rather than assumed: e5-small and BGE-M3 tokenizers give the **same 113 chunks,
  byte-identical texts**.
- The notebook iterated `QUESTIONS`, not `SPECS`, with `batch_size=32`. Copied both, so the
  hardware was the only remaining difference.

CPU embedding of the corpus: ~105 s, once, at ingestion. Vectors cached in `cache/` (ignored by
Git, rebuilt on demand; the script asserts the cache matches the chunks).