from fastapi import FastAPI
from pydantic import BaseModel

from openai import OpenAI
from pinecone import Pinecone

from dotenv import load_dotenv
import os

from memory import (
    get_history,
    add_message
)

from rate_limit import allow_request

from logger import save_log

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
# SYSTEM PROMPT
# =====================================

SYSTEM_PROMPT = """
شما کارشناس ارشد مخازن ذخیره سازی هستید.

فقط از اطلاعات موجود در Context استفاده کن.

اگر پاسخ در Context پیدا نشد بگو:

اطلاعات کافی در پایگاه دانش موجود نیست.

از دانش خود چیزی اضافه نکن.

پاسخ‌ها باید:
- فارسی باشند
- دقیق باشند
- حرفه‌ای باشند
- ساختاریافته باشند
"""

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
    version="2.0.0"
)

# =====================================
# REQUEST MODEL
# =====================================

class SearchRequest(BaseModel):
    query: str
    chat_id: int
    user_id: int

# =====================================
# ROOT
# =====================================

@app.get("/")
def root():

    return {
        "status": "ok",
        "service": "Tank Storage RAG"
    }

# =====================================
# EMBEDDING
# =====================================

def get_embedding(text):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding

# =====================================
# SEARCH
# =====================================

@app.post("/search")
def search(req: SearchRequest):

    # -----------------------------
    # RATE LIMIT
    # -----------------------------

    if not allow_request(req.user_id):

        return {
            "answer": "⏳ لطفاً چند ثانیه صبر کنید و دوباره تلاش نمایید.",
            "sources": []
        }

    # -----------------------------
    # MEMORY
    # -----------------------------

    history = get_history(req.chat_id)

    # -----------------------------
    # EMBEDDING
    # -----------------------------

    query_embedding = get_embedding(
        req.query
    )

    # -----------------------------
    # PINECONE SEARCH
    # -----------------------------

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

    # -----------------------------
    # NO CONTEXT FOUND
    # -----------------------------

    if len(contexts) == 0:

        return {
            "answer":
            "اطلاعات کافی در پایگاه دانش موجود نیست.",
            "sources": []
        }

    # -----------------------------
    # BUILD CONTEXT
    # -----------------------------

    context_text = "\n\n".join(contexts)

    prompt = f"""
Context:
{context_text}

Question:
{req.query}

قوانین:

- فقط از Context استفاده کن.
- اگر پاسخ وجود ندارد اعلام کن.
- اطلاعات جدید اضافه نکن.
- پاسخ فارسی و حرفه‌ای باشد.
"""

    # -----------------------------
    # BUILD MESSAGES
    # -----------------------------

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # -----------------------------
    # GPT
    # -----------------------------

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=messages
    )

    answer = response.choices[0].message.content

    # -----------------------------
    # SAVE MEMORY
    # -----------------------------

    add_message(
        req.chat_id,
        "user",
        req.query
    )

    add_message(
        req.chat_id,
        "assistant",
        answer
    )

    # -----------------------------
    # LOGGING
    # -----------------------------

    save_log(
        req.user_id,
        req.query,
        answer
    )

    # -----------------------------
    # LONG ANSWERS
    # -----------------------------

    if len(answer) > 3500:

        answer = answer[:3500] + "..."

    # -----------------------------
    # RESPONSE
    # -----------------------------

    return {
        "answer": answer,
        "sources": list(set(sources))
    }