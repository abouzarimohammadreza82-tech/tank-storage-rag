import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# Chat memory
cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    chat_id INTEGER,
    role TEXT,
    content TEXT
)
""")

# Rate limit
cursor.execute("""
CREATE TABLE IF NOT EXISTS ratelimit (
    user_id INTEGER PRIMARY KEY,
    last_time REAL
)
""")

# Logs
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    user_id INTEGER,
    query TEXT,
    answer TEXT,
    time TEXT
)
""")

conn.commit()