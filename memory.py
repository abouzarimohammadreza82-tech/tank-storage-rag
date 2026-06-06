from supabase_client import supabase


def get_history(chat_id: int):
    try:
        result = (
            supabase.table("chat_history")
            .select("*")
            .eq("chat_id", chat_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        rows = list(reversed(result.data or []))

        return [
            {
                "role": r.get("role"),
                "content": r.get("content")
            }
            for r in rows
        ]
    except:
        return []


def add_message(chat_id: int, role: str, content: str):
    try:
        supabase.table("chat_history").insert({
            "chat_id": chat_id,
            "role": role,
            "content": content
        }).execute()
    except:
        pass