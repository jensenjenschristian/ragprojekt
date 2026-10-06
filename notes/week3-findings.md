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

---

## 2. Tokenizer and stemmer, tested before scoring

Token pattern `\w+(?:[.,]\w+)*`: numbers survive whole (`1.728`, `0,38`, `12.2`, `7.30`),
sentence-final periods dropped. `0,38` and `0.38` remain distinct tokens — the known
decimal-separator gap (W2 §7), left for documented post-processing.

**Danish Snowball is inconsistent across one noun paradigm.** Rule-based suffix stripping,
longest match first, no dictionary:

| form | stem |
|---|---|
| sikkerhedsmyndighed / -en / -er | sikkerhedsmynd |
| sikkerhedsmyndighederne | **sikkerhedsmyndighed** |

`-erne` wins on the definite plural and stops; the other forms lose `-hed(en/er)` and then
`-ig`. A stem need not be a word, but it must be the same key for every form — here it isn't.

**Consequence for Q10, noted before the BM25 run:** the corpus contains only
`sikkerhedsmyndigheder` (Aftale p7 and p8); the query has `-erne`. With stemming the query's
rarest token matches nothing, and the word occurs on p7 as well as p8, so even a match would tie.
The §1 prediction (stemmed → rank 1) stands as committed and is now expected to fail.

Not patched: a rule for one paradigm is fitting to one case. The principled alternative is a
lemmatiser (dictionary-based, e.g. spaCy/DaCy Danish) — a candidate third variant if stemming
disappoints.

---

## 3. BM25 alone — results, and what the diagnostics show

| Q | Dense | BM25 raw | BM25 stemmed | Shared tokens (stemmed) |
|---|---|---|---|---|
| Q1 | 1 | 1 | 1 | many |
| Q2 | 5 | — (29) | **2** | `teknisk`, `gæld`, `installation` |
| Q5 | 1 | 1 | 1 | many |
| Q6 | 1 | 1 | 1 | many |
| Q7 | 1 | 1 | 2 | many — 19.62 vs 20.15, a near tie |
| Q8 | 1 | 1 | 1 | many |
| Q9 | 4 | — (27) | — (6) | `udkaldstillæg`, `arbejdstid` — not `københavn` |
| Q10 | 2 | — (101) | — (90) | `leverandør` only |
| Q11 | 1 | 1 | 1 | many |
| Q12 | 2 | 3 | 3 | `kontraktstart` only |
| Q13 | 1 | — (97) | — (100) | `for` only |
| **MRR** | **0.768** | **0.576** | **0.576** | |

Brackets: rank among all 113 chunks.

**Same MRR, different questions.** Stemming fixed Q2, found Q9's key token, cost Q7 a rank.
The aggregate hides all of it — the W2 §11 lesson again.

### Against the predictions (§1)

- **Q2 — wrong, in the useful direction.** Predicted a compound-noun problem that BM25 would
  make worse. Stemming of *ordinary inflection* (`gælder`, `installationerne`) took it from
  rank 29 to 2, beating dense (5). The one question so far where BM25 is right and dense is not.
- **Q9 — stemming worked as predicted** (`udkaldstillægget` → `udkaldstillæg`) but the target
  lands at 6. `københavn` is not in the chunk text: assumption 1 confirmed.
- **Q10 — failed as diagnosed in §2.** Only `leverandør` shared.
- **Q13 — as predicted.** Reverse compound; only `for` shared.
- **Q12 — wrong, and the reason is the eval set, not the retriever.** See below.

### Q12 has three correct answers; the spec accepts one

Top 3 under dense, and BM25's rank 1:

1. Udbudsbetingelser p4 — *"Kontraktstart den 1. december 2026 forudsætter…"* (adds that the
   date may slip)
2. Udbudsbetingelser p6–7 — the tidsplan (**the only chunk the spec accepts**)
3. Aftale p16, `18.1 Løbetid` — *"Denne Aftale træder i kraft den 1. december 2026…"* (the
   binding source)

Both retrievers put a correct answer at rank 1. Q12 is not headroom; **the real headroom is Q2,
Q9, Q10.** With a multi-answer spec, dense MRR would be 0.814.

Same defect class as W2's Q4: a question is only a clean test if it has exactly one acceptable
answer. Spec frozen for this week; **Week 6 golden set should allow several acceptable chunks
per question.**

Also corrects assumption 2: the tidsplan halves are one structural chunk (`pages=[6, 7]`),
not two.

Minor: BM25 rank 2 for Q12 (Udelukkelsesgrunde) shares only `er`, `hvornår` — a question word
acting as a rare keyword. Real, but not what beat the target.