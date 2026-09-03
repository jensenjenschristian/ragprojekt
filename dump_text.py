import sys
from pathlib import Path

sys.path.insert(0, "src")
from ingest import load_pages

pages = load_pages("data")          # adjust if your signature differs

lines = []
for p in pages:
    for ln in p["text"].splitlines():
        if ln.strip():
            lines.append(f"{p['source']}\tp{p['page']}\t{ln.strip()}")

out = Path("notes/corpus-dump.txt")
out.write_text("\n".join(lines), encoding="utf-8")
print(f"{len(pages)} pages -> {len(lines)} lines -> {out}")