"""A minimal SQLite-backed persistent task queue for MVP.

This is intentionally small and synchronous on the DB side (sqlite3). It
provides an async-friendly API by using asyncio.to_thread for DB calls so
it can be polled in an async worker loop.

Schema:
  tasks(id INTEGER PRIMARY KEY, created_at TEXT, priority INTEGER, status TEXT, payload TEXT)

Status: pending, running, done, failed
"""
import sqlite3
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SimplePersistentQueue:
    def __init__(self, db_path: str | Path = ".data/tasks.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            # Increased timeout from 30s to 60s for WSL/Windows mount disk I/O
            self._conn = sqlite3.connect(str(self.db_path), timeout=60, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._initialize()
        return self._conn

    def _initialize(self) -> None:
        c = self._conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT,
                priority INTEGER DEFAULT 100,
                status TEXT DEFAULT 'pending',
                payload TEXT
            )
            """
        )
        self._conn.commit()

    def enqueue(self, payload: Dict[str, Any], priority: int = 100) -> int:
        """Enqueue a task with retry logic for disk I/O errors on WSL/Windows."""
        max_retries = 3
        retry_delay = 0.5  # seconds
        
        for attempt in range(max_retries):
            try:
                conn = self._connect()
                c = conn.cursor()
                now = datetime.utcnow().isoformat()
                c.execute(
                    "INSERT INTO tasks (created_at, priority, status, payload) VALUES (?, ?, 'pending', ?)",
                    (now, int(priority), json.dumps(payload)),
                )
                conn.commit()
                return c.lastrowid
            except sqlite3.OperationalError as e:
                if "disk I/O error" in str(e) and attempt < max_retries - 1:
                    logger.warning(
                        f"⚠️ Disk I/O error on enqueue (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                    # Close and reopen connection on retry
                    if self._conn:
                        try:
                            self._conn.close()
                        except Exception:
                            pass
                        self._conn = None
                else:
                    logger.error(f"❌ Failed to enqueue task after {max_retries} attempts: {e}")
                    raise

    def dequeue_and_lock(self) -> Optional[Dict[str, Any]]:
        """Atomically find one pending task, mark running, and return it."""
        conn = self._connect()
        c = conn.cursor()

        # Select one pending task by priority and id
        c.execute(
            "SELECT id, payload FROM tasks WHERE status = 'pending' ORDER BY priority ASC, id ASC LIMIT 1"
        )
        row = c.fetchone()
        if not row:
            return None

        task_id = row["id"]
        # Attempt to mark running only if still pending
        c.execute("UPDATE tasks SET status = 'running' WHERE id = ? AND status = 'pending'", (task_id,))
        if c.rowcount == 0:
            # someone else claimed it
            conn.commit()
            return None

        conn.commit()

        payload = json.loads(row["payload"])
        return {"id": task_id, "payload": payload}

    def mark_done(self, task_id: int) -> None:
        conn = self._connect()
        c = conn.cursor()
        c.execute("UPDATE tasks SET status = 'done' WHERE id = ?", (task_id,))
        conn.commit()

    def mark_failed(self, task_id: int, reason: str | None = None) -> None:
        conn = self._connect()
        c = conn.cursor()
        c.execute("UPDATE tasks SET status = 'failed' WHERE id = ?", (task_id,))
        # Optionally append failure note to payload
        if reason:
            c.execute("SELECT payload FROM tasks WHERE id = ?", (task_id,))
            row = c.fetchone()
            if row:
                try:
                    payload = json.loads(row[0])
                except Exception:
                    payload = {"_raw": row[0]}
                payload.setdefault("_errors", []).append({"when": datetime.utcnow().isoformat(), "reason": str(reason)})
                c.execute("UPDATE tasks SET payload = ? WHERE id = ?", (json.dumps(payload), task_id))

        conn.commit()

    def pending_count(self) -> int:
        conn = self._connect()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'pending'")
        row = c.fetchone()
        return int(row[0]) if row else 0
