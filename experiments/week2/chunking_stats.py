from transformers import AutoTokenizer
from src.parse_docling import load_corpus
from src.chunking import chunk_fixed, chunk_recursive, chunk_structural

tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small")
els = load_corpus()

for name, fn in [("fixed", chunk_fixed), ("recursive", chunk_recursive),
                 ("structural", chunk_structural)]:
    cs = fn(els, tok)
    lens = sorted(len(tok.encode(c["text"], add_special_tokens=False)) for c in cs)
    over = sum(1 for l in lens if l > 512)
    print(f"{name:11} {len(cs):4} chunks | median {lens[len(lens)//2]:3} | max {lens[-1]:3} | over 512: {over}")

cs = chunk_structural(els, tok)
lens = sorted(len(tok.encode(c["text"], add_special_tokens=False)) for c in cs)
print("under 50 tokens:", sum(1 for l in lens if l < 50))
print("p10:", lens[len(lens)//10], "| p90:", lens[int(len(lens)*0.9)])

print("\n--- structural chunk sizes ---")
cs = chunk_structural(els, tok)
lens = sorted(len(tok.encode(c["text"], add_special_tokens=False)) for c in cs)
print("under 50 tokens:", sum(1 for l in lens if l < 50))
print("p10:", lens[len(lens) // 10], "| p90:", lens[int(len(lens) * 0.9)])

PROBES = [
    ("severed subject", "faglært person med relevant svendebrev"),
    ("severed condition", "fremsende en rekvisition med angivelse af ordrenr"),
]

for label, probe in PROBES:
    print(f"\n=== {label} ===")
    for name, fn in [("fixed", chunk_fixed), ("recursive", chunk_recursive),
                     ("structural", chunk_structural)]:
        hits = [c for c in fn(els, tok) if probe in c["text"]]
        if not hits:
            print(f"  {name:11} NOT FOUND")
            continue
        c = hits[0]
        i = c["text"].index(probe)
        print(f"  {name:11} section: {c['section']}")
        print(f"              ...{c['text'][max(0, i - 120):i + 60]}...")

print("\n--- short structural chunks ---")
for c in cs:
    n = len(tok.encode(c["text"], add_special_tokens=False))
    if n < 50:
        print(f"  {n:3} | {c['source'][:18]:18} | {c['section']} | {c['text'][:60]!r}")