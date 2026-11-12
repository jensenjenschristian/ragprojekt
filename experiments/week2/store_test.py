from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
from src.parse_docling import load_corpus
from src.chunking import chunk_structural
from src.store import NumpyStore, ChromaStore, FaissStore

tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small")
model = SentenceTransformer("intfloat/multilingual-e5-small")

chunks = chunk_structural(load_corpus(), tok)
vecs = model.encode(["passage: " + c["text"] for c in chunks],
                    normalize_embeddings=True)

s = NumpyStore()
s.add(vecs, chunks)

q = model.encode("query: Hvornår er kontraktstart?", normalize_embeddings=True)
for c in s.query(q, k=3):
    print(c["source"], "| p", c["page"], "|", c["section"])

print("\n--- filtered to Bilag 4, København ---")
q2 = model.encode("query: Hvad er timeprisen for en elektrikersvend?",
                  normalize_embeddings=True)
for c in s.query(q2, k=3, where={"delaftale": "København"}):
    print(c["delaftale"], "|", c["section"])

print("\n--- same query, three stores ---")
for label, cls in [("numpy", NumpyStore), ("chroma", ChromaStore), ("faiss", FaissStore)]:
    st = cls()
    st.add(vecs, chunks)
    hits = st.query(q, k=3)
    print(f"{label:7}", [f"{c['source'][:12]} p{c['page']}" for c in hits])

print("\n--- filtered query, three stores ---")
for label, cls in [("numpy", NumpyStore), ("chroma", ChromaStore), ("faiss", FaissStore)]:
    st = cls()
    st.add(vecs, chunks)
    hits = st.query(q2, k=3, where={"delaftale": "København"})
    print(f"{label:7}", [c["section"][:30] for c in hits])