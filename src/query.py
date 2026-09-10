from src.models import MODELS, DEFAULT_MODEL
import chromadb
from sentence_transformers import SentenceTransformer
import os
#use to silence HF warnings when you've already cached the model locally
#os.environ["HF_HUB_OFFLINE"] = "1"
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

cfg = MODELS[DEFAULT_MODEL]
model = SentenceTransformer(cfg["name"])
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection("tender")

def retrieve(question, k=5, where=None):
    q_vec = model.encode(cfg["query_prefix"] + question,
                         normalize_embeddings=True)
    res = collection.query(query_embeddings=[q_vec.tolist()],
                           n_results=k, where=where or None)
    out = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0],
                               res["distances"][0]):
        out.append({
            "text": doc,
            "source": meta["source"],
            "page": meta["page"],
            "pages": [int(p) for p in meta["pages"].split(",") if p],
            "section": meta["section"],
            "delaftale": meta["delaftale"],
            "distance": dist,
        })
    return out

#stage 5

#Brug udelukkende oplysningerne i konteksten nedenfor. Hvis konteksten ikke
#indeholder svaret, så sig det tydeligt — gæt ikke, og brug ikke din egen viden.


PROMPT = """Du er en assistent, der svarer på spørgsmål om et dansk udbudsmateriale.

Hvis konteksten kun henviser til et andet dokument, som ikke indgår i konteksten,
så oplys dette og gengiv ikke andet indhold som svar på spørgsmålet

Angiv altid kilde i formatet (dokumentnavn, side N) efter hver påstand.

KONTEKST:
{context}

SPØRGSMÅL: {question}

SVAR:"""


def build_context(results):
    parts = []
    for r in results:
        loc = f"{r['source']}, side {r['page']}"
        if r["section"]:
            loc += f", {r['section']}"
        if r["delaftale"]:
            loc += f", delaftale {r['delaftale']}"
        parts.append(f"[{loc}]\n{r['text']}")
    return "\n\n".join(parts)

def answer(question, k=5):
    results = retrieve(question, k=k)
    prompt = PROMPT.format(context=build_context(results), question=question)
    resp = llm.chat.completions.create(
        model="gpt-5.6-luna",
        messages=[{"role": "user", "content": prompt}],
       # temperature=0,
    )
    return resp.choices[0].message.content, results

#if __name__ == "__main__":
#    #question = "Hvor stor en andel af årsværkene skal udgøres af personer under oplæring?"
#    question = "Hvilke tekniske krav gælder for installationerne?"
#    for i, r in enumerate(retrieve(question), start=1):
#        print(f"\n[{i}] {r['source']} side {r['page']}  (distance {r['distance']:.4f})")
#        print(r["text"][:300].replace("\n", " "))

#Stage 5

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]
    retrieve_only = "-r" in args
    question = " ".join(a for a in args if a != "-r")

    if retrieve_only:
        for r in retrieve(question):
            loc = f"{r['source']} side {r['page']}"
            if r["delaftale"]:
                loc += f" [{r['delaftale']}]"
            if r["section"]:
                loc += f" — {r['section'][:40]}"
            print(f"\n{loc} ({r['distance']:.4f})")
            print(r["text"][:200].replace("\n", " "))
    else:
        text, results = answer(question)
        print(f"\n{text}\n")
        print("--- kilder ---")
        for i, r in enumerate(results, start=1):
            print(f"[{i}] {r['source']} side {r['page']} ({r['distance']:.4f})")