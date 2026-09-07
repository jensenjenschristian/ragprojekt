# Week 2 — findings

Parsing, chunking, metadata and embeddings over the same corpus as Week 1 (AAU
el-installatørydelser). Read alongside `notes/week1-findings.md`, which this measures against.

*In progress. Started 3 September 2026.*

---

## 1. The eval set was built before any comparison ran

`notes/eval-questions.md` went from 3 entries to 10, each with question, expected answer,
exact source document and page, and what it tests. Deliberately written **before** running
any chunking or embedding comparison — questions written after seeing results get fitted to
the results.

Coverage: factual lookup, ambiguous-delegation, two true refusals, cross-reference,
near-duplicate trap, compound noun, modality, rare-token retrieval, and one question that is
currently unanswerable and should flip once the xlsx is ingested.

Two entries were corrected after reading the source rather than trusting a grep hit, and
both corrections are worth recording.

**Q4 was ambiguous, not a refusal test.** Originally *"Hvad kræver Sikkerhedscirkulæret af
leverandøren?"* — but `Aftale.pdf` p8 contains two obligations *relating to* the circular, so
a plausible answer exists in context. That's the same defect Week 1 §7 identified in the
tekniske krav question: refusal is only testable when no plausible alternative exists.
Narrowed to ask what the circular itself defines (classification levels, handling
requirements), which the corpus demonstrably lacks. The positive version became Q10.

**Q6's two copies are byte-identical.** I had assumed the secondary-supplier passage differed
between `Aftale.pdf` p4 and `Udbudsbetingelser.pdf` p4. Reading both: the three bullets are
word-for-word identical, and the apparent differences were line-wrap positions only. This
makes the trap *harder*, and it is the sharpest available argument for the schema work — see
§4 below.

### Method note: metadata contaminated the corpus statistics

The corpus dump (`dump_text.py`) writes tab-separated `source \t page \t text`. Searching
whole lines counted filename tokens as content: `samarbejdspartnere` appeared to occur 181
times, which is the line count of `Bilag 5 - Vejledning til eksterne samarbejdspartnere -
version august 2024.pdf`, not a term frequency. Corrected by extracting field 3 first
(`cut -f3`).

Trivial as a scripting slip; not trivial as a preview. It is exactly what happens if
document/appendix metadata is prepended to chunk text before embedding — a common tutorial
recommendation. The filename tokens then appear in every chunk of that document and BM25
treats them as ordinary content in Week 3. **Decision: metadata stays in metadata fields.**

---

## 2. Docling vs pypdf, measured on the corpus's worst-extracted document

Docling runs a layout model over a rendered image of each page, classifying regions
(heading, paragraph, list item, table, furniture) and inferring reading order from geometry.
pypdf returns the PDF's text operators in emission order with no structure. That difference
is the point: a text stream cannot populate a `section` metadata field because nothing in it
marks a heading.

Tested at `do_table_structure=False`, `do_ocr=False` (all documents have a real text layer —
Week 1 §2).

### Three of the four Week 1 §2 defects are fixed structurally

| Week 1 defect | Status | Evidence |
|---|---|---|
| Hyphenation splitting compounds | **Fixed** | `Aftale.pdf` p10 clean; `refe-\nrenceprisliste` now whole |
| Hard line breaks mid-sentence | **Fixed** | Paragraphs emitted as continuous blocks |
| Bullet markers glued to words | **Fixed** | `- du rydder op efter dig` as proper list items |
| `Side N` page furniture | **Fixed** | Routed to Docling's furniture layer, out of reading order |

`Bilag 5` had the worst pypdf extraction in the corpus — bullets breaking **mid-word**, no
hyphen involved:

| pypdf | Docling |
|---|---|
| `• du r` / `ydder  op efter  dig` | `- du rydder op efter dig` |
| `• al` / `t affald sorteres` | `- alt affald sorteres` |
| `• H` / `vor du ringer fra` | `- Hvor du ringer fra` |

So `rydder` existed in the Week 1 index only as `r` and `ydder`, matching nothing. Same
class of loss as the hyphenation case but caused differently, and invisible until the
documents were read directly.

Furniture removal generalises across formats: `Side N` in `Aftale.pdf` and
`Rev. August 2024 N` in `Bilag 5` were both dropped without configuration. Note this also
removes the `Side 4` that pypdf placed *inside* the Q6 passage, between the intro sentence
and the bullet list.

Headings are classified rather than inferred — `## Vi forventer at`, `## ULYKKE OG BRAND`,
`## Underskriftsforhold`. This is what makes step 4 possible.

### Two residual issues, both to be handled as documented post-processing

**Letter-spacing in the source.** `t  i  l skade` (`til`). The characters are genuinely
positioned apart in the PDF, so no reading-order model recovers it. A source defect, not a
parser defect. Needs a normalisation pass; per the Week 2 plan this stays a **documented
post-processing step, not a hidden regex**.

**Over-joining across layout columns.** Two separate lines merged into one paragraph:

> `Alarmcentralen - I tilfælde af ulykke eller brand skal du ringe til 1-1-2 Politiet - har du
> brug for at kontakte politiet skal du ringe 1-1-4`

The reading-order model resolved ambiguous two-row geometry by concatenating. Worth naming
the direction of the error: **pypdf split things that belonged together; Docling
occasionally joins things that don't.** For retrieval, over-joining is the safer failure —
this chunk still answers "hvilket nummer ringer jeg til ved brand", whereas Week 1 §4's
severed subject (`faglært person med…`) answered nothing correctly. A dangerous failure mode
traded for a benign one.

---

## 3. Docling does not fit on this machine — parsing moves to Colab

| Document | Pages | Table structure | Peak RSS | Time |
|---|---|---|---|---|
| Tro- og loveerklæring | 1 | off | 847 MB | 33.1 s |
| `Bilag 5` | 6 | off | **1235 MB** | 29.6 s |

Available headroom: **~930 MB**. Exceeded on a 6-page document with TableFormer still
disabled; `Aftale.pdf` is 17 pages. Post-conversion RSS fell to 462 MB, so memory is released
afterwards — the run completed because Windows paged to disk, not because it fit.

This is rung 3 of the Week 2 plan's mitigation ladder, reached on measurement rather than
assumption. **Parsing runs in Colab and the extracted output is committed.** Legitimate
rather than a compromise: parsing is ingestion, it runs once, and the result is a file.

Convenient consequence: step 6 already required Colab for BGE-M3 (~2.3 GB). One notebook now
covers parsing *and* the embedding comparison, which is the Week 2 deliverable anyway.

**Dependency note.** `pip install docling` pulled PyTorch into the local venv, which will now
never parse anything. Keep parsing dependencies in a separate `requirements-parsing.txt` so
the main `requirements.txt` doesn't make anyone cloning the repo download PyTorch to run a
pipeline that doesn't parse locally.

---

## 4. Corpus findings that constrain the schema

Three things surfaced while building the eval set that bear directly on step 4.

### Modality correlates with document and actor

Every genuine `bør` in the corpus is in `Udbudsbetingelser.pdf`, addressed to
**tilbudsgiver**, about preparing a tender. Every `skal` found so far is in `Aftale.pdf`,
`Bilag 3` or `Bilag 7`, addressed to **Leverandøren**, about performing the contract. This
reflects the two-phase structure of a procurement: tender conditions advise a bidder who has
won nothing; contract terms bind a supplier who has.

Week 1 §5 established that embeddings cannot see modality (0.9966 cosine). If modality is
substantially predictable from the source document, **metadata filtering partially addresses
it without any retrieval change** — a hypothesis testable this week rather than an assertion.

*(Note the initial grep was unbounded and matched `børnearbejde`. Use `grep -w` on Danish;
short words are buried inside compounds constantly.)*

### Modality is not a two-word binary

`Udbudsbetingelser.pdf` p12, four lines, three levels:

- `Tilbudsgiver **bør** nøje overveje` — advisory, to the bidder
- `AAU **er berettiget til** at afvise` — discretionary right
- `AAU **er forpligtet til** at afvise` — binding obligation

`skal`/`bør` is the marker noticed first, not the whole system. A `skal`-scanner fails twice
on this passage: it flags `om tilbuddet **skal** indeholde forbehold` (an ordinary
subordinate modal, not an obligation) and misses `er forpligtet til` (the real one). Q10's
security obligation is a second `er forpligtet til` with no `skal` anywhere in the clause.

Stakes are inverted relative to grammar: the *advisory* clause carries the harshest
consequence in the passage, since ignoring it gets the bid rejected. **Direct constraint on
Week 7 mode 2** — modality is not recoverable from surface form.

### Only metadata can separate the Q6 near-duplicates

The secondary-supplier passage is verbatim identical in `Aftale.pdf` p4 (binding) and
`Udbudsbetingelser.pdf` p4 (describes the procurement, does not bind).

No embedding separates them — same string. No reranker separates them — a cross-encoder sees
identical text against the same query. No BM25 separates them — identical tokens. **The
`source` field is the sole available discriminator.** If Week 2's schema gets this right, Q6
is answerable; if not, nothing downstream rescues it. This is the strongest available
argument that schema design does work usually attributed to a smarter retriever.

`Udbudsbetingelser.pdf` p4 also uses `aktør` and `leverandør` interchangeably for the same
party in the same section — a Week 3 synonym/lexical-gap case.

---

## 5. Two corpus-curation problems

### A cross-reference points at the wrong appendix

`Bilag 3 - Kravspecifikation.pdf` p2 cites `vejledning til eksterne samarbejdspartnere
(bilag 6)`. Bilag 6 is the situationsplaner. Three sources agree the vejledning is **Bilag 5**
(`Aftale.pdf` p3 and p17, `Udbudsbetingelser.pdf` p6), and the filename confirms it.

Step 4 plans to treat appendix references as addressable structure. Here one doesn't resolve
— a system following `(bilag 6)` literally lands on a map of Aalborg Øst. Mild, since a human
corrects it instantly from context, but the principle matters: **appendix references are
claims about structure, not structure itself**, and may need validating against the actual
document set.

### Four documents produce text that survives extraction and means nothing

`Bilag 6A–6D` (situationsplaner) are CAD exports, not scans — they have a real text layer,
which is why 6A is the largest PDF in the corpus. The text is building identifiers and street
labels: `Fib 11`, `Kst 7`, `Pon 109Pon 107`, `ANVAlfred Nobels Vej`, `1 : 4500
SITUATIONSPLAN`.

A distinct failure from Week 1 §2's "image-only pages carry no text" — arguably worse, since
these chunks are in the index, can occupy top-k slots, and will tokenise into BM25 in Week 3.
They can never answer a question.

Also explains the near-duplicates found earlier: `REV. DATO:06.11.2025` (6A, 6B, no space)
vs `REV. DATO: 06.11.2025` (6C, 6D, with space), and repeated street labels *within* 6B —
not cross-document boilerplate as first read.

**Open decision for step 4:** exclude the situationsplaner from the index with a documented
rationale. Four documents of pure noise, and deciding what the model should see before it
answers is the substance of the course.

Incidental: `Bilag 6A` p1 contains `E:\000 Terræn\Situationsplaner\Situationsplan 2024\AAU
Aalborg Øst - Situationsplan.dwg` — an internal filesystem path from AAU's drawing office,
published in a public tender. Harmless here; a concrete instance of the Week 8 point that
tender documents are untrusted content.

---

## Carried forward

| Finding | Lands in |
|---|---|
| Docling fixes hyphenation, line breaks, bullet gluing, furniture | W2 chunking, W3 BM25 |
| Letter-spacing needs documented normalisation | W2 post-processing |
| Docling over-joins across columns; benign vs pypdf's splitting | W2 chunking evaluation |
| 1235 MB peak on 6 pages, ~930 MB available | Parsing in Colab, W3 machine switch |
| Metadata must not be prepended to embedded text | W2 schema, W3 BM25 |
| Modality correlates with document and actor | W2 metadata filtering test |
| Three modality levels, `skal`-scanner fails both ways | W7 mode 2 |
| Q6 separable only by `source` metadata | W2 schema — the test that matters |
| `aktør` / `leverandør` used interchangeably | W3 lexical gap |
| Bilag 3 cites the wrong appendix | W2 schema, W7 cross-reference resolution |
| Situationsplaner produce meaningless indexable text | W2 corpus curation |