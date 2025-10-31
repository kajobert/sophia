import os
from pathlib import Path
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, insert, select
from typing import List, Dict


class SQLiteMemory(BasePlugin):
    """A memory plugin that stores conversation history in a SQLite database."""

    @property
    def name(self) -> str:
        return "memory_sqlite"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.MEMORY

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Initializes the database connection and creates the table if it doesn't exist."""
        db_path_str = config.get("db_path", "data/memory/sophia_memory.db")

        # Ensure the directory for the database exists
        db_path = Path(db_path_str)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{db_path_str}")
        self.metadata = MetaData()
        self.history_table = Table(
            "conversation_history",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("session_id", String),
            Column("role", String),
            Column("content", String),
        )
        self.metadata.create_all(self.engine)

    async def execute(self, context: SharedContext) -> SharedContext:
        """Saves the current user input and LLM response to the database."""
        user_input = context.user_input
        llm_response = context.payload.get("llm_response")

        if not user_input or not llm_response:
            return context

        with self.engine.connect() as conn:
            conn.execute(
                insert(self.history_table).values(
                    session_id=context.session_id, role="user", content=user_input
                )
            )
            conn.execute(
                insert(self.history_table).values(
                    session_id=context.session_id, role="assistant", content=llm_response
                )
            )
            conn.commit()
            context.logger.info(
                "Saved interaction to short-term memory.",
                extra={"plugin_name": self.name},
            )

        return context

    def get_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retrieves the most recent history for a session."""
        with self.engine.connect() as conn:
            stmt = (
                select(self.history_table.c.role, self.history_table.c.content)
                .where(self.history_table.c.session_id == session_id)
                .order_by(self.history_table.c.id.desc())
                .limit(limit)
            )
            results = conn.execute(stmt).fetchall()
            return [{"role": row[0], "content": row[1]} for row in reversed(results)]
