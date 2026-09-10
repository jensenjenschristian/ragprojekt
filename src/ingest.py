
import chromadb
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

from src.parse_docling import load_corpus
from src.chunking import chunk_structural
from src.models import MODELS, DEFAULT_MODEL


def build_chunks(parsed_dir="data-parsed", model_key=DEFAULT_MODEL):
    cfg = MODELS[model_key]
    tok = AutoTokenizer.from_pretrained(cfg["name"])
    return chunk_structural(load_corpus(parsed_dir), tok)


def build_index(chunks, db_path="chroma_db", collection_name="tender",
                model_key=DEFAULT_MODEL):
    cfg = MODELS[model_key]
    model = SentenceTransformer(cfg["name"])

    texts = [cfg["passage_prefix"] + c["text"] for c in chunks]
    print(f"Embedding {len(texts)} chunks with {model_key}...")
    vectors = model.encode(texts, batch_size=16, show_progress_bar=True,
                           normalize_embeddings=True)

    client = chromadb.PersistentClient(path=db_path)
    if collection_name in [c.name for c in client.list_collections()]:
        client.delete_collection(collection_name)
    collection = client.create_collection(
        name=collection_name, metadata={"hnsw:space": "cosine"})

    collection.add(
        ids=[str(i) for i in range(len(chunks))],
        embeddings=[v.tolist() for v in vectors],
        documents=[c["text"] for c in chunks],
        metadatas=[_meta(c) for c in chunks],
    )
    return collection


def _meta(c):
    """Chroma rejects None and lists. `pages` is serialised to a comma string
    and parsed back on retrieval — see week2-findings.md §13."""
    return {
        "source": c["source"],
        "page": c["page"] or 0,
        "pages": ",".join(str(p) for p in (c.get("pages") or [])),
        "section": c["section"] or "",
        "section_path": c["section_path"] or "",
        "subsection": c["subsection"] or "",
        "delaftale": c["delaftale"] or "",
        "strategy": c.get("strategy", ""),
    }


if __name__ == "__main__":
    chunks = build_chunks()
    print(f"{len(chunks)} chunks")
    collection = build_index(chunks)
    print(f"Indexed: {collection.count()} chunks")