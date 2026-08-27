#from sentence_transformers import SentenceTransformer
#first run
#model = SentenceTransformer("intfloat/multilingual-e5-small")
#v = model.encode("passage: Leverandøren skal sikre stabil drift.")
#print(v.shape)

#second run

from sentence_transformers import SentenceTransformer, util


model = SentenceTransformer("intfloat/multilingual-e5-small")

sentences = [
    "passage: Leverandøren skal levere ydelsen inden 10 arbejdsdage.",
    "passage: Leverandøren bør levere ydelsen inden 10 arbejdsdage.",
    "passage: Leverandøren skal fakturere elektronisk via NemHandel.",
]

emb = model.encode(sentences)
print(f"skal vs bør  (same clause, opposite obligation): {util.cos_sim(emb[0], emb[1]).item():.4f}")
print(f"skal vs skal (different clause, same document):  {util.cos_sim(emb[0], emb[2]).item():.4f}")


