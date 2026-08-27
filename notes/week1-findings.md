# Week 1 — findings

Naive RAG pipeline over a Danish public tender (AAU el-installatørydelser, campus
Aalborg/Esbjerg/København). 8–10 PDFs, 166 chunks.

Stack as built: `pypdf` → fixed-size chunks (1000 chars, 200 overlap) → `intfloat/multilingual-e5-small`
→ Chroma (cosine) → top-k → GPT-5.6 Luna.

*Completed 27 August 2026.*

---

## 1. Environment constraint changed the local-first default

Machine has 4 GB total RAM, ~930 MB free in practice. `gemma4:e4b` failed to load
(7.2 GB allocation). BGE-M3 (~2.3 GB) also doesn't fit alongside a generator.

**Substitutions made:**

| Syllabus default | Used instead | Why |
|---|---|---|
| BGE-M3 | `multilingual-e5-small` (~470 MB, 384-dim) | RAM; still genuinely multilingual |
| Ollama local generation | Hosted (GPT-5.6 Luna) | 1B models unusable on Danish |

`gemma3:1b` kept installed as an offline fallback and comparison point.

**Carry into Week 2:** run BGE-M3 in Colab (free tier, ~12 GB) to produce the ceiling
number for the embedding comparison. The Week 2 deliverable is a notebook anyway.

**Carry into Week 7:** full-corpus embedding on 4 GB will be painful. Size the corpus
accordingly, or find a bigger machine first.

### Local generation baseline

`gemma3:1b` on *"Forklar kort forskellen på skal og bør i et udbudsmateriale"* answered
**in Norwegian**, hallucinated *bør* into *bur* (Norwegian for cage), and invented a
branding framework involving coffee. Confident throughout, no hedging.

Three separate failures: language drift (Danish/Bokmål collapse in small models),
weak grip on low-frequency Danish tokens, and pure parametric confabulation.

This is the argument for RAG demonstrated on the target corpus in one prompt. Small
models are far better at *reading supplied text* than at recalling facts.

---

## 2. What `pypdf` does to Danish procurement PDFs

All documents had a real text layer — no silent loss. Short pages were genuinely short
(headings, images). Damage is formatting, not omission:

- **Hard line breaks mid-sentence.** `\n` marks where the *line* ended on the page, not
  the clause. Any newline-based splitter cuts mid-sentence.
- **Hyphenation splits compounds.** `efteruddan-\nnelse`, `anven-\nde`. Typographic
  justification hyphens, not real ones. `efteruddannelse` exists in the index only as two
  fragments that match nothing. Worse in Danish than English because of compounding.
- **Bullet markers glued to words.** `-AAU's`, `•én`. BM25 tokenises on whitespace, so
  `•én` will match nothing in Week 3.
- **Page furniture embedded as content.** `Side 2` opens every page.
- **Image-only pages carry no text.** Anything shown in a diagram is invisible to the
  system. Known limitation — state it in the README.

Deliberately **not** fixed. De-hyphenation is four lines of regex; patching the symptom
would leave Week 2's structure-aware parsing nothing to demonstrate.

---

## 3. The requirements are prose, not tables

`Leverandøren skal sikre, at 15 % af de leverede årsværk udgøres af personer under
oplæring` is a hard mandatory requirement sitting in a paragraph, with no ID and no row.

Two consequences:

- **Week 7 mode 2 can't parse a table.** Every sentence has to be classified. Harder than
  the table case, and more portfolio-relevant — a table-based tender is half-solvable with
  a regex.
- **`skal`/`bør` is the only marker of what binds.** No requirement IDs to fall back on.

The prisliste is an `.xlsx`, deliberately excluded from Week 1 (pypdf only). Docling reads
xlsx — bring it in at Week 2. A Week 7 system that silently ignores the file containing all
the pricing has a hole in it.

---

## 4. Fixed-size chunking severs the parts that carry meaning

Two chunks pulled at random, both broken, in different ways:

> `faglært person med relevant svendebrev og den relevante efteruddan-\nnelse, kursus eller
> certificering til at kunne udføre data-/netværks-/fiberinstallationer…`

**No subject.** Describes a qualification requirement in detail; *who* must hold it was cut
off above. Retrieves well for "hvilke kvalifikationer kræves", then leaves the model to guess
whom it applies to.

> `d bestilling skal AAU fremsende en rekvisition med angivelse af ordrenr., som Leverandøren
> skal anven-\nde i forbindelse med fakturering.`

**No condition.** Opens mid-token (`Ved bestilling`), so the circumstance triggering the
obligation is gone. The `skal` survives; what activates it doesn't. In procurement that's
the dangerous direction.

Keep both strings. The Week 2 before/after on the same content is the writeup.

---

## 5. Embeddings cannot see modality

`multilingual-e5-small`, cosine similarity:

| Pair | Similarity |
|---|---|
| `skal` vs `bør` — same clause, opposite obligation | **0.9966** |
| `skal` vs `skal` — different clauses, same document | 0.9067 |

One word apart, and that word decides whether a clause binds. The vectors are 99.7%
identical. Two genuine obligations sit further apart than a requirement and its optional twin.

Embeddings encode **topic**. Modality is not a topical difference. Neither is identity —
`Bilag 4 §7.2` and `Bilag 7 §4.2` will behave the same way.

Also note the **compressed range**: e5-small pushes Danish text into roughly 0.85–1.00.
Absolute scores carry almost no information; only ordering does.

→ This is the motivation for hybrid retrieval in Week 3. BM25 weights rare exact tokens,
which is precisely what embeddings smooth away.

---

## 6. Retrieval distance does not indicate answerability

Measured across three questions:

| Question | Answerable? | Distance band | Correct chunk rank |
|---|---|---|---|
| Andel årsværk under oplæring | yes | 0.116 – 0.157 | **4** |
| Tekniske krav til installationerne | ambiguous | 0.118 – 0.130 | 3 |
| Krav til kabeldimensionering | **no** | 0.121 – 0.136 | 4 (delegation clause) |

Every distance across all three lands in 0.115–0.158. The unanswerable question's top hit
(0.118) scored *better* than the answerable question's correct chunk (0.132).

**No similarity threshold can separate answerable from unanswerable on this corpus.** That
rules out the obvious abstention mechanism — "refuse if best distance > X" — empirically
rather than by assertion. Week 5 abstention has to come from instructing the model to judge
the retrieved text.

Cause is visible in §5: everything is the same supplier's obligations under the same
contract, so everything is topically similar to everything. The near-duplicate boilerplate
property, as predicted.

**Baseline for Week 3 to beat:** Q2 correct chunk at rank 4 → MRR 0.25. At `k=3` it would
have been missed entirely.

Encouraging side-finding: ranks 2–3 for Q2 returned Bilag 7 — the document `jf. Bilag 7`
points at. Similarity found the cross-referenced document without being told the reference
existed.

---

## 7. Abstention: a controlled pair

Same prompt, same `k=5`, same model. Opposite behaviour.

**Fails** — *"Hvilke tekniske krav gælder for installationerne?"*
Produced 13 bullets of real, correctly-cited, on-topic clauses about change management,
backup and coordination. Nothing fabricated. **Faithful and wrong.** The correct answer was
that Bilag 3 §1 delegates technical requirements to AAU's externally hosted Tekniske
Kravspecifikation.

**Works** — *"Hvilke krav stiller AAU til kabeldimensionering?"*
Two sentences: no requirements in the context, points at the external document, cites the
page. Nothing invented.

**The difference is not the prompt — it's whether the context contains a plausible
alternative.** Question 1 is genuinely ambiguous against this corpus (the specification that
defines the requirements, or the tender's obligations concerning installations), and four
dense chunks support the second reading. Question 2 has no such substitute.

### Two failed interventions, both instructive

**`k=2`** — made it worse. The delegation clause was at rank 3, so it dropped out of context
entirely and the model answered from ABA/AVA procedural clauses alone.
→ **You cannot abstain your way out of a retrieval miss.** No prompt makes a model refuse
based on a clause it wasn't shown. Recall first, then precision, then prompting.

**Sharpened prompt** (explicitly naming the delegation failure) — no change. The model *used*
the delegation clause in bullet one, then continued for 13 more. It satisfied the instruction
and overran it anyway. A third prompt variant would have been fitting the prompt to one test
case.

### Consequence for golden-set design

**Refusal is only testable when no plausible alternative exists in context.** If distractors
can answer a nearby reading of the question, you're measuring the model's interpretation of
your question, not its willingness to abstain.

Split the eval entry in two:
- A true refusal test (`kabeldimensionering`) — expects abstention.
- The ambiguous question — expects the delegation named **first and prominently**, which the
  system already does.

Minor but telling: the model wrote `AAU's til enhver tid gældende tekniske kravspecifikation`
in lowercase — treating a specific named artifact as a general obligation. The mechanism of
the whole failure in one word.

---

## 8. Generation constraints worth remembering

- **Reasoning models reject `temperature`.** Locked at 1; `temperature=0` returns a 400.
  Same family renames `max_tokens` → `max_completion_tokens`.
- **So generation is non-deterministic.** Harmless for extracting a figure; a problem for
  measurement. Week 6 options: run each eval question 2–3× and treat the spread as the noise
  floor, or use a non-reasoning model where determinism matters more than answer quality.
- **`passage:` / `query:` prefixes are not optional** for the e5 family — asymmetric, and
  omitting them degrades retrieval silently. BGE-M3 uses no prefixes. Check every model card
  on swap.
- **Chroma defaults are traps.** Default distance is squared L2, not cosine. Default
  embedding function is `all-MiniLM-L6-v2`, English-trained, and will embed Danish without
  complaint or warning. Both set explicitly.

---

## Carried forward

| Finding | Lands in |
|---|---|
| Hyphenation splits compounds; bullets glued to words | W2 parsing, W3 BM25 tokenisation |
| Chunks lose subjects and conditions | W2 structure-aware chunking |
| Requirements are prose, no IDs | W7 mode 2 design |
| `skal`/`bør` invisible to embeddings (0.9966) | W3 hybrid retrieval |
| Distance carries no answerability signal | W5 abstention, W6 threshold design |
| Q2 correct chunk at rank 4 (MRR 0.25) | W3 baseline to beat |
| Refusal untestable when distractors are on-topic | W6 golden-set design |
| Non-deterministic generation | W6 eval methodology |
| BGE-M3 doesn't fit locally | W2 (run in Colab) |
| `.xlsx` prisliste excluded | W2 (Docling reads xlsx) |
