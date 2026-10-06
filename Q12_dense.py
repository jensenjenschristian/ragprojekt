import numpy as np
from sentence_transformers import SentenceTransformer
from src.ingest import build_chunks
from src.models import MODELS
from src.eval_specs import QUESTIONS

cfg = MODELS["bge-m3"]
chunks = build_chunks(model_key="e5-small")
E = np.load("cache/bge-m3_structural.npy")
model = SentenceTransformer(cfg["name"], device="cpu")

q = QUESTIONS[[k for k in QUESTIONS if str(k).lstrip("Qq") == "12"][0]]
sims = E @ model.encode(cfg["query_prefix"] + q, normalize_embeddings=True)
for i in np.argsort(-sims)[:3]:
    c = chunks[i]
    print(f"{sims[i]:.4f}  {c['source']} p{c['page']} pages={c['pages']}  {c['section']}")
    print(f"        {c['text'][:120]!r}")