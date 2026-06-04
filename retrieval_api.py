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

INDEX_NAME = "tank-storage-openai"

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

app = FastAPI()


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

    query_embedding = get_embedding(req.query)

    result = index.query(
        vector=query_embedding,
        top_k=5,
        include_metadata=True
    )

    contexts = []

    for match in result["matches"]:

        contexts.append(
            match["metadata"]["text"]
        )

    context_text = "\n\n".join(contexts)

    system_prompt = """
شما یک دستیار تخصصی مخازن ذخیره سازی نفت، گاز و پتروشیمی هستید.

فقط بر اساس اطلاعات ارائه شده پاسخ بده.

اگر پاسخ در متن موجود نبود بگو:

"اطلاعات کافی در منابع موجود یافت نشد."

پاسخ را به زبان فارسی و به صورت آموزشی و حرفه ای ارائه کن.
"""

    user_prompt = f"""
سوال:

{req.query}

منابع:

{context_text}
"""

    answer = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.2
    )

    final_answer = answer.choices[0].message.content

    return {
        "query": req.query,
        "answer": final_answer,
        "sources": contexts
    }