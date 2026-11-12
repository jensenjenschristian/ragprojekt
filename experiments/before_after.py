import numpy as np
from sentence_transformers import SentenceTransformer

from src.retrieve import dense_search
from src.rerank import CohereReranker
from src.ingest import build_chunks
from src.models import MODELS
from src.eval_specs import SPECS, QUESTIONS
from src.evaluate import matches

cfg = MODELS["bge-m3"]
chunks = build_chunks(model_key="e5-small")
E = np.load("cache/bge-m3_structural.npy")
embed = SentenceTransformer(cfg["name"], device="cpu")
rr = CohereReranker("rerank-v5.0-pro")


def row(rank, i, score, spec):
    c = chunks[i]
    loc = c["source"]
    if c["delaftale"]:
        loc += f" [{c['delaftale']}]"
    if c["section"]:
        loc += f" — {c['section']}"
    mark = " **← correct**" if matches(c, spec) else ""
    text = c["text"][:90].replace("\n", " ").replace("|", "/")
    return f"| {rank} | {score:.3f} | {loc}{mark} | {text}… |"


lines = ["# Week 3 — before/after examples", "",
         "Before: dense BGE-M3 (cosine). After: dense top-10 → Cohere rerank-v5.0-pro reading "
         "delaftale + section heading + text (relevance score). Scores are on different scales.", ""]
for qid in ["Q2", "Q9"]:
    q, spec = QUESTIONS[qid], SPECS[qid]
    dense = dense_search(E, embed.encode(cfg["query_prefix"] + q, normalize_embeddings=True), n=10)
    after = rr.rerank(q, chunks, [i for i, _ in dense], with_heading=True, with_delaftale=True)
    lines += [f"## {qid}: {q}", ""]
    for title, lst in [("Before — dense", dense[:5]), ("After — rerank", after)]:
        lines += [f"**{title}**", "", "| # | score | chunk | text |", "|---|---|---|---|"]
        lines += [row(r, i, s, spec) for r, (i, s) in enumerate(lst, 1)]
        lines.append("")

with open("notes/week3-before-after.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))