from pathlib import Path
from pypdf import PdfReader
import chromadb
from sentence_transformers import SentenceTransformer

def load_pages(data_dir="data"):
    pages = []
    for pdf in sorted(Path(data_dir).glob("*.pdf")):
        reader = PdfReader(pdf)
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"text": text, "source": pdf.name, "page": i})
    return pages

def chunk_pages(pages, size=1000, overlap=200):
    chunks = []
    for p in pages:
        text = p["text"]
        start = 0
        while start < len(text):
            piece = text[start:start + size]
            if piece.strip():
                chunks.append({
                    "text": piece,
                    "source": p["source"],
                    "page": p["page"],
                })
            start += size - overlap
    return chunks

#stage 1
#if __name__ == "__main__":
#    pages = load_pages()
#    docs = len({p["source"] for p in pages})
#    print(f"{len(pages)} pages with text, from {docs} documents")
#    #for i, p in enumerate(pages):
#    #    print(f"{i:4}  {p['source'][:40]:40}  side {p['page']:3}  {len(p['text']):5} chars")
#    t = pages[18]["text"]
#    print(len(t))
#    print(repr(t[:1500]))
#    Path("page18.txt").write_text(t, encoding="utf-8")

def build_index(chunks, db_path="chroma_db", collection_name="tender"):
    model = SentenceTransformer("intfloat/multilingual-e5-small")

    texts = [f"passage: {c['text']}" for c in chunks]
    print(f"Embedding {len(texts)} chunks...")
    vectors = model.encode(texts, batch_size=16, show_progress_bar=True)

    client = chromadb.PersistentClient(path=db_path)
    client.delete_collection(collection_name) if collection_name in [
        c.name for c in client.list_collections()
    ] else None
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[f"{c['source']}-p{c['page']}-{i}" for i, c in enumerate(chunks)],
        embeddings=[v.tolist() for v in vectors],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"], "page": c["page"]} for c in chunks],
    )
    return collection

#stage 2
if __name__ == "__main__":
    pages = load_pages()
    chunks = chunk_pages(pages)
    print(f"{len(pages)} pages -> {len(chunks)} chunks")

    c = chunks[27]
    print(f"\n--- {c['source']} side {c['page']} ---")
    print(c["text"])