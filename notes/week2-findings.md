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

### Three residual issues, all to be handled as documented post-processing

**Letter-spacing in the source.** `t  i  l skade` (`til`), `Der f  indes` (`findes`). The
characters are genuinely positioned apart in the PDF, so no reading-order model recovers it.
A source defect, not a parser defect, and systematic in `Bilag 5` rather than a one-off.
Needs a normalisation pass; per the Week 2 plan this stays a **documented post-processing
step, not a hidden regex**.

**Over-joining across layout rows.** Two separate lines merged into one paragraph:

> `Alarmcentralen - I tilfælde af ulykke eller brand skal du ringe til 1-1-2 Politiet - har du
> brug for at kontakte politiet skal du ringe 1-1-4`

The reading-order model resolved ambiguous two-row geometry by concatenating.

**Splitting a paragraph mid-phrase.** On the same page as the correctly-repaired bullets:

> `Færdselsoven gælder overalt på campus. Færdsels- og parkeringsskilte er opsat i`
> *(blank line)*
> `samarbejde med politiet. Der f  indes parkeringspladser overalt omkring universitetet…`

A paragraph break inserted mid-prepositional-phrase, and then the following sentence boundary
lost — the break landed in the wrong place *and* merged what came after.

This is the **dangerous** direction, and it revises the tidy version of the pypdf/Docling
comparison. Docling does not simply err toward joining: it splits too, and
`Færdsels- og parkeringsskilte er opsat i` is Week 1 §4's failure mode reappearing — a
fragment that retrieves plausibly having lost what completes it. Over-joining
(`Alarmcentralen`) is benign because the merged chunk still answers the question;
under-joining is not.

**Hypothesis, untested.** `Færdsels- og parkeringsskilte` is a suspended compound — a real
lexical hyphen awaiting the head noun, common in Danish administrative prose and rare in
English. Docling correctly declined to de-hyphenate it, but the layout model may have read
the same line-ending hyphen as a block boundary. If so it is a Danish-specific interaction
with a model trained largely on English documents. Testable by grepping the Docling output
for other `X- og Y` constructions and checking whether breaks cluster near them.

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

## 6. Tables: what TableFormer gets right, and how it fails silently

Table structure was enabled for the Colab parse (RAM no longer a constraint). Ten documents,
all parsed successfully. The tables are where the interesting behaviour is.

### It works where it matters

`Udbudsbetingelser.pdf` p5 — the delaftale values — extracted cleanly:

| | Samlet værdi |
|---|---|
| Delaftale Aalborg | 35 mio. kr. |
| Delaftale Esbjerg | 4,2 mio. kr. |
| Delaftale København | 16,1 mio. kr. |

Under pypdf this was undifferentiated text. It is now a retrievable fact — see Q11.

### A table of contents is not a table

Eleven `MatchingPostProcessor` warnings fired during the run, all on one 21×2 table:
`Udbudsbetingelser.pdf` p2, the **table of contents**. Dot-leader typography — label, run of
periods, page number, positioned by tab stops — geometrically resembles a two-column grid, so
TableFormer detected one, then could not place cells that did not fit its inferred rows.

Damage from row 11 onward: entries duplicated across both columns, one entry's trailing
leader landing in another's cell, and `12.2 Udvælgelse` colliding with `13. Tilbudsfasen` and
`13.1 Tilbudslisten` in a single cell.

Substantively harmless — a navigation aid whose page numbers are wrong in the extraction and
irrelevant to retrieval. But that is luck, not design.

### The failures are invisible downstream

The warnings appeared in the Colab log and **nowhere in the JSON**. Cells recovered by
nearest-row fallback — one moved 95.7 points — are stored identically to cells matched
confidently. A consumer reading `data-parsed/` cannot distinguish them.

Had the 21-row table been the tidsplan rather than the ToC, a misplaced deadline would have
looked exactly as authoritative as it does now.

**This is the first point in the course where a model made a silent judgement call about the
data.** pypdf never guessed; it returned what was in the file, badly. Docling guesses well and
does not say so. Consequence for step 4: capture parse-time warnings into the output, or at
minimum commit the parse log alongside the JSON. A table that triggered orphan recovery
deserves lower confidence than one that did not, and right now that information exists only in
a cell output.

### Tables split at page breaks

The tidsplan runs from `Afsendelse af udbudsbekendtgørelse` to `Kontraktstart`, crossing the
p6/p7 boundary. TableFormer works per page, so it became two tables — 8 rows on p6, 5 rows on
p7 — and **the continuation has no header**. In isolation the p7 table is five dates:
`Uge 45`, `Uge 45`, `Uge 46-47`, `Uge 48`, `1. december 2026`. Nothing says what they are.

Same shape as Week 1 §4's severed subject: a chunk that retrieves plausibly for a date query
having lost the frame that gives it meaning. Except here the parser did nothing wrong — the
*page* is the boundary that breaks it. Structure-aware chunking has to reason across page
boundaries, not just within them. Week 1's chunker was fixed-size and within-page only.
Recorded as Q12.

### Chunk from the JSON, not the markdown

The markdown export renders a header row for every table. The JSON says otherwise —
`column_header: False` on all cells of the tidsplan, `start_row_offset_idx: 0` on the first
data row. Docling correctly determined the table has no header; **Markdown's table syntax
cannot express a headerless table**, so the exporter invents one.

Markdown also discards `column_header` flags and per-element page provenance. Provenance is
the ground truth for every metric in Weeks 2 and 6.

**Decision: the pipeline reads JSON. Markdown is kept for human inspection only.** Cleanest
instance so far of the week's thesis — the information was there, and the convenient
representation threw it away.

Practical consequence: row 0 of a headerless table is data, so a chunker that skips it drops a
real row. The header must come from the heading Docling classified *above* the table — the
same mechanism that populates `section` in the schema, so tables and prose share one solution.
That also rescues the split tidsplan: with a section heading attached, the p7 continuation
stops being five orphan dates.

---

## 7. The xlsx: Q9 flips, and the corpus's hardest retrieval trap appears

`Bilag 4 - Tilbudsliste.XLSX` parsed in 0.5 s — no layout model needed, the file is already
structured. It contains 36 tables in a repeating twelve-table pattern, three times over: one
sheet per delaftale (Aalborg, Esbjerg, København).

### Q9 flips from unanswerable to answered

`Udkaldstillæg i kr. (gna. timepris x 3)` — **1.728 kr.** for Aalborg and Esbjerg, 1.848 kr.
for København. Under pypdf, `Aftale.pdf` p7 established that the surcharge existed and the
file defining it was invisible. This is the measured before/after that justifies step 3, not
an assertion that the xlsx "should" be included.

### Q7's missing parameter was in the spreadsheet

`Tilbudsgivers faste rabatsats på materialer iht. referenceliste — 0.38`. The Aftale p10
clauses repeatedly reference "den tilbudte rabatsats" without stating it. Q7 is therefore a
cross-document, cross-format question: the rule is in a PDF, the parameter in a spreadsheet,
neither complete alone.

Note the terminology shift — `Aftale.pdf` says `referenceprislisten`, `Bilag 4` says
`referenceliste`. Same object, different compound. Week 3 lexical gap.

### Three sheets, two of them byte-identical: the hardest case in the corpus

| Kategori | Vægtning | Aalborg | Esbjerg | København |
|---|---|---|---|---|
| Lærling | 0,1 | 350 | 350 | 350 |
| Tekniker | 0,3 | 650 | 650 | **700** |
| Elektriker svend | 0,5 | 500 | 500 | **550** |
| El-installatør | 0,08 | 900 | 900 | 900 |
| Programmør | 0,02 | 1200 | 1200 | 1200 |
| **Gennemsnitstimesats** | 1 | **576** | **576** | **616** |

Aalborg and Esbjerg are identical. København differs in **two cells of fifteen**.

Embeddings cannot separate them: the discriminating tokens are bare numbers in an otherwise
identical passage. BM25 cannot either — fourteen of sixteen tokens are shared. The only
discriminator is the sheet title (`Bilag 4 - Tilbudsliste for delaftale X`), which sits twelve
tables away in the parsed structure and is **absent from the chunk**.

**Worse than Q6.** There, retrieving the wrong copy gives the correct fact with the wrong
citation. Here it gives *a different number*. Without `delaftale` as a metadata field, a
pricing question has a one-in-three chance of being right and no way to signal which.
Recorded as Q13. This is the schema argument in its most concrete form.

### The gennemsnitstimesats is not a price

`(Tilbudsprisen anvendes kun ifm. beregning af tildelingen på aftalen. Der afregnes efter
medgået tid og sats for given kategori på den konkrete opgave)`

576 is a weighted average used **only to score bids**. Invoicing is per category at the
category's rate, within normal hours (07.30–15.30). A system reporting 576 as "the hourly
rate" would be confidently wrong, and the qualification that says so is a parenthetical in
the row below the number.

### Numeric normalisation has three distinct cases

- **Float artifacts.** `172.79999999999998` — IEEE 754, not a parse defect. 576 × 0.3 has no
  exact binary representation; Excel rounds for display, the stored value is this.
- **Decimal separator.** Extraction yields `.`; Danish prose throughout the corpus uses `,`.
- **Fraction vs percentage.** `0.38` and `0.1` in cells, `(30%)` in labels. A user queries
  "38% rabat"; the index holds `0.38`.

All three break exact-token matching in Week 3 — the index holds forms nobody will query. Same
class as the compound-noun problem. Belongs in the documented post-processing pass alongside
the letter-spacing fix, **not** in the parser.

### The 1×1 "tables" are section headings

Eighteen of the 36 tables are single cells: `Tillæg til timepriser`, `Materialepriser`,
`Timepriser ifm. opgaver (inden for normal arbejdstid kl. 7.30-15.30)`. Read in sequence they
are the sheet's structure — the spreadsheet equivalent of the headings Docling classifies in
prose.

Initially read as noise to filter. They are not: they are exactly the context the adjacent
tables need, and the normal-hours qualifier above only exists because of one. Treat as section
context, not as chunks.

---

## 8. A recurring methodological error, recorded because it cost three times

Three times this week an inspection artifact was mistaken for a data problem:

1. **`samarbejdspartnere` at 181 occurrences** — searching whole tab-separated lines counted
   filename tokens as content. Fixed with `cut -f3`.
2. **Fabricated table headers** — the markdown export invented a header row; the JSON was
   correct all along.
3. **A "truncated" cell** — `(Tilbudsprisen anvendes kun ifm. beregning af` looked like an
   xlsx ingestion limit. It was a `[:45]` slice in the inspection code. The full 151-character
   string was in the JSON throughout.

Each time a lossy *view* was introduced for readability and then reasoned about as if it were
the data. Case 2 is the same error at pipeline scale, which is why the JSON decision in §6
matters beyond convenience.

**Rule for the rest of the course: when something looks damaged, check whether the inspection
is damaging it before concluding anything about the data.**

---

## Corpus curation: what should not be indexed

Three categories of extracted-but-useless content have surfaced. All are decisions for step 4,
documented rather than hidden.

| Content | Why exclude | Note |
|---|---|---|
| `Bilag 6A–6D` situationsplaner | CAD exports; text is building IDs and street labels (`Fib 11`, `ANVAlfred Nobels Vej`) meaningful only by position | Can occupy top-k, will tokenise into BM25 |
| Table of contents, `Udbudsbetingelser.pdf` p2 | Navigation artifact; extraction is damaged and page numbers unreliable | Dot leaders are pure BM25 noise |
| — | — | The xlsx 1×1 headings were initially in this list. They are not noise; see §7. |

The parser's job is to extract everything. **Deciding what belongs in the index is a separate
decision, and Week 2 is where it gets made.**

--

## Carried forward

| Finding | Lands in |
|---|---|
| Docling fixes hyphenation, line breaks, bullet gluing, furniture | W2 chunking, W3 BM25 |
| Letter-spacing needs documented normalisation | W2 post-processing |
| Docling over-joins across rows (benign) and splits mid-phrase (dangerous) | W2 chunking evaluation |
| Suspended compounds (`X- og Y`) may trigger false block breaks | W2 parsing check, W3 Danish handling |
| 1235 MB peak on 6 pages, ~930 MB available | Parsing in Colab, W3 machine switch |
| Metadata must not be prepended to embedded text | W2 schema, W3 BM25 |
| Modality correlates with document and actor | W2 metadata filtering test |
| Three modality levels, `skal`-scanner fails both ways | W7 mode 2 |
| Q6 separable only by `source` metadata | W2 schema — the test that matters |
| `aktør` / `leverandør` used interchangeably | W3 lexical gap |
| Bilag 3 cites the wrong appendix | W2 schema, W7 cross-reference resolution |
| Situationsplaner produce meaningless indexable text | W2 corpus curation |
| TableFormer fallback is invisible in the JSON | W2 schema — capture parse warnings |
| ToC misdetected as a table | W2 corpus curation |
| Tables split at page breaks lose their header | W2 chunking across pages |
| Pipeline reads JSON; markdown is inspection only | W2 chunking, all downstream |
| Q9 answerable only after xlsx ingestion | W2 before/after evidence |
| Three delaftale sheets, two byte-identical | W2 schema — `delaftale` must be a field |
| Gennemsnitstimesats is an evaluation figure, not a price | W7 mode 2 |
| Float artifacts, decimal separators, fraction vs percentage | W2 post-processing, W3 BM25 |
| Inspection artifacts mistaken for data problems, ×3 | Method, all weeks |