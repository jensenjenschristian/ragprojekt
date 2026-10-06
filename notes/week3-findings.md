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

---

## 1. Predictions, written before any Week 3 retriever ran

Rank of the correct chunk in the top 5 (1 = best, miss = not in top 5). Dense is measured
(§0); every other column is a prediction. Recorded so results can be checked against them —
a prediction written after the run is an explanation.

| Q | Dense | BM25 raw | BM25 stemmed | Hybrid | Rerank | Reasoning |
|---|---|---|---|---|---|---|
| Q12 kontraktstart | 2 | 1 | 1 | 1 | 1 | `kontraktstart` is a rare exact token in the target chunk |
| Q10 sikkerhedsmyndighederne | 2 | worse/miss | 1 | 1 | 1 | query `-erne` vs corpus `-er`; only stemming makes the rare token match |
| Q2 tekniske krav | 5 | worse | worse | ≥5 | 2–3? | target says `Kravspecifikation` — compound, `krav` won't match; BM25 favours chunks literally saying "tekniske krav" |
| Q9 udkaldstillæg København | 4 | miss | top 3 | 2–3 | 2–3 | label is in all three sheets; `København` likely metadata only, not chunk text |
| Q13 elektrikersvend | 1 | miss | miss | 1–3 | 1–3 | reverse compound: query `elektrikersvend`, table `Elektriker svend`; sheets differ only in digits absent from the query |
| Q6 sekundær leverandør | 1 | 1–2 | 1–2 | 1–2 | 1–2 | passage identical in Aftale and Udbudsbetingelser; only surrounding text differs |

**Overall predictions:**

- BM25 helps Q10 and Q12 only — Q10 only with stemming. Expected hybrid gain ≈ +0.09 MRR
  (two questions 2 → 1).
- Q9 and Q13 cannot be fixed by any text-based ranking. They need the delaftale extracted from
  the query and applied as a filter — a routing problem, not a ranking one.
- **Movement on Q13 or Q6 is noise, not a finding.**
- Q2 is a compound-noun problem that looks like a retrieval problem. If step 6 (decompounding)
  moves it, that is the week's Danish-specific result.

**Assumptions, deliberately not checked yet** (checking them now would turn predictions into
lookups):

- `København` does not appear in the text of the Q9/Q13 chunks
- Q12's rank-1 dense chunk is the p6 half of the tidsplan
- Danish Snowball strips `-erne` and `-et` as expected

**Step 2 (extend the eval set) deferred** until the original 11 have run through BM25 and
hybrid. The predictions already point at which new questions are worth writing.