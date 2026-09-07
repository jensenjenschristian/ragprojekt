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
**Question:** Hvilke sikkerhedsklassifikationsniveauer opererer Sikkerhedscirkulæret med, og
hvad kræves der for at opbevare information på hvert niveau?
**Expected:** abstention. The corpus imposes obligations *relating to* the Sikkerhedscirkulæret
but contains none of its content — no classification levels, no handling procedures, no
clearance criteria. The correct answer points at the external circular.
**Source:** none — absence is the ground truth. The two referring clauses are at
`Aftale.pdf` p8.
**Tests:** whether the Q3 refusal generalises or was topic-specific. Week 1 §7 showed
abstention is context-sensitive, so one refusal test does not characterise the behaviour.
**Note:** the question was originally phrased *"Hvad kræver Sikkerhedscirkulæret af
leverandøren?"*, which is ambiguous — the p8 obligations are a plausible answer to a nearby
reading, making it a test of interpretation rather than abstention. Same defect as Q2.
Narrowed to something the circular itself defines and the corpus demonstrably lacks. The
positive version is now Q10.
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
**Expected:** three situations, all from the same list — (1) the primary cannot perform due to
temporary obstacles such as mandskabsmangel, so the individual order goes to the secondary;
(2) the primary cannot meet a deadline AAU has set; (3) the primary materially breaches the
agreement, AAU terminates, and the secondary is **permanently promoted** to primary for all
services. Cases 1–2 are order-by-order fallbacks; case 3 is a permanent change of role.
Conflating them is the failure mode.
**Source:** `Aftale.pdf` p4 — binding. The passage is **verbatim identical** at
`Udbudsbetingelser.pdf` p4, which does not bind but adds the rationale (a fixed primary for
both maintenance and larger works, a secondary to secure continuity) and names
`aftalens pkt. 3.2` as the governing clause.
**Tests:** whether the system can distinguish two chunks that are lexically identical. No
embedding, reranker or BM25 signal exists — the strings are the same. The `source` metadata
field is the only available discriminator, which makes this the direct test of the Week 2
schema decision.
**Note:** `Udbudsbetingelser.pdf` p4 uses `aktør` and `leverandør` interchangeably for the
same party in the same section — a Week 3 synonym/lexical-gap case.
**Note:** the Week 1 pypdf extraction places page furniture (`Side 4`) inside the passage,
between the intro sentence and the bullet list. Check Docling removes it.

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

---

### Q10 — obligation with named third parties
**Question:** Hvilke forpligtelser har leverandøren over for sikkerhedsmyndighederne?
**Expected:** two obligations. Clearance to store and handle classified information, and
dialogue and cooperation with the relevant security authorities and AAU's security
organisation regarding advice, design and construction of facilities subject to the
Sikkerhedscirkulæret. The authorities are named: PET and FE.
**Source:** `Aftale.pdf` p8
**Tests:** whether the named authorities survive retrieval. `PET` and `FE` are rare short
tokens — smoothed away by embeddings, weighted heavily by BM25. A Week 3 hybrid target.
**Note:** the obligation is expressed as `er forpligtet til`, with no `skal` anywhere in the
clause. Second instance after Q8 of a binding obligation a `skal`-scanner would miss.
**Note:** `sikkerhedsmyndigheder` is hyphen-split by pypdf (`sikker-\nhedsmyndigheder`), so
the term is damaged in the Week 1 index — alongside `referenceprisliste` in Q7. Re-check
both after Docling.