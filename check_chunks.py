from transformers import AutoTokenizer
from src.parse_docling import load_corpus
from src.chunking import chunk_structural
from src.models import MODELS

els = load_corpus()
print(len(els), "elements (expect 601)")

out = {}
for key in ["e5-small", "bge-m3"]:
    tok = AutoTokenizer.from_pretrained(MODELS[key]["name"])
    out[key] = chunk_structural(els, tok)
    print(f"{key}: {len(out[key])} chunks (expect 113)")

same = [c["text"] for c in out["e5-small"]] == [c["text"] for c in out["bge-m3"]]
print("identical chunk texts:", same)