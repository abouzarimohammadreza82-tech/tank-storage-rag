from supabase_client import supabase


def get_history(chat_id):

    result = (
        supabase
        .table("chat_history")
        .select("*")
        .eq("chat_id", chat_id)
        .order("created_at")
        .limit(10)
        .execute()
    )

    rows = result.data or []

    return [
        {
            "role": row["role"],
            "content": row["content"]
        }
        for row in rows
    ]


def add_message(chat_id, role, content):

    supabase.table(
        "chat_history"
    ).insert({
        "chat_id": chat_id,
        "role": role,
        "content": content
    }).execute()