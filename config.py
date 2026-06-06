import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# API KEYS
# =========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# =========================
# PINECONE
# =========================

INDEX_NAME = os.getenv("INDEX_NAME")

# =========================
# SUPABASE
# =========================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# =========================
# VALIDATION
# =========================

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY is missing")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase config is missing")