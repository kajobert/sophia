# scripts/inspect_queue.py
import sqlite3

conn = sqlite3.connect('.data/tasks.sqlite')
c = conn.cursor()
c.execute("SELECT id, created_at, priority, status, payload FROM tasks ORDER BY id DESC LIMIT 50")
rows = c.fetchall()
for r in rows:
    print(f"id={r[0]} priority={r[2]} status={r[3]} created_at={r[1]}")
    print(r[4][:400])
    print('---')
