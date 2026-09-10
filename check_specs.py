from transformers import AutoTokenizer

from src.parse_docling import load_corpus
from src.chunking import chunk_structural
from src.evaluate import matches
from src.eval_specs import SPECS, QUESTIONS

print("specs:", len(SPECS), "| questions:", len(QUESTIONS))
print("scored:", sorted(k for k in SPECS if SPECS[k] is not None))
print("missing questions:", [k for k in SPECS if SPECS[k] and k not in QUESTIONS])

tok = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-small")
chunks = chunk_structural(load_corpus(), tok)

print(f"\n--- match counts against {len(chunks)} structural chunks ---")
for qid, spec in SPECS.items():
    if spec is None:
        continue
    hits = [i for i, c in enumerate(chunks, 1) if matches(c, spec)]
    print(f"{qid:4} {len(hits):2} match(es) at {hits[:3]}")