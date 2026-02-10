import sqlite3

conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT,
    last_video_id TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER,
    channel_id TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    user_id INTEGER PRIMARY KEY,
    interval INTEGER DEFAULT 5
)
""")

conn.commit()
