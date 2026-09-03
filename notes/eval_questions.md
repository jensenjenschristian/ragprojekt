# Eval questions

Ground truth for retrieval metrics (hit rate, MRR) and generation checks. Sources are
document + page as extracted by the Week 1 pypdf pipeline; re-verify after the Docling swap.

Written before running any Week 2 comparison, deliberately — questions written after seeing
results get fitted to the results.

*Started Week 1, extended 3 September 2026.*

---

### Q1 — simple factual lookup
**Question:** Hvor stor en andel af de leverede årsværk skal udgøres af personer under oplæring?
**Expected:** 15 %.
**Source:** `Bilag 3 - Kravspecifikation.pdf` p2
**Tests:** baseline retrieval of a single stated figure.
**Week 1 result:** correct chunk at rank 4 → MRR 0.25. The baseline to beat.

---

### Q2 — ambiguous, delegation must be named first
**Question:** Hvilke tekniske krav gælder for installationerne?
**Expected:** Bilag 3 §1 delegates technical requirements to AAU's externally hosted
Tekniske Kravspecifikation. The delegation must appear first and prominently; a list of
on-topic contractual clauses without it is a failure.
**Source:** `Bilag 3 - Kravspecifikation.pdf` p2
**Tests:** behaviour when on-topic distractors can support a nearby reading of the question.
**Week 1 result:** failed — 13 correctly-cited bullets, none of them the answer. Faithful and
wrong. `k=2` made it worse; a sharpened prompt changed nothing.

---

### Q3 — true refusal, no plausible alternative
**Question:** Hvilke krav stiller AAU til kabeldimensionering?
**Expected:** abstention. Not in the corpus; points at the external Tekniske
Kravspecifikation, with a citation.
**Source:** none — absence is the ground truth.
**Tests:** refusal where the context contains no substitute answer.
**Week 1 result:** passed.

---

### Q4 — true refusal, external reference, second topic
**Question:** Hvad kræver Sikkerhedscirkulæret af leverandøren?
**Expected:** abstention. `Aftale.pdf` p8 requires the supplier to be cleared to store and
handle classified information `jf. Sikkerhedscirkulæret`, but the circular is not in the
corpus and its contents are unavailable.
**Source:** referring clause at `Aftale.pdf` p8; the answer itself is out of corpus.
**Tests:** whether the Q3 refusal generalises or was topic-specific. Week 1 §7 showed
abstention is context-sensitive, so one refusal test does not characterise the behaviour.
**Status:** unverified — confirm the expected answer by reading p8 before first use.

---

### Q5 — cross-reference
**Question:** Hvad er konsekvensen, hvis leverandøren ikke beskæftiger det aftalte antal
årsværk lærlinge?
**Expected:** a penalty (bod) of 100.000 kr. per missing årsværk, applied pro rata —
0,5 årsværk short = 50.000 kr., 1,1 short = 110.000 kr.
**Source:** `Bilag 7 - Arbejdsklausul.pdf` p4
**Tests:** whether retrieval follows `jf. Bilag 7` to the referenced document. The referring
clauses (`Bilag 3` p2, `Aftale.pdf` p15) state the obligation and are silent on consequences,
so answering from them alone is the failure mode.
**Note:** Bilag 3 frames the obligation as a percentage, Bilag 7 penalises an absolute count.
Reconciling the two needs the total årsværk. Not tested here; flagged for Week 7.

---

### Q6 — near-duplicate trap
**Question:** Hvornår kan bestillinger gå til den sekundære leverandør i stedet for den primære?
**Expected:** capacity problems (mandskabsmangel or similar) redirect an individual order —
a temporary fallback. Distinct from the separate case where the secondary is permanently
promoted to primary for all services under the agreement.
**Source:** `Aftale.pdf` p4 (binding). The same passage appears at
`Udbudsbetingelser.pdf` p4 (describes the procurement, does not bind).
**Tests:** two things. Whether the temporary and permanent cases are kept apart, and whether
retrieval indicates which document governs when both return near-identical text.
**Note:** the two copies differ slightly in the pypdf extraction. Check after Docling whether
that is a real textual difference or a line-wrap artifact.

---

### Q7 — compound noun
**Question:** Hvordan fastsættes afregningsprisen for et materiale, der ikke fremgår af prislisten?
**Expected:** based on the most comparable product in the referenceprisliste, less the
supplier's quoted discount rate.
**Source:** `Aftale.pdf` p10
**Tests:** compound matching. The question says `prislisten`; the corpus says
`referenceprislisten`. BM25 will not match the part to the compound in Week 3.
**Note:** the defining occurrence — `efterfølgende omtalt som "referenceprislisten"` — is
hyphen-split by pypdf into `refe-\nrenceprisliste`, so the one sentence that introduces the
term is also the one instance corrupted. Compounding and hyphenation stacking on one term.

---

### Q8 — modality
**Question:** Skal tilbudsgiver undlade at tage forbehold over for udbudsmaterialet?
**Expected:** the passage is advisory in form (`bør nøje overveje`) but the consequence is
severe: any reservation entitles AAU to reject the tender, and AAU is *obliged* to reject
reservations against fundamental elements or ones that cannot be reliably priced. An answer
that reports "bør" as merely optional has missed the point.
**Source:** `Udbudsbetingelser.pdf` p12
**Tests:** modality beyond the skal/bør binary. Three levels in four lines — `bør` (advisory),
`er berettiget til` (discretionary), `er forpligtet til` (binding).
**Note for Week 7:** a naive `skal`-detector fails twice on this passage. It flags
`om tilbuddet skal indeholde forbehold` (an ordinary subordinate modal, not an obligation)
and misses `er forpligtet til` (the real one).

---

### Q9 — currently unanswerable, should change in Week 2
**Question:** Hvad er udkaldstillægget for hasteopgaver uden for almindelig arbejdstid?
**Expected:** currently — abstention or a partial answer noting that the surcharge exists but
its size is defined in Bilag 4. After the xlsx is ingested — the actual figure.
**Source:** `Aftale.pdf` p7 establishes the surcharge `jf. Bilag 4`;
`Bilag 4 - Tilbudsliste.XLSX` holds the value.
**Tests:** the cost of excluding a file format. Bilag 4 is in the corpus directory but
invisible to pypdf, so the reference resolves to nothing.
**Use:** run before and after the Docling swap. This is the measured justification for
bringing the xlsx in.