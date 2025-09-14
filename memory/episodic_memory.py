# /memory/episodic_memory.py
"""
Modul pro správu epizodické paměti Sophie.
Tato paměť ukládá konkrétní události a zážitky v chronologickém pořadí.
Využívá databázi SQLite pro jednoduchost a efektivitu.
"""

import sqlite3
import os
from datetime import datetime

class EpisodicMemory:
    """
    Třída pro správu epizodické paměti pomocí SQLite.
    """
    def __init__(self, db_path='memory/sophia_episodic.db'):
        """
        Inicializuje připojení k databázi a zajistí existenci tabulky.
        """
        # Zajistíme, že adresář pro databázi existuje
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        """
        Vytvoří tabulku 'memories', pokud ještě neexistuje.
        Tabulka obsahuje sloupce pro id, timestamp, obsah, typ, váhu a etický koeficient.
        """
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                ethos_coefficient REAL DEFAULT 0.0
            )
        """)
        self.connection.commit()

    def add_memory(self, content, mem_type):
        """
        Přidá novou vzpomínku do databáze.

        Args:
            content (str): Obsah vzpomínky.
            mem_type (str): Typ vzpomínky (např. 'user_interaction', 'self_reflection').

        Returns:
            int: ID nově přidané vzpomínky.
        """
        timestamp = datetime.now()
        self.cursor.execute("""
            INSERT INTO memories (timestamp, content, type)
            VALUES (?, ?, ?)
        """, (timestamp, content, mem_type))
        self.connection.commit()
        return self.cursor.lastrowid

    def access_memory(self, memory_id):
        """
        Načte vzpomínku a zvýší její váhu o 0.1.

        Args:
            memory_id (int): ID vzpomínky, ke které se přistupuje.

        Returns:
            dict: Slovník s daty vzpomínky, nebo None, pokud nebyla nalezena.
        """
        # Nejprve načteme vzpomínku
        self.cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
        row = self.cursor.fetchone()

        if row:
            # Zvýšíme váhu
            new_weight = row[4] + 0.1  # index 4 je 'weight'
            self.cursor.execute("UPDATE memories SET weight = ? WHERE id = ?", (new_weight, memory_id))
            self.connection.commit()

            # Vrátíme data jako slovník pro snadnější použití
            memory_data = {
                "id": row[0],
                "timestamp": row[1],
                "content": row[2],
                "type": row[3],
                "weight": new_weight, # Vracíme aktualizovanou váhu
                "ethos_coefficient": row[5]
            }
            return memory_data
        else:
            return None

    def memory_decay(self):
        """
        Placeholder pro budoucí implementaci mechanismu blednutí vzpomínek.
        Tato funkce bude periodicky snižovat váhu všech vzpomínek.
        """
        pass

    def read_last_n_memories(self, n=10):
        """
        Přečte posledních N vzpomínek z databáze.

        Args:
            n (int): Počet vzpomínek k načtení.

        Returns:
            list: Seznam slovníků s daty posledních N vzpomínek.
        """
        self.cursor.execute("SELECT * FROM memories ORDER BY timestamp DESC LIMIT ?", (n,))
        rows = self.cursor.fetchall()

        memories = []
        for row in rows:
            memories.append({
                "id": row[0],
                "timestamp": row[1],
                "content": row[2],
                "type": row[3],
                "weight": row[4],
                "ethos_coefficient": row[5]
            })
        return memories

    def add_task(self, description):
        """
        Přidá nový úkol do epizodické paměti.

        Args:
            description (str): Popis úkolu.

        Returns:
            int: ID nově přidaného úkolu.
        """
        return self.add_memory(description, "NEW_TASK")

    def get_next_task(self):
        """
        Najde nejstarší nový úkol, označí ho jako probíhající a vrátí ho.
        """
        self.cursor.execute("SELECT * FROM memories WHERE type = 'NEW_TASK' ORDER BY timestamp ASC LIMIT 1")
        row = self.cursor.fetchone()

        if row:
            task_id = row[0]
            self.update_task_status(task_id, "IN_PROGRESS")

            # Načteme znovu, abychom měli aktuální stav
            self.cursor.execute("SELECT * FROM memories WHERE id = ?", (task_id,))
            updated_row = self.cursor.fetchone()

            return {
                "id": updated_row[0],
                "timestamp": updated_row[1],
                "content": updated_row[2],
                "type": updated_row[3],
                "weight": updated_row[4],
                "ethos_coefficient": updated_row[5]
            }
        else:
            return None

    def update_task_status(self, task_id, status):
        """
        Aktualizuje stav (typ) úkolu v databázi.

        Args:
            task_id (int): ID úkolu k aktualizaci.
            status (str): Nový stav (např. 'IN_PROGRESS', 'TASK_COMPLETED').
        """
        self.cursor.execute("UPDATE memories SET type = ? WHERE id = ?", (status, task_id))
        self.connection.commit()

    def close(self):
        """
        Uzavře připojení k databázi.
        """
        self.connection.close()

# Tento blok slouží pro případné budoucí testování nebo ukázku použití.
if __name__ == '__main__':
    # Vytvoření instance paměti (vytvoří soubor sophia_episodic.db, pokud neexistuje)
    em = EpisodicMemory()

    # Přidání testovací vzpomínky
    mem_id = em.add_memory("Toto je testovací vzpomínka.", "module_test")
    print(f"Přidána vzpomínka s ID: {mem_id}")

    # Přístup ke vzpomínce pro zvýšení váhy
    retrieved_mem = em.access_memory(mem_id)
    print(f"Načtená vzpomínka (po 1. přístupu): {retrieved_mem}")

    retrieved_mem = em.access_memory(mem_id)
    print(f"Načtená vzpomínka (po 2. přístupu): {retrieved_mem}")

    em.close()
    print("Test dokončen a připojení uzavřeno.")
