import time
from fastapi import FastAPI
from pydantic import BaseModel

from openai import OpenAI
from pinecone import Pinecone

from config import (
    OPENAI_API_KEY,
    PINECONE_API_KEY,
    INDEX_NAME
)

from memory import get_history, add_message
from rate_limit import allow_request
from logger import save_log

# =====================================
# INIT
# =====================================

client = OpenAI(api_key=OPENAI_API_KEY)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

app = FastAPI(
    title="Tank Storage RAG",
    version="3.0.0"
)

# =====================================
# SYSTEM PROMPT
# =====================================

SYSTEM_PROMPT = """
شما کارشناس ارشد مخازن ذخیره سازی هستید.

قوانین:
- فقط از Context استفاده کن
- اگر پاسخ وجود ندارد بگو اطلاعات کافی نیست
- چیزی اضافه نکن
- پاسخ فارسی، دقیق و حرفه‌ای باشد
"""

# =====================================
# MODEL
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
    return {"status": "ok", "service": "Tank Storage RAG"}


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
# SEARCH ENDPOINT
# =====================================

@app.post("/search")
def search(req: SearchRequest):

    start_time = time.time()

    # -----------------------------
    # RATE LIMIT
    # -----------------------------
    if not allow_request(req.user_id):
        return {
            "answer": "⏳ لطفاً چند ثانیه صبر کنید.",
            "sources": []
        }

    # -----------------------------
    # SAVE USER MESSAGE (safe-first)
    # -----------------------------
    add_message(req.chat_id, "user", req.query)

    # -----------------------------
    # MEMORY
    # -----------------------------
    history = get_history(req.chat_id)

    # -----------------------------
    # EMBEDDING
    # -----------------------------
    query_embedding = get_embedding(req.query)

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

    for match in result.get("matches", []):
        score = float(match.get("score", 0))

        if score > 0.45:
            metadata = match.get("metadata", {})

            contexts.append(metadata.get("text", ""))

            if metadata.get("source"):
                sources.append(metadata["source"])

    # -----------------------------
    # NO CONTEXT
    # -----------------------------
    if not contexts:
        answer = "اطلاعات کافی در پایگاه دانش موجود نیست."

        add_message(req.chat_id, "assistant", answer)
        save_log(req.user_id, req.query, answer, 0)

        return {
            "answer": answer,
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
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": prompt}
    ]

    # -----------------------------
    # GPT CALL
    # -----------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=messages
    )

    answer = response.choices[0].message.content

    response_time_ms = int((time.time() - start_time) * 1000)

    # -----------------------------
    # SAVE ASSISTANT MESSAGE
    # -----------------------------
    add_message(req.chat_id, "assistant", answer)

    # -----------------------------
    # LOGGING (safe)
    # -----------------------------
    save_log(
        req.user_id,
        req.query,
        answer,
        response_time_ms
    )

    # -----------------------------
    # LIMIT OUTPUT SIZE
    # -----------------------------
    if len(answer) > 3500:
        answer = answer[:3500] + "..."

    # -----------------------------
    # RESPONSE
    # -----------------------------
    return {
        "answer": answer,
        "sources": list(dict.fromkeys(sources))
    }