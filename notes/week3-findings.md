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

---

## 4. Hybrid (RRF, k=60, top-20 from each) — a net loss

| Q | Dense | BM25-stem | Hybrid-raw | Hybrid-stem |
|---|---|---|---|---|
| Q2 | 5 | 2 | — | **2** |
| Q9 | 4 | — | — | 5 |
| Q10 | 2 | — | 5 | **—** |
| Q12 | 2 | 3 | 2 | 2 |
| Q13 | 1 | — | 4 | **—** |
| others | 1 | 1 (Q7: 2) | 1 | 1 |
| **MRR** | **0.768** | 0.576 | 0.632 | 0.655 |
| hit@1 / @3 / @5 | 0.64 / 0.82 / 1.00 | 0.45 / 0.73 / 0.73 | 0.55 / 0.64 / 0.82 | 0.55 / 0.73 / 0.82 |

Hybrid-stem vs dense: Q2 +0.30, Q9 −0.05, Q10 −0.50, Q13 −1.00 → net −0.114.

**Why.** With k=60 a chunk in both lists scores ≥ 2/80 = 0.025; a chunk in one list scores at
most 1/61 = 0.016. Agreement dominates. Q10 and Q13 were absent from BM25's top 20, so every
chunk both retrievers liked overtook them. Equal-weight fusion assumes comparably competent
retrievers; BM25 here is much weaker, and fails by absence rather than by rank.

**BM25 adds no recall on this eval set.** Dense hit@5 = 1.00, so dense top-20 already contains
every target. BM25's only possible contribution is ordering (Q2), which RRF trades badly. The
eval set cannot test the core hybrid argument — that sparse retrieval finds what dense misses —
because dense misses nothing here.

**Decisions.**
- No RRF tuning (k or weights) — fitted to 11 questions.
- Treat fusion as **candidate generation**; ordering is the reranker's job (step 5). Recall of
  the dense-20 ∪ BM25-20 pool is 11/11.
- Write the deferred step 2 questions (lexical gap, clause address, numeric form) **before** the
  reranker runs, since only questions dense might miss can measure BM25's recall value.

Against §1: hybrid on Q2 predicted ≥5, got 2; Q10 predicted 1, missed; Q13 predicted 1–3, missed.

---

## 5. Four additional questions (Q14–Q17), written before any reranker ran

Scored separately from the frozen 11. Specs verified against the chunks before any retriever
ran on them: Q14 matches 3 chunks (6.4 is split across three — all correct answers); Q15–Q17
match exactly one each. `matches()` gained an optional `section` field; baseline re-run after
the change: MRR 0.768, unchanged.

| Q | Question | Tests |
|---|---|---|
| Q14 | Hvad står der i punkt 6.4 i aftalen? | lookup by clause number; `6.4` exists only as metadata and in a cross-reference |
| Q15 | Skal fakturaen indeholde EAN-nummer? | rare exact identifier — the BM25 case |
| Q16 | Hvilket nummer skal man ringe til, hvis der går ild i noget på campus? | synonym gap `ild`/`brand` — the dense case |
| Q17 | Gælder aftalen også for undervisningsbygninger? | suspended compound — the full word never occurs |

Corpus notes from building them:
- Clause 6.4 exceeds 400 tokens and spans three chunks. A lookup by clause number returns a
  third of the clause → parent-document retrieval for W5/W7.
- `laboratoriebygninger` is now whole; the split recorded in W2 §10 is gone from the current
  chunks (presumably the hyphen-join rule). Original Q17 premise dropped.

### Predictions

| Q | Dense | BM25-stem | Hybrid |
|---|---|---|---|
| Q14 | miss | miss (rank 1 = Udb p12 cross-reference) | miss |
| Q15 | 1–3 | 1 | 1 |
| Q16 | 1–2 | 2–5 | 1–3 |
| Q17 | 1–3 | miss | 1–5 |

Overall: no question where BM25 finds what dense misses. The case dense fails (Q14) is an
addressing problem that BM25 also fails. If this holds, dense failures on this corpus are
routing problems (address, delaftale), not keyword problems.

### Results

| Q | Dense | BM25-stem | Hybrid-raw | Hybrid-stem |
|---|---|---|---|---|
| Q14 | — | — | — | — |
| Q15 | 1 | 1 | 1 | 1 |
| Q16 | 2 | 4 | 1 | 2 |
| Q17 | 4 | — | — | — |

Predictions: dense 3/4, BM25 4/4, hybrid 2/4. The overall prediction held — **no question in
15 where BM25 finds what dense misses.** Q14 is missed by every text retriever (that BM25's
rank 1 is the Udb p12 cross-reference was predicted but not checked).

**The hybrid pattern across all 15 questions:** losses where BM25 has nothing — Q10 (2→—),
Q13 (1→—), Q17 (4→—); gains Q2 (5→2, stem) and Q16 (2→1, raw). Equal-weight RRF converts
BM25's absences into dense losses.

**Conclusion for step 4: RRF hybrid is not adopted as the default retriever.** On this corpus
the questions dense fails are routing problems — an address (Q14), a delaftale (Q9, Q13) —
not keyword problems. BM25 is kept only as a candidate source for the reranker, where its
contribution can be measured as pool recall rather than fused rank.

---

## 6. Reranker (bge-reranker-v2-m3) — predictions before the run

§1 rerank predictions stand for the original questions (Q2 2–3, Q9 2–3, Q10 1, Q12 1, Q13 1–3,
Q6 1–2). Added:

| Q | Rerank prediction | Why |
|---|---|---|
| Q14 | miss | no text signal for an address; the reranker sees only text |
| Q15 | 1 | already 1 everywhere |
| Q16 | 1 | cross-encoder reads `brand` against `ild` in context |
| Q17 | 1–3 | the suspended compound is readable in context |

**Pool prediction:** reranking dense-20 and reranking dense-20 ∪ BM25-20 give the same ranks.
Dense-20 already contains every findable target; BM25 can only add distractors. Any difference
is BM25 hurting, not helping.

**Q12 caveat:** a good reranker will likely put the p4 sentence or Aftale 18.1 first; the spec
only accepts the tidsplan, so a rank of 2–3 there is a correct result.

### Results

| Q | Dense | Rerank (dense-20) | Rerank (union) |
|---|---|---|---|
| Q2 | 5 | 2 | 2 |
| Q6 | 1 | 2 | 2 |
| Q9 | 4 | 5 | 5 |
| Q10 | 2 | 1 | 1 |
| Q12 | 2 | 2 | 2 |
| Q13 | 1 | 3 | 3 |
| Q14 | — | — | — |
| Q16 | 2 | 1 | 1 |
| Q17 | 4 | 1 | 1 |
| others | 1 | 1 | 1 |

Original 11: MRR 0.768 → 0.730, hit@1 0.64 → 0.55, hit@3 0.82 → 0.91.
Q14–Q17: MRR 0.438 → 0.750.

**The split is by question type, and it was predicted.**
- *Answer in the text, worded differently* (Q2, Q10, Q16, Q17): reranker wins every time.
- *Only metadata discriminates* (Q6 source, Q9 and Q13 delaftale): reranker loses. Nothing in
  the text to decide on; dense's rank 1 on Q6/Q13 was a lucky tie-break, not understanding.
- On the original questions where text can decide (Q1, 2, 5, 7, 8, 10, 11):
  **dense MRR 0.814 → reranked 0.929.** That is the reranker's real effect.

**Q13 is underspecified.** The question does not name a delaftale; the spec demands
København. All three sheets answer it as asked. Same defect class as Q12 → Week 6.

**Pool:** rerank(dense-20) and rerank(dense-20 ∪ BM25-20) give identical ranks on all 15
questions. BM25 contributes nothing to this pipeline, even as a candidate source.

**Q14:** a 6.4 chunk *is* in dense-20, but the reranker cannot recognise it — `6.4` is only
in metadata. Next experiment: section heading prepended to the reranker input.

**Latency (CPU, bge-reranker-v2-m3): median 24.6 s per query, ~1 s per candidate.**
Unusable interactively. Strongest argument so far for the hosted reranker (step 8) or a
shorter candidate list.

Against predictions: Q2 ✓, Q6 ✓ (noise), Q9 ✗ (predicted 2–3, got 5), Q10 ✓, Q12 ✓ (caveat),
Q13 ✓, Q14 ✓, Q15 ✓, Q16 ✓, Q17 ✓, pool ✓.

---

## 7. Reranker with section heading, and pool size 10 — predictions before the run

Variant: the chunk's `section` is prepended to the text the reranker reads
(`"6.4 Afregning af materialeforbrug\n<chunk>"`). Query-time only — nothing indexed changes, so
the W2 §1 decision (no metadata in indexed text) is untouched. Chunks with no section are
unchanged.

| Q | Rerank (plain, §6) | Prediction with heading | Why |
|---|---|---|---|
| Q14 | — | **top 5, likely 1** | `6.4` becomes readable text |
| Q12 | 2 | 1–3 | `7. Tidsplan` and `18.1 Løbetid` both relevant — could go either way |
| Q6 | 2 | 2 (or arbitrary flip) | headings differ, but the question doesn't ask contract vs tender |
| Q9, Q13 | 5, 3 | unchanged | all three sheets share the same section; delaftale is not a heading |
| others | — | unchanged ±1 | a heading adds a few generic words; may shift near ties |

**Pool 10 vs 20:** identical ranks if every target sits in dense top 10; latency roughly halved
(~12 s per query).

### Results

| Q | Plain-20 | Head-20 | Head-10 | Dense rank |
|---|---|---|---|---|
| Q9 | 5 | — | — | 4 |
| Q14 | — | **1** | **1** | 9 |
| all others | unchanged | | | |

Original 11 MRR 0.730 → 0.712 (Q9 only); Q14–Q17 MRR 0.750 → **1.000**.
Pool 10 = pool 20 on all 15 questions; latency 22.6 s → 13.0 s. **Margin is thin:** the deepest
target sits at dense rank 9. Pool 10 is fitted to this set — recheck on the W6 set.

All 15 questions: dense 0.680 → dense-10 + rerank-with-heading **0.789**.

Predictions: Q14 ✓, Q6/Q12/Q13 ✓, pool-10 latency ✓, **Q9 ✗**.

**Q9 diagnosis — hypothesis rejected.** Predicted the mislabelled Tilbudsevaluering table (W2 §9)
would crowd in. It never appears. Actual cause: section 4.3 Hasteopgaver spans two chunks; with
headings, the second also starts with the query's own word and rises to rank 4 (0.230), pushing
the København table (0.236) to 6. A noise-scale reshuffle among scores of ~0.23.

**Q9 is a two-part question.** The reranker's top two are `4.3 Hasteopgaver` and `6.3 Tillæg`
("3 x timesats" — the rule); the København table supplies the figure (1848). A complete answer
needs rule + figure; the spec accepts only the figure. Same defect class as Q12 → W6. First
concrete multi-chunk case for W5.

**The three sheets are ordered by chance** — the question names København, the chunk text does
not.

---

## 8. Reranker with delaftale — predictions before the run

Variant: `Delaftale <X>` prepended (with the section heading) for chunks that have a delaftale.
Query-time only, same rationale as §7.

| Q | Head-10 | Prediction | Why |
|---|---|---|---|
| Q9 | — | **3** | question names København → København table first among the three sheets; 4.3 and 6.3 stay above it, legitimately |
| Q13 | 3 | 3 (unchanged, ±arbitrary) | question names no delaftale |
| all others | — | unchanged | no other target has a delaftale |

Hypothesis: exposing metadata to the reranker solves a metadata question **only when the
question names the value**.