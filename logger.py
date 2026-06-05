from db import conn, cursor
from datetime import datetime

def save_log(user_id, query, answer):

    cursor.execute(
        "INSERT INTO logs VALUES (?, ?, ?, ?)",
        (user_id, query, answer, datetime.utcnow().isoformat())
    )

    conn.commit()