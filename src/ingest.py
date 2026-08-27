from pathlib import Path
from pypdf import PdfReader


def load_pages(data_dir="data"):
    pages = []
    for pdf in sorted(Path(data_dir).glob("*.pdf")):
        reader = PdfReader(pdf)
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"text": text, "source": pdf.name, "page": i})
    return pages


if __name__ == "__main__":
    pages = load_pages()
    docs = len({p["source"] for p in pages})
    print(f"{len(pages)} pages with text, from {docs} documents")