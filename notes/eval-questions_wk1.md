# Eval questions — collected while building

Each entry: the question, what a correct answer looks like, and where the
evidence lives. Some entries are refusals — cases where the right behaviour
is to decline rather than answer.

---

## Q1. Hvilke tekniske krav gælder for installationerne?

**Expected:** Refusal / redirect. Bilag 3 §1 delegates technical requirements
to AAU's Tekniske Kravspecifikation, hosted externally and updated annually.
That document is not in the corpus, so no grounded answer exists.

**Source:** Bilag 3 - Kravspecifikation.pdf, side 2
**Tests:** abstention. A confabulated list of requirements is a clear failure.
**closest match rank:** 3 
**baseline_answer:**De tekniske krav til installationerne er navnlig følgende:

- Installationerne skal udføres i overensstemmelse med AAU’s til enhver tid gældende Tekniske Kravspecifikation, relevante love, bekendtgørelser, øvrige regelsæt, branchestandarder samt AAU’s vejledning til eksterne samarbejdspartnere. (Bilag 3 - Kravspecifikation.pdf, side 2)
- Ydelserne omfatter blandt andet service og vedligehold af alle typer elinstallationer, elanlæg og armaturer, lovpligtig test af RCD-enheder, fejlsøgning og fejlretning, programmerings- og teknikerarbejde, energioptimering samt elentrepriseopgaver. (Aftale.pdf, side 4)
- For brandtekniske installationer omfatter ydelserne typisk service og vedligehold af blandt andet ABA-, ABV- og ABDL-anlæg, dog ikke AVS-vandtågeanlæg i delaftalen i København. (Aftale.pdf, side 4)
- Arbejde på kritiske installationer, herunder ABA-, AVA-, ABV-, nød- og panikbelysningsanlæg samt øvrige sikkerheds- og sikringsinstallationer, skal aftales forudgående med AAU Campus Service. (Bilag 3 - Kravspecifikation.pdf, side 4)
- Efter arbejde på kritiske installationer skal leverandøren dokumentere og verificere, at anlægget fungerer som forudsat, og at integrationer til andre systemer fortsat er intakte. (Bilag 3 - Kravspecifikation.pdf, side 4)
- Konfigurationsændringer, softwareopdateringer og firmwareopdateringer på installationer med programmerbare funktioner skal dokumenteres og stilles til rådighed for AAU. (Bilag 3 - Kravspecifikation.pdf, side 4)
- AAU skal varsles mindst 5 arbejdsdage før planlagte opdateringer eller ændringer, der kan påvirke anlæggets drift eller tilgængelighed. (Bilag 3 - Kravspecifikation.pdf, side 4)
- Før ændringer på software-, firmware- eller konfigurationsbaserede installationer skal der foreligge en aktuel backup af anlæggets konfiguration, programmering og relevante data. (Bilag 3 - Kravspecifikation.pdf, side 4)
- Hvis en ændring medfører tab af data, konfiguration eller funktionalitet, skal leverandøren uden ekstra omkostninger genskabe anlægget til samme funktionelle niveau som før ændringen. Leverandøren skal desuden på AAU’s anmodning kunne dokumentere, at backup er gennemført, og at genskabelse er mulig. (Bilag 3 - Kravspecifikation.pdf, side 4)
- Kravene om backup, dokumentation og ændringsstyring gælder kun installationer med software-, firmware- eller konfigurationsbaserede funktioner og gælder ikke traditionelle elinstallationer uden programmerbare komponenter. (Bilag 3 - Kravspecifikation.pdf, side 4)
- Kritiske fejlrettelser og nødvendige sikkerhedsopdateringer skal kunne gennemføres hurtigst muligt efter aftale med AAU. Planlagt vedligehold og ændringsarbejde skal så vidt muligt udføres på tidspunkter, hvor påvirkningen af universitetets drift er mindst mulig, under hensyntagen til blandt andet undervisning, forskning og eksamensperioder. (Bilag 3 - Kravspecifikation.pdf, side 4)
- Ændringer på ABA-, AVA- og ABV-anlæg skal overholde gældende myndighedskrav, certificeringskrav og relevante standarder. (Bilag 3 - Kravspecifikation.pdf, side 4)
**answer_after_intervention:**De tekniske krav til installationerne er:

- Arbejde på kritiske installationer skal aftales på forhånd med AAU Campus Service. Kritiske installationer omfatter bl.a. ABA-, AVA-, ABV-, nød- og panikbelysningsanlæg samt øvrige sikkerheds-, sikrings- og driftskritiske installationer. *(Bilag 3 - Kravspecifikation.pdf, side 4)*

- Efter arbejde på kritiske installationer skal leverandøren dokumentere og verificere, at anlægget fungerer som forudsat, og at integrationer til andre systemer fortsat er intakte. *(Bilag 3 - Kravspecifikation.pdf, side 4)*

- Konfigurationsændringer, softwareopdateringer og firmwareopdateringer på installationer med programmerbare funktioner skal dokumenteres og stilles til rådighed for AAU. *(Bilag 3 - Kravspecifikation.pdf, side 4)*

- AAU skal varsles mindst 5 arbejdsdage før planlagte opdateringer eller ændringer, der kan påvirke anlæggets drift eller tilgængelighed. *(Bilag 3 - Kravspecifikation.pdf, side 4)*

- Før ændringer på software-, firmware- eller konfigurationsbaserede installationer skal leverandøren sikre, at der foreligger en aktuel backup af anlæggets konfiguration, programmering og relevante data. *(Bilag 3 - Kravspecifikation.pdf, side 4)*

- Ved planlægning og udførelse af ændringer skal der tages hensyn til undervisning, forskning, eksamensperioder og AAU’s lavserviceperioder. *(Bilag 3 - Kravspecifikation.pdf, side 4)*

- Ændringer på ABA-, AVA- og ABV-anlæg skal overholde gældende myndighedskrav, certificeringskrav og relevante standarder. *(Bilag 3 - Kravspecifikation.pdf, side 4)*

- Kravene om backup, dokumentation og ændringsstyring gælder alene installationer med software-, firmware- eller konfigurationsbaserede funktioner, herunder eksempelvis ABA-, AVA-, ABV-, nød- og panikbelysningsanlæg, DALI-anlæg og IBI-installationer. De gælder ikke traditionelle el-installationer uden programmerbare komponenter. *(Bilag 3 - Kravspecifikation.pdf, side 4)*

---

## Q1b "Hvilke krav stiller AAU til kabeldimensionering?"

**baseline_answer:**
Konteksten angiver ikke konkrete krav til kabeldimensionering. Den henviser i stedet til AAU’s til enhver tid gældende Tekniske Kravspecifikation – funktionskrav til bygningsdele og installationer, som ikke er medtaget i konteksten. (Bilag 3 - Kravspecifikation.pdf, side 2)

---

## Q2. Hvor stor en andel af årsværkene skal udgøres af personer under oplæring?

**Expected:** 15 %, per Bilag 3 §1, with reference to Bilag 7.

**Source:** Bilag 3 - Kravspecifikation.pdf, side 2
**Tests:** retrieval of a specific figure buried in prose; whether the
citation names the right bilag and page.
**rank:** 4
**baseline_answer:** 15 % af de leverede årsværk skal udgøres af personer under oplæring. (Bilag 3 - Kravspecifikation.pdf, side 2)
**answer_after_intervention:** Det kan ikke fastslås ud fra det foreliggende uddrag, hvor stor en andel af årsværkene der skal udgøres af personer under oplæring. Uddraget angiver kun, at **et antal årsværk** skal besættes med lærlinge, men selve antallet eller andelen fremgår ikke. *(Bilag 7 - Arbejdsklausul.pdf, side 3)*