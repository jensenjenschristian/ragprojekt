import json
from pathlib import Path
from collections import Counter

PARSED = Path("data-parsed")

for f in sorted(PARSED.glob("*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    labels = Counter(t.get("label") for t in d.get("texts", []))
    print(f"\n{f.stem}")
    print("  ", dict(labels))

#d = json.loads((PARSED / "Aftale.json").read_text(encoding="utf-8"))
#for t in d.get("texts", []):
#    if t.get("label") in ("section_header", "title"):
#        page = t.get("prov", [{}])[0].get("page_no")
#       print(f"p{page:>3} | {t.get('level', '-')} | {t.get('text','')[:70]}")
    
d = json.loads((PARSED / "Udbudsbetingelser.json").read_text(encoding="utf-8"))
for t in d.get("texts", []):
    if t.get("label") in ("section_header", "title"):
        print(f"p{t.get('prov',[{}])[0].get('page_no'):>3} | {t.get('text','')[:70]}")

d = json.loads((PARSED / "Aftale.json").read_text(encoding="utf-8"))
for t in d.get("texts", []):
    if t.get("label") == "page_footer":
        print(t.get("text","")[:60])