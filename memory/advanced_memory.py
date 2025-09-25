# /memory/advanced_memory.py
"""
Modul pro správu pokročilé paměti Sophie.
Tento modul je wrapper okolo knihovny GibsonAI/memori a poskytuje
jednotné rozhraní pro epizodickou a sémantickou paměť.
"""

import yaml
from memori import Memori
from sqlalchemy import text
import asyncio
import uuid
import time


class AdvancedMemory:
    """
    Třída pro správu paměti pomocí knihovny Memori.
    """

    def __init__(self, config_path="config.yaml", user_id="sophia"):
        """
        Inicializuje knihovnu Memori s připojením k databázi
        a nastaví potřebné proměnné.
        """
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        db_config = config["database"]
        db_conn_str = f"postgresql://{db_config['db_user']}:{db_config['db_password']}@{db_config['db_host']}:{db_config['db_port']}/{db_config['db_name']}"

        api_key = config.get("openai_api_key", "sk-dummy")

        self.user_id = user_id
        self.memori = Memori(
            database_connect=db_conn_str,
            openai_api_key=api_key,
            conscious_ingest=True,
            auto_ingest=True,
            namespace=self.user_id,
        )
        self.memori.enable()
        print("AdvancedMemory initialized.")

    async def add_memory(self, content, mem_type, metadata=None):
        if metadata is None:
            metadata = {}
        metadata["memory_type"] = mem_type

        chat_id = self.memori.record_conversation(
            user_input=content,
            ai_output=f"Noted: {mem_type}",
            model="internal_event",
            metadata=metadata,
        )
        return chat_id

    async def access_memory(self, memory_id):
        history = self.memori.get_conversation_history(limit=1000)
        for memory in history:
            if memory.get("chat_id") == memory_id:
                return memory
        return None

    async def read_last_n_memories(self, n=10, mem_type: str = None):
        """
        Reads the last N memories. If mem_type is provided, it filters by memory type.
        """
        if mem_type is None:
            return self.memori.get_conversation_history(limit=n)

        session = self.memori.db_manager.SessionLocal()
        try:
            # This query is designed to be compatible with PostgreSQL's JSONB format
            # and return data in a structure similar to memori.get_conversation_history
            query = text(
                """
                SELECT
                    chat_id,
                    user_input,
                    ai_output,
                    timestamp,
                    metadata_json as metadata,
                    model
                FROM chat_history
                WHERE namespace = :namespace
                  AND metadata_json->>'memory_type' = :mem_type
                ORDER BY timestamp DESC
                LIMIT :n
            """
            )
            result = session.execute(
                query, {"namespace": self.user_id, "mem_type": mem_type, "n": n}
            )

            # Convert rows to a list of dictionaries
            memories = [
                {
                    "chat_id": row.chat_id,
                    "user_input": row.user_input,
                    "ai_output": row.ai_output,
                    "timestamp": row.timestamp.isoformat(),
                    "metadata": row.metadata,
                    "model": row.model,
                }
                for row in result
            ]
            return memories
        finally:
            session.close()

    async def add_task(self, description):
        """
        Přidá nový úkol do paměti a ověří jeho úspěšné zapsání.
        """
        task_uuid = str(uuid.uuid4())
        metadata = {"status": "new", "task_uuid": task_uuid}

        chat_id = await self.add_memory(description, "TASK", metadata)

        start_time = time.time()
        timeout = 5  # seconds

        while time.time() - start_time < timeout:
            session = self.memori.db_manager.SessionLocal()
            try:
                query = text(
                    "SELECT chat_id FROM chat_history WHERE metadata_json->>'task_uuid' = :task_uuid"
                )
                result = session.execute(query, {"task_uuid": task_uuid}).fetchone()

                if result and result[0] == chat_id:
                    print(f"Task {chat_id} with UUID {task_uuid} verified in database.")
                    return chat_id
            finally:
                session.close()

            await asyncio.sleep(0.2)

        raise TimeoutError(
            f"Failed to verify task creation in memory for chat_id {chat_id}"
        )

    async def get_next_task(self):
        """
        Najde nejstarší nový úkol, označí ho jako probíhající a vrátí ho.
        Tato metoda nyní přímo prohledává 'chat_history' aby se předešlo race condition.
        """
        next_task_id = None
        session = self.memori.db_manager.SessionLocal()
        try:
            # PostgreSQL specifický dotaz pro JSONB
            query = text(
                """
                SELECT chat_id FROM chat_history
                WHERE metadata_json->>'memory_type' = 'TASK'
                  AND metadata_json->>'status' = 'new'
                  AND namespace = :namespace
                ORDER BY timestamp ASC
                LIMIT 1
            """
            )
            result = session.execute(query, {"namespace": self.user_id}).fetchone()
            if result:
                next_task_id = result[0]
        finally:
            session.close()

        if next_task_id:
            await self.update_task_status(next_task_id, "IN_PROGRESS")
            return await self.access_memory(next_task_id)

        return None

    async def update_task_status(self, task_id, status):
        task_memory = await self.access_memory(task_id)
        if not task_memory:
            return

        metadata = task_memory.get("metadata", {})
        metadata["status"] = status

        query = text(
            """
            UPDATE chat_history
            SET metadata_json = jsonb_set(metadata_json::jsonb, '{status}', :status::jsonb)
            WHERE chat_id = :chat_id
        """
        )

        session = self.memori.db_manager.SessionLocal()
        try:
            session.execute(query, {"status": f'"{status}"', "chat_id": task_id})
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def close(self):
        print("AdvancedMemory closed.")
        pass
