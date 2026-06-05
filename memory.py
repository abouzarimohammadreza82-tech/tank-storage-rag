from db import conn, cursor
import json

def get_history(chat_id):

    cursor.execute(
        "SELECT role, content FROM messages WHERE chat_id=?",
        (chat_id,)
    )

    rows = cursor.fetchall()

    return [
        {"role": r[0], "content": r[1]}
        for r in rows
    ]


def add_message(chat_id, role, content):

    cursor.execute(
        "INSERT INTO messages VALUES (?, ?, ?)",
        (chat_id, role, content)
    )

    conn.commit()