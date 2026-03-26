import sqlite3
import json

conn = sqlite3.connect('chat_history.db')
c = conn.cursor()
rows = c.execute("SELECT role, content, standalone_content FROM messages").fetchall()
formatted = [{"role": r[0], "content": r[1], "standalone_content": r[2]} for r in rows]

with open('db_dump.json', 'w', encoding='utf-8') as f:
    json.dump(formatted, f, indent=4, ensure_ascii=False)
