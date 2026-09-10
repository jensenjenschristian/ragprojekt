from src.query import retrieve

for r in retrieve("Hvad er timeprisen for en elektrikersvend?",
                  where={"delaftale": "København"}):
    print(r["delaftale"], "|", r["section"], f"({r['distance']:.4f})")