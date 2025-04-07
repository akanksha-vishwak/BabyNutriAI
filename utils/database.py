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

def init_facts_table():
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            user_id TEXT,
            key TEXT,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, key)
        )
    """)
    conn.commit()
    conn.close()

def update_fact(user_id, key, value):
    if value in [None, "None", "", [], {}]:
        return  # don't save junk

    if isinstance(value, list):
        value = ", ".join(value)
    else:
        value = str(value)

    conn = sqlite3.connect("memory.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO facts (user_id, key, value)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, key) DO UPDATE SET
            value = excluded.value,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, key, value))
    conn.commit()
    conn.close()



def get_user_facts(user_id):
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()
    c.execute("SELECT key, value FROM facts WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return {k: v for k, v in rows}
