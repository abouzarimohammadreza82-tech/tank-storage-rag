import time
from db import conn, cursor

def allow_request(user_id):

    now = time.time()

    cursor.execute(
        "SELECT last_time FROM ratelimit WHERE user_id=?",
        (user_id,)
    )

    row = cursor.fetchone()

    if row and now - row[0] < 2:
        return False

    cursor.execute("""
    INSERT INTO ratelimit(user_id, last_time)
    VALUES (?, ?)
    ON CONFLICT(user_id)
    DO UPDATE SET last_time=excluded.last_time
    """, (user_id, now))

    conn.commit()

    return True