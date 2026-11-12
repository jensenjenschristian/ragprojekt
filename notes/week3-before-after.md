# Week 3 — before/after examples

Before: dense BGE-M3 (cosine). After: dense top-10 → Cohere rerank-v5.0-pro reading delaftale + section heading + text (relevance score). Scores are on different scales.

## Q2: Hvilke tekniske krav gælder for installationerne?

**Before — dense**

| # | score | chunk | text |
|---|---|---|---|
| 1 | 0.638 | Bilag 3 - Kravspecifikation — 2. Krav til udførelsen af arbejdet | Ved ændringer på ABA-, AVA- og ABV-anlæg skal gældende myndighedskrav, certificeringskrav … |
| 2 | 0.596 | Bilag 3 - Kravspecifikation — 2. Krav til udførelsen af arbejdet | Alle ændringer på kritiske installationer, herunder ABA-, AVA-, ABV-, nødog panikbelysning… |
| 3 | 0.572 | Bilag 3 - Kravspecifikation — 2. Krav til udførelsen af arbejdet | Leverandøren skal sikre sig en stabil medarbejdergruppe, der over tid opbygger stort kends… |
| 4 | 0.566 | Aftale — 3.3 Omfattede ydelser | Aftalen omfatter levering af alle henholdsvis eltekniske og brandtekniske ydelser, dog med… |
| 5 | 0.564 | Bilag 3 - Kravspecifikation — 1. Generelt **← correct** | Leverandøren skal generelt ved udførelse af ydelserne sikre overholdelse af følgende regle… |

**After — rerank**

| # | score | chunk | text |
|---|---|---|---|
| 1 | 0.682 | Bilag 3 - Kravspecifikation — 2. Krav til udførelsen af arbejdet | Ved ændringer på ABA-, AVA- og ABV-anlæg skal gældende myndighedskrav, certificeringskrav … |
| 2 | 0.647 | Bilag 3 - Kravspecifikation — 1. Generelt **← correct** | Leverandøren skal generelt ved udførelse af ydelserne sikre overholdelse af følgende regle… |
| 3 | 0.613 | Bilag 3 - Kravspecifikation — 2. Krav til udførelsen af arbejdet | Alle ændringer på kritiske installationer, herunder ABA-, AVA-, ABV-, nødog panikbelysning… |
| 4 | 0.431 | Bilag 3 - Kravspecifikation — 2. Krav til udførelsen af arbejdet | Leverandøren skal sikre sig en stabil medarbejdergruppe, der over tid opbygger stort kends… |
| 5 | 0.344 | Aftale — 3.3 Omfattede ydelser | Aftalen omfatter levering af alle henholdsvis eltekniske og brandtekniske ydelser, dog med… |

## Q9: Hvad er udkaldstillægget for hasteopgaver uden for almindelig arbejdstid på delaftale København?

**Before — dense**

| # | score | chunk | text |
|---|---|---|---|
| 1 | 0.653 | Aftale — 6.3 Tillæg | Der ydes tillæg for udkald uden for normal arbejdstid på 3 x timesats. Der ydes tillæg på … |
| 2 | 0.638 | Bilag 4 - Tilbudsliste [Esbjerg] — Tillæg til timepriser | Enhedspris Udkaldstillæg i kr. (gna. timepris x 3) / 1728 Overarbejdstillæg i kr. (30%) / … |
| 3 | 0.636 | Bilag 4 - Tilbudsliste [Aalborg] — Tillæg til timepriser | Enhedspris Udkaldstillæg i kr. (gna. timepris x 3) / 1728 Overarbejdstillæg i kr. (30%) / … |
| 4 | 0.627 | Bilag 4 - Tilbudsliste [København] — Tillæg til timepriser **← correct** | Enhedspris Udkaldstillæg i kr. (gna. timepris x 3) / 1848 Overarbejdstillæg i kr. (30%) / … |
| 5 | 0.602 | Aftale — 4.3 Hasteopgaver | Opgaver vedr. hasteopgaver skal være påbegyndt på adressen inden for 1 time regnet fra det… |

**After — rerank**

| # | score | chunk | text |
|---|---|---|---|
| 1 | 0.447 | Aftale — 4.3 Hasteopgaver | Opgaver vedr. hasteopgaver skal være påbegyndt på adressen inden for 1 time regnet fra det… |
| 2 | 0.396 | Bilag 4 - Tilbudsliste [København] — Tillæg til timepriser **← correct** | Enhedspris Udkaldstillæg i kr. (gna. timepris x 3) / 1848 Overarbejdstillæg i kr. (30%) / … |
| 3 | 0.375 | Aftale — 6.3 Tillæg | Der ydes tillæg for udkald uden for normal arbejdstid på 3 x timesats. Der ydes tillæg på … |
| 4 | 0.161 | Udbudsbetingelser — 13.1 Tilbudslisten | Tilbudslisten indgår som Bilag 4. Tilbudslisten skal udfyldes i sin helhed, og priser på s… |
| 5 | 0.154 | Bilag 4 - Tilbudsliste [Aalborg] — Tillæg til timepriser | Enhedspris Udkaldstillæg i kr. (gna. timepris x 3) / 1728 Overarbejdstillæg i kr. (30%) / … |
