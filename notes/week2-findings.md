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

## 9. The document schema

The architectural decision of the week. The plan targeted document / appendix / §-path /
page; the corpus forced three additions, each traceable to a specific eval question.

### The corpus has real §-numbering

An open question from the Week 2 plan: does the tender have §-numbering consistent enough to
build a path from, or is heading hierarchy the only usable structure? Answer: it has
numbering, and Docling captured it.

`Aftale.pdf` has 47 section headers, `Udbudsbetingelser.pdf` 32, in consistent dotted-decimal
form — `3.1 Aftalens omfang`, `6.4 Afregning af materialeforbrug`, `10.3 Ophævelse af Aftalen`.
Three caveats:

- **The number is inside the heading text**, not in a field. Splitting it out is a regex you
  own: `^(\d+(?:\.\d+)*)\.?\s+(.*)$`.
- **`level` is 1 on every heading.** Docling produced no nesting. The tree comes from the
  numbering itself — `6.4` is a child of `6` because of its dots. Arguably better: the
  document's own numbering is more reliable than inferred visual hierarchy.
- **The appendices have headings but no numbers.** `Bilag 7` has 5 headings, none numbered.
  So `section` is populatable everywhere; `section_path` only in the two main documents. The
  schema must tolerate a null path rather than assume one.

### A §-path is not a unique key

`Udbudsbetingelser.pdf` p11 has **two sections numbered 12.2** — `12.2 Udvælgelse` and
`12.2 Dokumentation`. Confirmed in both the heading list and the (separately damaged) ToC, so
it is a numbering error in the source, not a parse artifact.

Together with the `Bilag 3` → `(bilag 6)` misreference in §5, the same lesson from two
directions: **the document's structural claims are usable but not trustworthy.** Treat the
§-path as an addressing aid, not an identifier.

### Reading order comes from `body`, not from the arrays

`texts` and `tables` are separate arrays. Interleaving them by array position is wrong.
`body.children` holds JSON Pointer refs (`{'$ref': '#/texts/12'}`) in true reading order, and
walking those is what makes heading-to-table attachment work.

The xlsx nests one level deeper: `body.children` holds three `#/groups/N` refs, one per
sheet, each with 12 table children. The group `name` carries the sheet name
(`Tilbudsliste - Aalborg`) — structural metadata, better than regexing a delaftale out of a
cell. The walk has to recurse.

### The schema, and why each field exists

| Field | Justification |
|---|---|
| `text` | — |
| `source` | Q6 — the byte-identical secondary-supplier passage |
| `page` | ground truth for every eval question |
| `section` | retrieval by address; the header for split tables |
| `section_path` | sortable §-hierarchy; null in unnumbered appendices |
| `subsection` | unnumbered headings — Q10's obligations sit under `Særligt vedr. sikkerhed` |
| `delaftale` | Q13 — where the wrong sheet returns the wrong number |
| `element_type` | filter tables in or out; know when text came from a cell |

Populated by a single walk carrying section state, which is reset by a numbered heading and
inherited by everything after it. Headings are consumed as metadata, not emitted as chunks.

Page furniture is dropped by **label** (`page_footer`), not by matching `Side \d+`. Verified:
16 footers in `Aftale.pdf`, all `Side 2`–`Side 17`, no clause misrouted. Dropping by label
generalises to `Rev. August 2024 N` in `Bilag 5` without a second rule.

### Three questions became answerable through metadata alone

**Q10 — subsection state carries across pages.** The security obligations on p7 and p8 both
carry `section_path: 5`, `subsection: Særligt vedr. sikkerhed`.

**Q12 — the split tidsplan.** Both fragments carry `section: 7. Tidsplan`. The p7
continuation was five bare dates (`Uge 45`, `Uge 46-47`, `Uge 48`, `1. december 2026`) with no
header, because TableFormer works per page. **No table-specific code was needed** — the same
heading-state mechanism that handles prose handles the split table.

**Q13 — three delaftale sheets.** `Elektriker svend` now returns three chunks: Aalborg 500,
Esbjerg 500, København 550, each tagged with its delaftale.

**Q6 — two discriminators where there were none.** The identical passage now carries
`Aftale / 3.1 Aftalens omfang` versus `Udbudsbetingelser / 2. Udbuddets genstand`. The section
names are themselves informative: one is the contract defining its scope, the other the tender
describing what is procured.

**No retriever could have done any of this.** Q13's three chunks are the same string apart from
two digits — identical embeddings, fourteen of sixteen tokens shared. The distinction came
entirely from schema design: a group name and a state variable. This is the week's thesis
demonstrated rather than asserted.

### Curation, implemented as `exclude=True`

601 elements after exclusions, from 691 before. 90 removed:

- **88 from the four situationsplaner** — 13% of the corpus, all of it noise.
- **2 tables of contents**, caught by a structural rule rather than a page number: a table
  with `section is None` precedes the first heading and is therefore front matter. Precise —
  it caught the `Udbudsbetingelser` ToC (2885 chars, by far the largest table) and a second
  ToC in `Aftale.pdf` p2 that had not been noticed, and nothing else.

The flag matters. Being able to run `exclude=False` makes this a measurable decision rather
than an assertion.

### Known limitations

- `Bilag 4`'s `Materialepriser` and `Tilbudsevaluering` chunks inherit the wrong section,
  because those headings sit in the first cell of their own table rather than as separate
  1×1s. Misleading — `Tilbudsevaluering` under `Tillæg til timepriser` is the evaluation
  table, not a surcharge. No eval question depends on it.
- `Bilag 6B` and `6D` lost most elements in the walk (35→15, 15→1). Unexplained. Irrelevant
  now they are excluded, but recorded rather than shrugged at.

---

## 10. Chunking: three strategies, and the surprise is which finding survives

Week 1 used 1000-character chunks with 200 overlap. Characters are the wrong unit — the
model's limit is in tokens.

### Token statistics for the corpus

Measured with `multilingual-e5-small`'s own tokenizer, on 601 elements:

| | tokens |
|---|---|
| min | 3 |
| median | **33** |
| p90 | 83 |
| max | 463 |
| over 512 | **0** |

**4.03 characters per token** — top of the 3–4 range the plan estimated. Week 1's
1000-character chunks were therefore ~248 tokens, targeting roughly half of a 512 budget
without knowing it.

Median 33 means chunking here is a **grouping** problem, not a splitting one — the opposite of
Week 1. Nothing exceeds e5's 512-token limit, so no silent truncation. (That limit is a real
hazard: e5 will embed a 600-token string and discard the tail without warning.)

### The 55 elements under 8 tokens

Three kinds, needing no special handling because grouping absorbs them: form-field labels
(`Navn :`, `EAN-nummer`, `Fakturanummer` — individually empty, collectively a real invoicing
requirement), title-page fragments (`mellem`, `og`, `(`, `)` — the layout model split a
parenthetical into three elements), and one genuine defect (below).

`Bilag 1 :` and `Bilag 2 :` in the bilagsfortegnelse confirm those appendices are genuinely
absent from the corpus rather than a download oversight.

### A hypothesis tested and rejected

§2 recorded a hypothesis that Danish suspended compounds (`Færdsels- og parkeringsskilte`)
confuse Docling's de-hyphenation, since they are common in Danish administrative prose and
rare in English.

Tested across the corpus: **ten chains found, nine handled correctly.** One missed join —
`administrations-, undervisnings-, værksteds- og labora-` + `toriebygninger`, so
`laboratoriebygninger` exists only as two fragments. One over-join in the other direction —
`nød- og` became `nødog` in `Bilag 3` p4, producing a token that matches nothing.

Two isolated defects, opposite directions, one instance each in 601 elements. **The hypothesis
does not survive the data.** Docling's hyphenation handling is essentially reliable here.

Post-processing: the join rule (element ends in `-`, next starts lowercase) is safe and worth
adding. `nødog` is not worth a rule — one instance does not justify machinery that could
damage real compounds.

### The three strategies

| Strategy | Chunks | Median | Max |
|---|---|---|---|
| Fixed (250/50, tokens) | 123 | 250 | 252 |
| Recursive (350/50, element-bounded) | 83 | 323 | 461 |
| Structural (400, section-bounded) | 113 | 204 | 461 |

Structural produces **more** chunks than recursive despite a larger budget, because sections
are frequently smaller than the budget and it emits at the boundary rather than packing on.
That is the tradeoff numerically: more coherent chunks, less dense. Smaller chunks mean less
distractor text diluting the embedding but also less context to answer from.

### The Week 1 severed chunks are fixed — but not by chunking

Both `week1-findings.md` §4 defects are resolved in **all three** strategies, fixed-size
included:

> `'Tekniker' = faglært person med relevant svendebrev og den relevante efteruddannelse…`

The severed subject was a definition in a category list; Week 1's cut landed inside it. And:

> `Ved bestilling skal AAU fremsende en rekvisition med angivelse af ordrenr.…`

`Ved` intact, condition restored.

**The credit belongs to Docling, not to chunking strategy.** pypdf's text stream had no
boundaries to respect, so a cut at character 1000 landed mid-token. With structured elements,
even a naive chunker cuts at element joins. The chunking comparison has to rest on different
evidence — which the same output supplies.

### Recursive chunking's failure mode is silent citation error

The severed-condition probe landed differently across strategies:

| Strategy | Section reported |
|---|---|
| Fixed | `None` |
| Recursive | `7.1 Fakturering af opgaver baseret på tidsforbrug…` |
| Structural | `7.3 Generelt om fakturering` |

Structural is correct — the clause is in 7.3. Recursive packed content across the section
boundary, so its chunk *starts* in 7.1 and *contains* 7.3 material, and takes its label from
the first element. **A confident incorrect citation, which is worse than fixed-size's honest
`None`.**

Fixed-size cannot cite at all. Concatenating a document before slicing destroys per-element
provenance, so a fixed chunk has no single page and no section. Recorded rather than patched:
the baseline's inability to cite is part of what the comparison shows.

Same class as everything else this week — TableFormer's fallback cells, the markdown
exporter's fabricated headers, the `[:45]` slice. Plausible output with no marker that it is
wrong.

### Short structural chunks: mostly fine, one real issue

12 chunks under 50 tokens (p10 = 43). Seven are genuinely short contract clauses —
`17. Overdragelse` at 32 tokens is complete as written. Five are form scaffolding.

The problem is three near-identical 20-token chunks: `Bilag 4 - Tilbudsliste for delaftale
X` + `Grønne felter skal udfyldes af tilbudsgiver`, one per sheet. A fourth near-duplicate
cluster, and prime candidates to win a query about the tilbudsliste while containing no
pricing. Worse, the `Grønne felter` instruction — which says the figures are bidder-supplied
and therefore qualifies how to read 1728 and 500 — is now isolated from the tables it
describes.

**Not fixed.** A merge rule that helped here would be fitted to one case, which is the trap
`week1-findings.md` §7 recorded with the third prompt variant. Revisit if retrieval evaluation
shows title chunks displacing real answers.

--

## 11. The comparison: chunking beats the embedding model

Nine configurations — three chunking strategies × three embedding models — scored on the 11
retrieval questions from `eval-questions.md`. Q3 and Q4 are refusal tests and belong to
generation evaluation in Week 5, so they are excluded here.

**Metrics.** Hit rate is whether the correct chunk appears in the top *k* at all (k=5). MRR is
the mean reciprocal rank — rank 1 scores 1.0, rank 4 scores 0.25, absent scores 0. Week 1's
baseline was Q2 at rank 4, MRR 0.25.

**Match conditions.** Each question carries a machine-readable `**Match:**` line — source,
page, and a `contains` probe — and all fields must hold together. `source` and `page` alone
are too loose (a page holds several chunks); `contains` alone too loose in the other direction
(`550` appears in all three delaftale sheets). Verified against the parsed corpus before the
comparison ran: 11 questions, exactly one matching chunk each.

**Models.** `multilingual-e5-small` (Week 1's reference, 384-dim), `BGE-M3` (the multilingual
ceiling, 1024-dim), and `all-MiniLM-L6-v2` (English-trained, 384-dim). The third is chosen
deliberately: it is the model Chroma silently defaults to, which Week 1 §8 flagged as a trap
because it will embed Danish without complaint or warning. This turns a documented trap into
a measured one.

**Prefixes as model config.** e5 requires `passage:`/`query:`; BGE-M3 and MiniLM use none.
Week 1 hardcoded these in `ingest.py:47` and `query.py:17`. Getting this wrong degrades
retrieval silently, which in a comparison means concluding something false about a model, so
the prefix is now a property of the model config rather than a string in the pipeline.

### Results

**MRR:**

| | fixed | recursive | structural |
|---|---|---|---|
| e5-small | 0.455 | 0.597 | **0.697** |
| BGE-M3 | 0.455 | 0.632 | **0.768** |
| MiniLM-en | 0.253 | 0.377 | 0.594 |

**Hit rate:**

| | fixed | recursive | structural |
|---|---|---|---|
| e5-small | 0.55 | **1.00** | 0.91 |
| BGE-M3 | 0.64 | 0.91 | **1.00** |
| MiniLM-en | 0.55 | 0.64 | 0.73 |

### Chunking is worth more than the model

Reading down a column versus across a row:

- **Chunking, model held constant:** BGE-M3 gains **0.313 MRR** from fixed to structural.
- **Model, chunking held constant:** swapping MiniLM for BGE-M3 at fixed size gains **0.202**.

The best model on the worst chunking (0.455) loses to the worst model on the best chunking
(0.594). The syllabus claim — retrieval quality is mostly decided before generation — measured
on this corpus rather than asserted.

Structural beats recursive on every model, and the gap widens as the model weakens: 0.100 for
e5, 0.136 for BGE-M3, 0.217 for MiniLM. Suggestive that structure compensates for a weaker
embedder, but eleven questions is too small a sample to lean on it.

### Hit rate and MRR disagree about the winner

`e5-small` + recursive finds **every** question (1.00) but ranks them worse (0.597).
BGE-M3 + structural also finds every question and ranks them better (0.768) — so BGE-M3
structural dominates. But e5 structural *misses* one question (0.91) while ranking the rest
more precisely than e5 recursive.

Which matters depends on *k* and on cost asymmetry. The syllabus's Week 6 note applies: in a
tender, a missed mandatory requirement can disqualify a bid while a false positive costs
someone thirty seconds of reading. That argues for recall over precision, and therefore for
reading hit rate first.

**Recommended stack: BGE-M3 + structural chunking.** The only configuration at hit rate 1.00
with MRR 0.768.

### Per-question ranks reveal what the aggregates hide

| model | chunking | Q1 | Q2 | Q5 | Q6 | Q7 | Q8 | Q9 | Q10 | Q11 | Q12 | Q13 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| e5 | structural | 3 | 2 | 1 | 1 | 1 | 1 | — | 1 | 1 | 2 | 3 |
| BGE-M3 | structural | 1 | 5 | 1 | 1 | 1 | 1 | 4 | 2 | 1 | 2 | 1 |
| MiniLM | structural | — | 1 | 1 | 1 | 1 | 5 | — | 1 | 1 | — | 3 |

**BGE-M3's advantage is narrow, not broad.** It wins Q1 (1 vs 3), Q13 (1 vs 3) and Q9 (4 vs
miss); it *loses* Q2 (5 vs 2) and Q10 (2 vs 1). The 0.071 MRR gain over e5 is essentially
"finds Q9, ranks the xlsx questions better" — not a uniform improvement, a different failure
profile.

That narrowness matters more than it sounds. Q9 and Q13 are the three-identical-sheets
questions, where the discriminating content is a bare number (`1848` vs `1728`, `550` vs
`500`). Those are precisely the cases where being wrong returns a *wrong figure* rather than a
wrong citation. BGE-M3's edge is concentrated on the questions that matter most.

**Q9 is nearly unsolvable by embedding alone** — found in 2 of 9 configurations, never above
rank 4. **Q7 is rank 1 in all nine** — distinctive vocabulary, no near-duplicates, the easy
case. **Q2 inverts:** MiniLM ranks it 1st while BGE-M3 ranks it 5th. With eleven questions
this cannot be distinguished from noise, and saying so is more honest than explaining it.

**MiniLM fails three questions outright** — Q1, Q9, Q12. Q1 is the simplest factual lookup in
the set (15 % årsværk under oplæring) and the English-centric model cannot find it in the top
5. The clearest possible illustration of why model choice on a Danish corpus is not a detail.

### The fixed-size baseline had to be repaired before it was fair

The first run scored fixed-size at hit rate 0.09 across all three models — identically, which
was the tell. `chunk_fixed` concatenated each document before slicing, destroying per-element
page provenance, so every page-based match failed. That measures "concatenate-then-slice
loses provenance," not "fixed-size retrieves badly."

Repaired to chunk per page, as Week 1 did, and re-run: 0.455 / 0.455 / 0.253. Two things stay
deliberately broken because they are real properties of the baseline, not implementation
choices: `section` is always `None` (fixed-size cannot cite a clause) and `delaftale` is
always `None` (the sheet identity lives in a group name that fixed-size has no mechanism to
carry). Q9 and Q13 therefore remain structural misses for fixed-size — which is the schema
argument, restated as a metric.

Note MiniLM + fixed scores **0.253**, almost exactly Week 1's 0.25 baseline. Coincidence, but
a tidy one: the naive configuration lands where the naive configuration landed.

---

## 12. Modality is invisible to every model tested — and now provably so

Week 1 §5 measured `skal` vs `bør` at **0.9966** on e5-small and concluded embeddings encode
topic, not modality. The Week 2 plan set the test: *if BGE-M3 separates them meaningfully
better, that changes the Week 3 hybrid-retrieval argument; if it doesn't, that's the stronger
finding.*

Measured across all three models, with an added control pair — two unrelated `skal`
obligations from different parts of the contract (apprentice quotas vs invoicing law):

| Model | `skal` vs `bør`, same clause | unrelated clauses | usable range |
|---|---|---|---|
| e5-small | 0.9981 | 0.8850 | **0.113** |
| BGE-M3 | 0.9920 | 0.4834 | **0.509** |
| MiniLM-en | 0.9685 | 0.5691 | 0.399 |

### The control pair is what makes this conclusive

Raw similarity means nothing across models, because each compresses its output range
differently. Week 1 §5 noted e5-small pushes Danish into roughly 0.85–1.00 and concluded
"absolute scores carry almost no information; only ordering does." The control quantifies it:
**e5 uses 0.885–0.998 for the entire span from unrelated to near-identical. BGE-M3 uses
0.483–0.992 — four and a half times the dynamic range.**

That reframes the finding entirely. It is not that BGE-M3 fails to separate `skal` from `bør`
in the same compressed way e5 does. BGE-M3 *can* discriminate — it places topically unrelated
clauses at 0.48. It still places a mandatory requirement and its optional twin at 0.992, on a
scale where it demonstrably has room to spare.

Normalised against each model's own usable range, the modality gap is:

- BGE-M3: 0.008 / 0.509 = **1.5 % of usable range**
- e5-small: 0.0019 / 0.113 = **1.7 % of usable range**

Nearly identical proportions from models that look completely different in absolute terms. A
model with a working discrimination range *chooses* to place these two almost on top of each
other, because **modality is not a topical difference.**

### Week 1's framing survives, and gets sharper

Week 1 §5's vivid version — *two genuine obligations sit further apart than a requirement and
its optional twin* — holds on all three models. For e5 the numbers are 0.885 vs 0.998. For
BGE-M3 they are **0.483 vs 0.992**: two real obligations are half a unit apart while a
requirement and its negation are within 0.008.

**The Week 3 hybrid-retrieval argument is now empirically grounded rather than asserted.** This
is not one model's limitation. Three models spanning 384 to 1024 dimensions, English-trained
to state-of-the-art multilingual, all agree. BM25 weights rare exact tokens, which is precisely
what every dense embedding tested here smooths away.

*(MiniLM's 0.9685 looks like better separation and is not: proportionally it is the same, and
it is the worst retriever in §11's table. A model that compresses everything shows smaller
differences everywhere, not sharper discrimination.)*

---

## 13. The vector store is a swappable component

Implemented behind one interface in `src/store.py`: `NumpyStore` (brute force, no
dependencies), `ChromaStore`, `FaissStore`. All three return identical results on the same
query, filtered and unfiltered, at 113 chunks.

The point was never a benchmark — at this size any timing difference is noise. It was the
seam, so Weeks 3 and 4 are not coupled to either backend.

**The two are not like-for-like, and that asymmetry is the lesson:**

| | Chroma | FAISS |
|---|---|---|
| What it is | a database | an index |
| Metadata | stored alongside vectors | not stored — parallel list, looked up by position |
| Filtering | server-side `where` clause | **none** — over-fetch and filter in Python |
| Persistence | built in | write the index to a file |
| Types | no `None`, no lists | n/a |

Chroma's type restriction is a live constraint: `pages` is a list and cannot be stored, so it
would have to be serialised to a string and parsed back — and `pages` is what the eval matcher
needs for the split-tidsplan question.

FAISS's inability to filter is worked around by fetching 20× and filtering in Python. That
works at 113 chunks and degrades badly at scale: with a selective filter you may over-fetch
the whole index and still come up short.

`NumpyStore` is included deliberately as a reference implementation. Twenty lines, and it makes
the other two legible — you can see exactly what they are optimising.

**Filtering answers Q13 outright.** `where={"delaftale": "København"}` returns three chunks,
all København, rate table first. The hardest near-duplicate case in the corpus, solved by
filtering rather than by hoping the ranking out-ranks two byte-identical competitors.

*Concepts to be able to explain:* cosine and dot product are identical on normalised vectors,
which is why `IndexFlatIP` works as cosine here. HNSW builds a navigable graph (fast queries,
high memory); IVF partitions into clusters and probes the nearest few (lower memory, tunable
recall). Neither is used here — `IndexFlat` is exhaustive, and at 113 vectors of 384 dimensions
that is ~43,000 multiply-adds, i.e. microseconds. Approximate search trades exactness for speed
and only pays off in the millions.

---

## 14. A fourth inspection artifact, and a fifth

§8 recorded three cases of mistaking an inspection artifact for a data problem. Two more
occurred during the comparison, and the pattern is now the most reliable finding of the week.

**4. Stale notebook state.** After editing `chunk_fixed`, the scores did not move.
`inspect.getsource` showed the *new* code — because it reads the file on disk — while the
running session held the *old* module. Notebook state persists across cells in whatever order
they were run, so "I changed the code" and "the running program uses the changed code" are
separate facts.

**5. A failed clone read as a data problem.** `ModuleNotFoundError: No module named 'src'`
after a clone URL still containing the placeholder `YOURNAME`. Ten minutes were spent
hypothesising about tokenizer round-trip losses corrupting `contains` probes before the
plumbing was checked.

**Rule, restated: check the pipe before diagnosing the water.**

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
| §-numbering is real; `section_path` populatable in the two main documents | W3 retrieval by address |
| Duplicate §12.2 — the path is not a unique key | W7 cross-reference resolution |
| Reading order comes from `body.children`; xlsx nests in `groups` | W2 chunking, W7 full corpus |
| Q6, Q10, Q12, Q13 answerable through metadata alone | W3 — sets the ceiling |
| 4.03 chars/token on Danish; median element 33 tokens | W2 chunk sizing |
| Suspended-compound hypothesis tested and rejected (9/10 correct) | Method |
| Severed chunks fixed by Docling, not by chunking strategy | W2 writeup — attribute correctly |
| Recursive chunking mislabels sections across boundaries | W2 strategy choice, W5 citations |
| Three `Bilag 4` title chunks are a fourth near-duplicate cluster | W3 retrieval eval |
| Chunking worth 0.313 MRR; model swap worth 0.202 | W3 — where effort pays |
| BGE-M3 + structural: hit 1.00, MRR 0.768 | W3 baseline to beat |
| MiniLM-en misses Q1, the simplest lookup in the set | W3 — model choice is not a detail |
| Modality gap ≈1.5 % of usable range on all three models | W3 hybrid — now empirical |
| BGE-M3 range 0.483–0.992 vs e5's 0.885–0.998 | W6 threshold design |
| Q9 found in 2 of 9 configurations, never above rank 4 | W3 — the hard case |
| Fixed-size cannot carry section or delaftale | W2 schema argument as a metric |
| Store swappable behind one interface; FAISS cannot filter | W3, W4 decoupling |
| Chroma rejects `None` and lists — `pages` needs serialising | W4 if Chroma is the store |