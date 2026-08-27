# RAG — Week 1: A Naive Pipeline

Your first end-to-end Retrieval-Augmented Generation system. By the end you'll ask a
question at the command line and get an answer grounded in your own documents.

Everything runs **locally and free** via Ollama. No API keys required.

## What you'll build

```
                 INGESTION (offline, run once)              QUERY (online, every question)
   docs/  ──►  load ──► chunk ──► embed ──► store          question ──► embed ──► search
                                            │                                      │
                                            ▼                                      ▼
                                      Chroma vector DB  ◄─────────────────────  top-k chunks
                                                                                   │
                                                                                   ▼
                                                              prompt (question + chunks) ──► Ollama ──► answer
```

Keep the two paths (ingestion vs query) separate in your head — you'll carry that split
through the whole course.

## Repo layout

```
rag-week1/
├── README.md            ← you are here
├── WALKTHROUGH.md       ← paste-along guide: build the code block by block
├── requirements.txt     ← Python deps
├── .env.example         ← copy to .env if/when you try the hosted swap
├── .gitignore
├── data/                ← drop your PDFs / .md / .txt files here
│   └── .gitkeep
└── src/                 ← empty on purpose — you'll create the .py files as you go
    └── .gitkeep
```

The `src/` folder is intentionally empty. WALKTHROUGH.md gives you each code block to
paste into the file it names, so you can run and test as you go.

## Setup

1. Install [Ollama](https://ollama.com), then pull the models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text
   ```
2. Create and activate a virtual environment, then install deps:
   ```bash
   python -m venv .venv
   # Windows:  .venv\Scripts\activate
   # macOS/Linux:  source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Put a few documents (PDF, `.md`, or `.txt`) in `data/`.
4. Open **WALKTHROUGH.md** and start pasting.

## Done when

- `python src/ingest.py` builds a local Chroma index from your `data/` files.
- `python src/query.py "your question"` returns an answer that cites its sources.
