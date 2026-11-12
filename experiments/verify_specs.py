from src.ingest import build_chunks
from src.evaluate import matches
from src.eval_specs import SPECS_W3

chunks = build_chunks(model_key="e5-small")
for qid, spec in SPECS_W3.items():
    hits = [c for c in chunks if matches(c, spec)]
    print(f"{qid}: {len(hits)} matching chunk(s)")
    for c in hits:
        print(f"    {c['source'][:30]} pages={c['pages']} {c['section']}")