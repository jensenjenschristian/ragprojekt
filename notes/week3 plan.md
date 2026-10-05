# Week 3 — plan and handoff

Read alongside `notes/week2-findings.md` and the Week 3 section of `rag-course-syllabus.md`.
This file records decisions already made so the Week 3 chat doesn't re-litigate them.

*Written 5 October 2026, at the start of Week 3.*

---

## Where things stand

Week 2 is complete and committed. Docling (parsed in Colab, JSON committed to `data-parsed/`)
→ schema walk in `src/parse_docling.py` → 601 elements after curation → structural chunking
(400-token, section-bounded, 113 chunks) → embeddings → swappable store (`src/store.py`:
Numpy / Chroma / FAISS) → scored by `src/evaluate.py` against 11 retrieval questions.

**Machine:** now on the 16 GB machine. BGE-M3 and a local reranker run here; Colab is no
longer required for anything this week.

---

## Goal of the week

Move from "it retrieves something" to "it retrieves the right thing" — and, more usefully,
find out *which* of the remaining misses are retrieval problems at all.

**Deliverable:** a retrieval pipeline with hybrid search + reranking, a results table across
variants, and before/after examples per question.

---

## The baseline to beat

BGE-M3 + structural, k=5: **hit rate 1.00, MRR 0.768.**

| Q1 | Q2 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 | Q11 | Q12 | Q13 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **5** | 1 | 1 | 1 | 1 | **4** | 2 | 1 | 2 | 1 |

Two consequences for how the week is measured:

- **Hit@5 is saturated.** It cannot show an improvement. Report **hit@1 and hit@3** alongside
  MRR; those are where movement is visible.
- **The headroom is four questions.** Q2, Q9, Q10 and Q12 hold all of the missing 0.232 MRR.
  With 11 questions, a single 2→1 rank change moves MRR by 0.045. **Treat any aggregate
  difference under ~0.05 as noise unless the per-question table explains it.**

---

## Order of work

### 0. Reproduce the Week 2 baseline on this machine

Run BGE-M3 + structural locally and confirm MRR 0.768 and the per-question ranks above,
exactly. The Week 2 numbers came from Colab on a GPU; CPU embeddings can differ in the last
decimal places, which can flip a near-tie in ranking.

If they don't match, stop and find out why before building anything on top. This is the
"check the pipe before diagnosing the water" rule from `week2-findings.md` §14, applied
before there is any water.

Also: cache the BGE-M3 chunk embeddings to disk. Every experiment this week reuses them, and
re-embedding is the only slow step.

### 1. Write predictions before running anything

For each of the four headroom questions plus Q6 and Q13, write one line in
`notes/week3-findings.md`: *does BM25 help, does reranking help, why.* Thirty minutes.

Same discipline as writing the eval set before the comparison in Week 2. A prediction written
afterwards is an explanation, and you will always be able to produce one.

Two predictions are already fixed by Week 2's findings and should be recorded as such:

- **Q6 and Q13 cannot be improved by BM25 or a reranker.** Byte-identical text — every
  text-based scorer ties. Only the `source` / `delaftale` metadata separates them. If either
  moves, find out why; it is probably a tie broken by array order, not a real gain.
- **Modality will not be fixed by a reranker either.** A cross-encoder reads the text, so it
  *can* see `skal` vs `bør` in principle — but whether it weighs them is an empirical
  question. Worth one probe, not a conclusion in advance.

### 2. Optionally extend the eval set — but keep it separable

The existing 11 questions were written for chunking and embeddings. Week 3 targets different
failures, and Week 2 already logged the cases:

- **Lexical gap:** `aktør` / `leverandør` (Udbudsbetingelser p4); `referenceprislisten` /
  `referenceliste` (Aftale p10 vs Bilag 4)
- **Address lookup:** a query naming a clause number, e.g. *"Hvad står der i 6.4?"*
- **Numeric form:** a query for *38 % rabat* against an index holding `0.38`

If you add these (Q14+), **report the original 11 and the new ones as separate rows.** The
original 11 are the baseline comparison; new questions written knowing that BM25 is coming
are useful but not neutral. Mixing them would make hybrid look better by construction.

Same verification as Week 2: each new question gets a `**Match:**` line, checked against the
parsed corpus to match exactly one chunk, *before* any retriever runs.

### 3. BM25 alone

`rank_bm25` over the same 113 structural chunks. **Tokenisation is the real decision here,
not the library.** Run at least two variants:

1. lowercase + split on non-alphanumerics
2. as (1) + Danish Snowball stemmer (`snowballstemmer` or `PyStemmer`) + Danish stopwords

Things to get right:

- **Index chunk text only.** Metadata stays in metadata fields (Week 2 §1 decision). Prepending
  `source` would put filename tokens into every chunk's term frequencies.
- **Numbers survive tokenisation.** Check what your splitter does to `1.728`, `0,38`, `12.2`,
  `07.30-15.30`. A tokeniser that splits on `.` turns `1.728` into `1` and `728`, and `12.2`
  into two tokens that match every other clause numbered 12 or 2.
- **Score BM25 alone** with the same `evaluate.py`. It needs to be a first-class retriever to
  be fused meaningfully.

Concept to be able to explain: BM25 is TF-IDF with two corrections — term-frequency
saturation (`k1`; the tenth occurrence of a word adds little) and length normalisation (`b`;
long chunks don't win just by containing more words). Don't tune `k1`/`b` on 11 questions.

### 4. Hybrid with Reciprocal Rank Fusion

Write RRF by hand — it's ten lines, and seeing the arithmetic is the point:

```
score(chunk) = Σ over retrievers  1 / (k + rank_in_that_retriever)      k = 60
```

RRF uses **ranks, not scores**, which is why it works: BM25 scores are unbounded and BGE-M3
cosines sit in 0.48–0.99 (Week 2 §12). Adding them directly would let whichever has the larger
numeric range dominate. Ranks put both on the same footing for free.

- Fuse from a deeper candidate list (top 20 from each) than you finally return (top 5).
- Keep `k = 60`. It is the published default; choosing another value on 11 questions is
  fitting.
- Score: dense vs BM25 vs BM25-stemmed vs hybrid.

### 5. Rerank the fused set

**Use `BAAI/bge-reranker-v2-m3`, not `bge-reranker-base`.** The base model is trained on
Chinese and English; v2-m3 is built on the same multilingual backbone as BGE-M3. Same lesson
as MiniLM in Week 2 §11 — an English-centric model will run on Danish without complaint.
*(Verify the current model name on Hugging Face before pinning it.)*

Pipeline: hybrid top-20 → cross-encoder scores each (query, chunk) pair → top-5.

Concepts to be able to explain: a bi-encoder (BGE-M3) embeds query and chunk *separately*, so
chunk vectors can be precomputed — fast, but the two never "see" each other. A cross-encoder
reads query and chunk *together* in one pass — much more accurate, but nothing can be
precomputed, so it is only affordable on a short candidate list. That is why retrieval is
two-stage.

Measure **latency on CPU** for 20 candidates. This number goes into Week 4's latency budget.

**Open experiment, flagged rather than decided:** whether to give the reranker the section
heading alongside chunk text (e.g. `"6.4 Afregning af materialeforbrug\n<chunk>"`). The Week 2
decision was that metadata stays out of *indexed* text — for embedding and BM25. Reranker input
is constructed at query time and never indexed, so this does not reopen that decision. But
measure it as a separate variant; don't make it the default silently.

### 6. Danish decompounding (timeboxed — 2–3 hours)

`informationssikkerhedskrav` does not match `sikkerhedskrav`. Snowball handles inflection,
not compounds.

Suggested approach, cheapest first: a **corpus-derived splitter** — split a token if both
parts (allowing the linking `-s-` / `-e-`) exist in the corpus's own vocabulary. Index the
compound *and* its parts for BM25. No external dictionary, and the behaviour is auditable.

Two cautions:

- Over-splitting is the dangerous direction. `Week 2 §10` declined a rule for `nødog` because
  machinery fitted to one case damages real compounds. Inspect a sample of splits before
  trusting it.
- Measure on the lexical-gap questions from step 2. If it moves nothing on the eval set,
  record that — it is a real finding, not a failed step.

If the timebox runs out, write down where it got to and move on. This is portfolio-relevant
but not on the critical path.

### 7. "Lost in the middle" — implement, don't over-invest

Reorder the final context so the strongest chunks sit at the start and end of the prompt,
weakest in the middle. A small function in the generation path.

Honest expectation: with 5 chunks of ~200 tokens, this is ~1,000 tokens of context — far below
where the effect is documented. It is unlikely to be measurable here, and it is a generation
effect, so it can't be scored with `evaluate.py` anyway. Implement it, note it, revisit in
Week 6 if there's an eval that can see it.

### 8. Hosted swap: Cohere Rerank

Compare against the local reranker on **quality (same eval) and latency**. Use Cohere's
multilingual rerank model — check the current name and trial-key limits before starting.

Note what is *not* comparable: local latency is compute, hosted latency is mostly network.
Record both, but don't conclude one is "faster" from a single number.

---

## Results table to fill in

Original 11 questions, k=5, BGE-M3 + structural chunks throughout:

| Variant | MRR | hit@1 | hit@3 | hit@5 | Q2 | Q9 | Q10 | Q12 |
|---|---|---|---|---|---|---|---|---|
| Dense (baseline) | 0.768 | | | 1.00 | 5 | 4 | 2 | 2 |
| BM25 | | | | | | | | |
| BM25 + stemming | | | | | | | | |
| Hybrid (RRF) | | | | | | | | |
| Hybrid + rerank (local) | | | | | | | | |
| Hybrid + rerank + heading | | | | | | | | |
| Hybrid + rerank (Cohere) | | | | | | | | |

Plus the full per-question rank table, and a separate block for Q14+ if added.

---

## Architecture

New module `src/retrieve.py` with composable stages rather than one function:

```
dense(query, n)  ─┐
                  ├─► rrf(lists, k=60) ─► rerank(query, cands, n) ─► filter / reorder
bm25(query, n)  ──┘
```

Each stage takes and returns a ranked list of chunk IDs (plus scores), so any variant in the
table above is a different composition, not a different script.

Keep ingestion and query paths separate, as since Week 1: the BM25 index and the dense
embeddings are built at **ingestion** and saved; the query path only loads them.

---

## Decisions already made — don't re-open

- **BGE-M3 + structural chunking is the dense baseline.** Week 2 §11.
- **Metadata is never prepended to indexed text.** Week 2 §1 and §9.
- **The pipeline reads Docling JSON**, not markdown.
- **Match conditions in `eval_specs.py` are frozen** for the original 11. Changing a probe now
  would move the baseline.
- **Generation stays hosted.** No generation calls are needed this week except a handful for
  before/after examples. Keep those on the cheap model.
- **RRF `k = 60`, BM25 defaults.** No hyperparameter tuning on 11 questions.

---

## Open questions for the Week 3 chat

- Does BM25 alone beat dense on any question — and is it the ones predicted?
- Can reranking move Q2 off rank 5 and Q9 off rank 4, or are those chunking/schema problems
  that no retriever reaches?
- Does stemming help or hurt on a compound-heavy language?
- Does the reranker see `skal` vs `bør` where embeddings didn't?
- What does the reranker cost in CPU latency per query?
- Has the Week 2 hypothesis — modality correlates with source document, so metadata filtering
  partly handles it — been tested? If not, it fits here.

---

## Cost

Everything through step 7 is local and free. Step 8 uses a Cohere trial key. Generation for
before/after examples: a few cents. Verify the Anthropic and GCP spend caps are still active
before step 8.

---

## End-of-week checklist

- [ ] Week 2 baseline reproduced locally (MRR 0.768, same per-question ranks)
- [ ] Predictions written before any Week 3 retriever ran
- [ ] BM25 implemented and scored as a standalone retriever, two tokenisation variants
- [ ] RRF fusion written by hand and scored
- [ ] Local multilingual reranker on the fused set, scored, CPU latency measured
- [ ] Cohere Rerank compared on quality and latency
- [ ] Results table + per-question ranks filled in
- [ ] Before/after examples for at least Q2 and Q9
- [ ] `notes/week3-findings.md` written, same shape as Weeks 1–2
- [ ] `requirements.txt` updated (`rank_bm25`, stemmer, reranker deps); repo pushed