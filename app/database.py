import sqlite3

# Initialize database
def init_db():
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            user_id TEXT,
            user_message TEXT,
            bot_response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# Save user conversation
def save_memory(user_id, user_message, bot_response):
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO memory (user_id, user_message, bot_response) 
        VALUES (?, ?, ?)
    """, (user_id, user_message, bot_response))
    conn.commit()
    conn.close()

# Retrieve past interactions
def get_past_messages(user_id, limit=5):
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()
    c.execute("""
        SELECT user_message, bot_response FROM memory 
        WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
    """, (user_id, limit))
    messages = c.fetchall()
    conn.close()
    return messages
