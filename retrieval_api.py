import os

from fastapi import FastAPI
from pydantic import BaseModel

from openai import OpenAI
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

# =====================================
# CONFIG
# =====================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME", "tank-storage-openai")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing")

# =====================================
# OPENAI
# =====================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)

# =====================================
# EMBEDDING
# =====================================

def get_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding

# =====================================
# PINECONE
# =====================================

pc = Pinecone(
    api_key=PINECONE_API_KEY
)

index = pc.Index(INDEX_NAME)

# =====================================
# FASTAPI
# =====================================

app = FastAPI()


class SearchRequest(BaseModel):
    query: str


@app.get("/")
def root():
    return {
        "status": "ok",
        "index": INDEX_NAME
    }


@app.post("/search")
def search(req: SearchRequest):

    query_embedding = get_embedding(req.query)

    result = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )

    contexts = []

    for match in result["matches"]:
        contexts.append({
            "score": float(match["score"]),
            "text": match["metadata"]["text"]
        })

    return {
        "query": req.query,
        "contexts": contexts
    }