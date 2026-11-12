from src.bm25 import tokenize

samples = [
    "Udkaldstillæg i kr. (gna. timepris x 3): 1.728",
    "faste rabatsats 0,38 og 0.38",
    "12.2 Udvælgelse",
    "normal arbejdstid kl. 7.30-15.30",
    "Kontraktstart: 1. december 2026",
    "sikkerhedsmyndighederne / sikkerhedsmyndigheder",
    "udkaldstillægget / Udkaldstillæg",
    "elektrikersvend / Elektriker svend",
    "Kravspecifikation / tekniske krav",
]
for s in samples:
    print(s)
    print("  raw :", tokenize(s))
    print("  stem:", tokenize(s, stem=True))

print()
for w in ["sikkerhedsmyndighed", "sikkerhedsmyndigheden",
          "sikkerhedsmyndigheder", "sikkerhedsmyndighederne",
          "myndighed", "myndigheder", "myndighederne"]:
    print(f"{w:26} -> {tokenize(w, stem=True)[0]}")

import re
from src.ingest import build_chunks
for c in build_chunks(model_key="e5-small"):
    for m in set(re.findall(r"\w*myndighed\w*", c["text"], flags=re.I)):
        print(f"{c['source']} p{c['page']}: {m}")