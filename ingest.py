import os
import uuid

from pptx import Presentation

from openai import OpenAI
from pinecone import Pinecone
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv

load_dotenv()

# =====================================
# CONFIG
# =====================================

DATA_DIR = "data"

import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")

# =====================================
# OPENAI
# =====================================

client = OpenAI(api_key=OPENAI_API_KEY)


def get_embedding(text):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


# =====================================
# PPT EXTRACTION
# =====================================

def extract_text_from_pptx(filepath):

    prs = Presentation(filepath)

    slides_text = []

    for i, slide in enumerate(prs.slides):

        slide_content = []

        for shape in slide.shapes:

            if not hasattr(shape, "text"):
                continue

            text = shape.text.strip()

            if text:
                slide_content.append(text)

        if slide_content:

            slides_text.append(
                f"[اسلاید {i+1}]\n"
                + "\n".join(slide_content)
            )

    return slides_text


# =====================================
# BUILD VECTOR DB
# =====================================

def build_vector_db():

    all_texts = []

    for filename in os.listdir(DATA_DIR):

        if filename.endswith(".pptx"):

            filepath = os.path.join(DATA_DIR, filename)

            print(f"\nProcessing: {filename}")

            texts = extract_text_from_pptx(filepath)

            all_texts.extend(texts)

    if not all_texts:

        print("No PPTX files found")
        return

    print(f"\nSlides Found: {len(all_texts)}")

    # نمایش نمونه استخراج

    for text in all_texts[:3]:

        print("\n" + "=" * 50)
        print(text[:1000])

    # =====================================
    # CHUNKING
    # =====================================

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=[
            "\n\n",
            "\n",
            " ",
            ""
        ]
    )

    chunks = splitter.create_documents(all_texts)

    print(f"\nChunks Created: {len(chunks)}")

    # =====================================
    # PINECONE
    # =====================================

    pc = Pinecone(
        api_key=PINECONE_API_KEY
    )

    index = pc.Index(INDEX_NAME)

    vectors = []

    for i, chunk in enumerate(chunks):

        print(f"Embedding {i+1}/{len(chunks)}")

        embedding = get_embedding(
            chunk.page_content
        )

        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embedding,
            "metadata": {
                "text": chunk.page_content,
                "source": "tank_storage"
            }
        })

        if len(vectors) >= 50:

            index.upsert(vectors=vectors)

            vectors = []

    if vectors:

        index.upsert(vectors=vectors)

    print("\nUpload completed successfully")


if __name__ == "__main__":

    build_vector_db()