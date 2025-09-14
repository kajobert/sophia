# /memory/advanced_memory.py
"""
Modul pro správu pokročilé paměti Sophie.
Tento modul je wrapper okolo knihovny GibsonAI/memori a poskytuje
jednotné rozhraní pro epizodickou a sémantickou paměť.
"""

import yaml
from memori import Memori
from datetime import datetime
from sqlalchemy import text
import asyncio

class AdvancedMemory:
    """
    Třída pro správu paměti pomocí knihovny Memori.
    """
    def __init__(self, config_path='config.yaml', user_id="sophia"):
        """
        Inicializuje knihovnu Memori s připojením k databázi
        a nastaví potřebné proměnné.
        """
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        db_config = config['database']
        db_conn_str = f"postgresql://{db_config['db_user']}:{db_config['db_password']}@{db_config['db_host']}:{db_config['db_port']}/{db_config['db_name']}"

        api_key = config.get('openai_api_key', 'sk-dummy')

        self.user_id = user_id
        self.memori = Memori(
            database_connect=db_conn_str,
            openai_api_key=api_key,
            conscious_ingest=True,
            auto_ingest=True,
            namespace=self.user_id
        )
        self.memori.enable()
        print("AdvancedMemory initialized.")

    async def add_memory(self, content, mem_type, metadata=None):
        if metadata is None:
            metadata = {}
        metadata['memory_type'] = mem_type

        chat_id = self.memori.record_conversation(
            user_input=content,
            ai_output=f"Noted: {mem_type}",
            model="internal_event",
            metadata=metadata
        )
        return chat_id

    async def access_memory(self, memory_id):
        history = self.memori.get_conversation_history(limit=1000)
        for memory in history:
            if memory.get('chat_id') == memory_id:
                return memory
        return None

    async def read_last_n_memories(self, n=10):
        return self.memori.get_conversation_history(limit=n)

    async def add_task(self, description):
        return await self.add_memory(description, "TASK", metadata={'status': 'new'})

    async def get_next_task(self):
        tasks = self.memori.db_manager.search_memories(
            query="",
            namespace=self.user_id,
            category_filter=['TASK'],
            limit=100
        )

        next_task = None
        for task in sorted(tasks, key=lambda x: x.get('timestamp')):
            metadata = task.get('metadata', {})
            if metadata.get('status') == 'new':
                next_task = task
                break

        if next_task:
            task_id = next_task.get('chat_id')
            await self.update_task_status(task_id, "IN_PROGRESS")
            return await self.access_memory(task_id)

        return None

    async def update_task_status(self, task_id, status):
        task_memory = await self.access_memory(task_id)
        if not task_memory:
            return

        metadata = task_memory.get('metadata', {})
        metadata['status'] = status

        query = text("""
            UPDATE chat_history
            SET metadata_json = jsonb_set(metadata_json::jsonb, '{status}', :status::jsonb)
            WHERE chat_id = :chat_id
        """)

        self.memori.db_manager.execute_with_translation(
            query,
            parameters={'status': f'"{status}"', 'chat_id': task_id}
        )

    def close(self):
        print("AdvancedMemory closed.")
        pass
