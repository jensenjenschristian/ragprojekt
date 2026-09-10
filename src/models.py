MODELS = {
    "e5-small": {
        "name": "intfloat/multilingual-e5-small",
        "passage_prefix": "passage: ",
        "query_prefix": "query: ",
    },
    "bge-m3": {
        "name": "BAAI/bge-m3",
        "passage_prefix": "",
        "query_prefix": "",
    },
}

# e5-small until the 16 GB machine; BGE-M3 scored MRR 0.768 vs 0.697
# on structural chunking (week2-findings.md §11) but needs ~2.3 GB.
DEFAULT_MODEL = "e5-small"