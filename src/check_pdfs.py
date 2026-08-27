from pathlib import Path
from pypdf import PdfReader

for pdf in sorted(Path("data").glob("*.pdf")):
    reader = PdfReader(pdf)
    pages = len(reader.pages)
    sampled = min(pages, 5)
    text = "".join((p.extract_text() or "") for p in reader.pages[:sampled])
    per_page = len(text) / sampled
    status = "OK" if per_page > 200 else "SCANNED?"
    print(f"{status:9} {pages:4} pages  {per_page:7.0f} chars/page  {pdf.name}")