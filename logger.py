from datetime import datetime, timezone
from supabase_client import supabase


def save_log(user_id, query, answer, response_time_ms=0):
    try:
        supabase.table("logs").insert({
            "user_id": user_id,
            "query": query,
            "answer": answer,
            "response_time_ms": response_time_ms,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
    except:
        pass