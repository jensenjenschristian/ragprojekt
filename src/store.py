import numpy as np


class Store:
    """Minimal vector store interface. Both backends implement this."""

    def add(self, vectors, chunks):
        raise NotImplementedError

    def query(self, vector, k=5, where=None):
        """Return k chunks nearest to vector, optionally filtered."""
        raise NotImplementedError


class NumpyStore(Store):
    """Reference implementation — brute force, no dependencies.

    At 113 chunks this is what the Colab comparison already did. Included as
    the baseline that shows what the other two are optimising."""

    def __init__(self):
        self.vectors = None
        self.chunks = []

    def add(self, vectors, chunks):
        self.vectors = np.asarray(vectors, dtype="float32")
        self.chunks = list(chunks)

    def query(self, vector, k=5, where=None):
        idx = range(len(self.chunks))
        if where:
            idx = [i for i in idx
                   if all(self.chunks[i].get(f) == v for f, v in where.items())]
            if not idx:
                return []
        sub = self.vectors[list(idx)]
        sims = sub @ np.asarray(vector, dtype="float32")
        order = np.argsort(-sims)[:k]
        keys = list(idx)
        return [self.chunks[keys[o]] for o in order]
class ChromaStore(Store):
    """Chroma: a database. Stores vectors with metadata, persists to disk,
    filters server-side via `where`."""

    def __init__(self, path=None, name="week2"):
        import chromadb
        client = chromadb.PersistentClient(path) if path else chromadb.Client()
        try:
            client.delete_collection(name)
        except Exception:
            pass
        self.col = client.create_collection(
            name, metadata={"hnsw:space": "cosine"})

    def add(self, vectors, chunks):
        self.col.add(
            ids=[str(i) for i in range(len(chunks))],
            embeddings=[v.tolist() for v in vectors],
            documents=[c["text"] for c in chunks],
            metadatas=[{k: ("" if v is None else v)
                        for k, v in c.items()
                        if k != "text" and not isinstance(v, list)}
                       for c in chunks],
        )
        self.chunks = list(chunks)

    def query(self, vector, k=5, where=None):
        res = self.col.query(query_embeddings=[vector.tolist()],
                             n_results=k, where=where or None)
        return [self.chunks[int(i)] for i in res["ids"][0]]


class FaissStore(Store):
    """FAISS: an index, not a database. No metadata, no filtering —
    metadata lives in a parallel list and is looked up by position."""

    def __init__(self):
        self.index = None
        self.chunks = []

    def add(self, vectors, chunks):
        import faiss
        v = np.asarray(vectors, dtype="float32")
        self.index = faiss.IndexFlatIP(v.shape[1])   # inner product = cosine on unit vectors
        self.index.add(v)
        self.chunks = list(chunks)

    def query(self, vector, k=5, where=None):
        q = np.asarray([vector], dtype="float32")
        if where:
            # FAISS cannot filter. Over-fetch and filter in Python.
            _, idx = self.index.search(q, min(len(self.chunks), k * 20))
            out = [self.chunks[i] for i in idx[0] if i >= 0]
            out = [c for c in out
                   if all(c.get(f) == v for f, v in where.items())]
            return out[:k]
        _, idx = self.index.search(q, k)
        return [self.chunks[i] for i in idx[0] if i >= 0]