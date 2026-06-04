from fastapi import FastAPI
from pydantic import BaseModel

from openai import OpenAI
from pinecone import Pinecone

from dotenv import load_dotenv
import os

load_dotenv()

# =====================================
# CONFIG
# =====================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found")

if not INDEX_NAME:
    raise ValueError("INDEX_NAME not found")

# =====================================
# OPENAI
# =====================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)

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

app = FastAPI(
    title="Tank Storage RAG",
    version="1.0.0"
)


class SearchRequest(BaseModel):
    query: str


@app.get("/")
def root():

    return {
        "status": "ok",
        "service": "Tank Storage RAG"
    }


def get_embedding(text):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


@app.post("/search")
def search(req: SearchRequest):

    query_embedding = get_embedding(
        req.query
    )

    result = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )

    contexts = []
    sources = []

    for match in result["matches"]:

        score = float(match["score"])

        if score > 0.45:

            contexts.append(
                match["metadata"]["text"]
            )

            if "source" in match["metadata"]:

                sources.append(
                    match["metadata"]["source"]
                )

    if len(contexts) == 0:

        return {
            "answer": "من فقط در زمینه مخازن ذخیره سازی، طراحی، ساخت، جوشکاری، بازرسی و استانداردهای API 650 ، API 620 و API 653 پاسخ می‌دهم.",
            "sources": []
        }

    context_text = "\n\n".join(contexts)

    prompt = f"""
شما یک کارشناس ارشد مخازن ذخیره سازی هستید.

فقط و فقط از اطلاعات موجود در Context استفاده کن.

اگر پاسخ در Context وجود ندارد بگو:

"اطلاعات کافی در پایگاه دانش موجود نیست."

Context:
{context_text}

Question:
{req.query}

قوانین:

- پاسخ فارسی باشد.
- پاسخ حرفه‌ای باشد.
- از کپی مستقیم متن Context خودداری کن.
- اطلاعات جدید از دانش خودت اضافه نکن.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": list(set(sources))
    }