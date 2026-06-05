from supabase_client import supabase
import traceback

def get_history(chat_id):
    try:
        # تبدیل chat_id به عدد برای مطابقت با ستون int8
        chat_id_int = int(chat_id)

        result = (
            supabase
            .table("chat_history")
            .select("*")
            .eq("chat_id", chat_id_int)
            .order("created_at")
            .limit(10)
            .execute()
        )

        rows = result.data or []

        return [
            {
                "role": row.get("role", "system"),
                "content": row.get("content", "")
            }
            for row in rows
        ]

    except Exception as e:
        # چاپ لاگ برای دیباگ
        print("Error in get_history:", traceback.format_exc())
        # برگرداندن لیست خالی اگر مشکلی پیش آمد
        return []

def add_message(chat_id, role, content):
    try:
        chat_id_int = int(chat_id)

        supabase.table("chat_history").insert({
            "chat_id": chat_id_int,
            "role": role,
            "content": content
        }).execute()

    except Exception as e:
        # چاپ لاگ برای دیباگ
        print("Error in add_message:", traceback.format_exc())