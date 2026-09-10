from src.parse_docling import load_corpus

CHECKS = [
    ("Q1",  "Bilag 3 - Kravspecifikation", 2,  "15 %"),
    ("Q2", "Bilag 3 - Kravspecifikation", 2, "Kravspecifikation"),
    ("Q5",  "Bilag 7 - Arbejdsklausul",    4,  "100.000"),
    ("Q6",  "Aftale",                       4,  "mandskabsmangel"),
    ("Q7", "Aftale", 10, "fratrukket"),
    ("Q8",  "Udbudsbetingelser",           12,  "forpligtet til at afvise"),
    ("Q10", "Aftale",                       8,  "sikkerhedsmyndigheder"),
    ("Q11", "Udbudsbetingelser",            5,  "35 mio"),
    ("Q12", "Udbudsbetingelser",            7,  "1. december 2026"),
]

els = load_corpus()

for qid, source, page, needle in CHECKS:
    hits = [e for e in els
            if e["source"] == source and e["page"] == page and needle in e["text"]]
    status = f"OK  ({len(hits)})" if hits else "MISS"
    print(f"{qid:4} {status:9} {needle!r}")
    if not hits:
        anywhere = [e for e in els if needle in e["text"]]
        if anywhere:
            print(f"       found elsewhere: "
                  f"{[(e['source'][:18], e['page']) for e in anywhere[:3]]}")

print("\n--- xlsx ---")
for qid, needle in [("Q9", "1848"), ("Q13", "550")]:
    hits = [e for e in els
            if e["source"].startswith("Bilag 4") and e["delaftale"] == "København"
            and needle in e["text"]]
    print(f"{qid:4} {'OK' if hits else 'MISS':9} {needle!r} ({len(hits)})")

els = load_corpus()
for e in els:
    if "kravspecifikation" in e["text"].lower():
        print(e["source"], "| p", e["page"], "|", e["section"])
        print("   ", e["text"][:150])

for e in els:
    if "sammenlignelig" in e["text"].lower():
        print(e["source"], "| p", e["page"], "|", e["section"])
        print("   ", repr(e["text"][:200]))

for e in els:
    if e["source"] == "Bilag 3 - Kravspecifikation" and e["page"] == 2:
        print(repr(e["text"][:200]))
        print()