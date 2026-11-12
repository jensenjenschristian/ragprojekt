import os
import cohere
from dotenv import load_dotenv

load_dotenv()
co = cohere.ClientV2(api_key=os.environ["COHERE_API_KEY"])
r = co.rerank(
    model="rerank-v5.0-pro",
    query="Hvilket nummer skal man ringe til, hvis der går ild i noget?",
    documents=["Fakturaen skal indeholde EAN-nummer.",
               "I tilfælde af ulykke eller brand skal du ringe til 1-1-2."],
    top_n=2,
)
print(r)