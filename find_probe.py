import sys
from src.ingest import build_chunks

chunks = build_chunks(model_key="e5-small")
probe = sys.argv[1]
hits = [c for c in chunks if probe in c["text"]]
print(f"{len(hits)} chunk(s) contain {probe!r}")
for c in hits:
    print(f"  {c['source']} p{c['page']} pages={c['pages']} "
          f"[{c['delaftale']}] {c['section']} / {c['subsection']}")
    i = c["text"].find(probe)
    print(f"    ...{c['text'][max(0, i - 80):i + 80]!r}...")