from transformers import AutoTokenizer
from src.parse_docling import load_corpus

tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small")
els = load_corpus()

counts = sorted(len(tok.encode(e["text"])) for e in els)
n = len(counts)

print("elements:", n)
print("min:   ", counts[0])
print("median:", counts[n // 2])
print("p90:   ", counts[int(n * 0.9)])
print("max:   ", counts[-1])
print("over 512:", sum(1 for c in counts if c > 512))
print("chars/token:", round(sum(len(e["text"]) for e in els) / sum(counts), 2))

print("\n--- elements under 8 tokens ---")
short = [e for e in els if len(tok.encode(e["text"])) < 8]
print(len(short), "elements")
for e in short[:15]:
    print(f"  {e['source'][:20]:20} p{e['page']} | {e['text'][:50]!r}")

for i, e in enumerate(els):
    if e["text"].strip() == "toriebygninger":
        print(repr(els[i-1]["text"][-60:]))
        print(repr(e["text"]))
        break

print("\n--- suspended compound chains ---")
import re
CHAIN = re.compile(r"\w+-,")
for e in els:
    if CHAIN.search(e["text"]):
        print(f"  {e['source'][:18]:18} p{e['page']} | {e['text'][:90]}")

print("\n--- elements starting lowercase after one ending in hyphen ---")
for i in range(1, len(els)):
    prev, cur = els[i-1]["text"].rstrip(), els[i]["text"].lstrip()
    if prev.endswith("-") and cur[:1].islower():
        print(f"  {els[i]['source'][:18]:18} p{els[i]['page']} | ...{prev[-40:]} + {cur[:40]}")

print("\n--- possible over-joins ---")
for e in els:
    for m in re.finditer(r"\b\w+og\b", e["text"]):
        w = m.group()
        if len(w) > 5 and not w.endswith(("log", "sog", "tog", "bog")):
            print(f"  {e['source'][:18]:18} p{e['page']} | {w}")