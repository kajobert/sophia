import sqlite3
import os
from datetime import datetime

DB_FILE = "memory.db"
MEMORY_DIR = "memory"

class MemoryManager:
    """
    Spravuje perzistentní paměť agenta pomocí SQLite databáze.
    """
    def __init__(self, db_path=None):
        if db_path is None:
            # Zajistí, že adresář pro paměť existuje
            os.makedirs(MEMORY_DIR, exist_ok=True)
            db_path = os.path.join(MEMORY_DIR, DB_FILE)

        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        """Vytvoří tabulky pro sessions a historii konverzace, pokud neexistují."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    task_prompt TEXT NOT NULL,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_index INTEGER NOT NULL,
                    request TEXT NOT NULL,
                    response TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                );
            """)
            self.conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_session_turn
                ON conversation_history (session_id, turn_index);
            """)

    def save_history(self, session_id: str, history: list[tuple[str, str]]):
        """
        Uloží kompletní historii konverzace pro dané sezení.
        Před uložením vymaže starou historii pro toto sezení.
        """
        with self.conn:
            # Nejprve vymažeme starou historii pro dané sezení
            self.conn.execute("DELETE FROM conversation_history WHERE session_id = ?", (session_id,))

            # Vložíme nové záznamy
            rows = [
                (session_id, i, request, response)
                for i, (request, response) in enumerate(history)
            ]
            self.conn.executemany(
                "INSERT INTO conversation_history (session_id, turn_index, request, response) VALUES (?, ?, ?, ?)",
                rows
            )

    def load_history(self, session_id: str) -> list[tuple[str, str]]:
        """Načte historii konverzace pro dané sezení."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT request, response FROM conversation_history WHERE session_id = ? ORDER BY turn_index ASC",
            (session_id,)
        )
        return cursor.fetchall()

    def save_session(self, session_id: str, task_prompt: str, summary: str):
        """Uloží shrnutí dokončeného úkolu do databáze."""
        query = "INSERT INTO sessions (session_id, task_prompt, summary) VALUES (?, ?, ?)"
        cursor = self.conn.cursor()
        cursor.execute(query, (session_id, task_prompt, summary))
        self.conn.commit()
        return cursor.lastrowid

    def get_relevant_memories(self, keywords: list[str], limit: int = 5) -> list[dict]:
        """
        Vyhledá relevantní vzpomínky na základě klíčových slov.
        Vrací seznam slovníků s detaily o session.
        """
        if not keywords:
            return []

        # Sestavení dynamického WHERE dotazu
        where_clauses = " OR ".join(["summary LIKE ?"] * len(keywords))
        query = f"SELECT task_prompt, summary, created_at FROM sessions WHERE {where_clauses} ORDER BY created_at DESC LIMIT ?"

        # Přidání '%' pro LIKE vyhledávání
        like_keywords = [f"%{kw}%" for kw in keywords]

        cursor = self.conn.cursor()
        cursor.execute(query, (*like_keywords, limit))

        rows = cursor.fetchall()
        memories = []
        for row in rows:
            memories.append({"task": row[0], "summary": row[1], "timestamp": row[2]})

        return memories

    def get_all_memories(self, limit: int = 100) -> list[dict]:
        """
        Získá všechny uložené vzpomínky (sessions), seřazené od nejnovější.
        """
        query = "SELECT task_prompt, summary, created_at FROM sessions ORDER BY created_at DESC LIMIT ?"
        cursor = self.conn.cursor()
        cursor.execute(query, (limit,))

        rows = cursor.fetchall()
        memories = []
        for row in rows:
            memories.append({"task": row[0], "summary": row[1], "timestamp": row[2]})

        return memories

    def close(self):
        """Uzavře spojení s databází."""
        if self.conn:
            self.conn.close()