import sqlite3
import os
from datetime import datetime
from .long_term_memory import LongTermMemory

DB_FILE = "memory.db"
MEMORY_DIR = "memory"

class MemoryManager:
    """
    Spravuje perzistentní paměť agenta pomocí SQLite databáze (pro strukturovaná data)
    a vektorové databáze ChromaDB (pro sémantické vyhledávání).
    """
    def __init__(self, db_path=None, ltm_db_path=None, ltm_collection_name=None):
        if db_path is None:
            os.makedirs(MEMORY_DIR, exist_ok=True)
            db_path = os.path.join(MEMORY_DIR, DB_FILE)

        self.conn = sqlite3.connect(db_path)
        self._create_table()

        # Inicializace dlouhodobé sémantické paměti s možností přepsání cest pro testování
        try:
            self.ltm = LongTermMemory(
                db_path_override=ltm_db_path,
                collection_name_override=ltm_collection_name
            )
        except Exception as e:
            self.ltm = None
            print(f"Chyba: Nepodařilo se inicializovat LongTermMemory: {e}")


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
        """
        with self.conn:
            self.conn.execute("DELETE FROM conversation_history WHERE session_id = ?", (session_id,))
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
        """
        Uloží shrnutí dokončeného úkolu do databáze a do vektorové paměti.
        """
        # Uložení do SQLite
        query = "INSERT INTO sessions (session_id, task_prompt, summary) VALUES (?, ?, ?)"
        cursor = self.conn.cursor()
        cursor.execute(query, (session_id, task_prompt, summary))
        self.conn.commit()

        # Uložení do vektorové paměti
        if self.ltm and summary:
            metadata = {"session_id": session_id, "task": task_prompt, "timestamp": datetime.now().isoformat()}
            self.ltm.add_memory(summary, metadata)

        return cursor.lastrowid

    def get_relevant_memories(self, query: str, limit: int = 5) -> list[dict]:
        """
        Vyhledá relevantní vzpomínky pomocí sémantického vyhledávání.
        """
        if not self.ltm:
            print("Varování: LongTermMemory není k dispozici. Vyhledávání není možné.")
            return []

        results = self.ltm.search_memory(query, n_results=limit)

        memories = []
        if results and results.get('documents'):
            # Spojení dokumentů a metadat do jednoho seznamu slovníků
            docs = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]

            for i, doc in enumerate(docs):
                meta = metadatas[i]
                memories.append({
                    "task": meta.get("task", "N/A"),
                    "summary": doc,
                    "timestamp": meta.get("timestamp", "N/A")
                })
        return memories


    def get_all_memories(self, limit: int = 100) -> list[dict]:
        """
        Získá všechny uložené vzpomínky (sessions) z SQLite, seřazené od nejnovější.
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
        """Uzavře spojení s oběma databázemi."""
        if self.conn:
            self.conn.close()
        if self.ltm:
            self.ltm.shutdown()