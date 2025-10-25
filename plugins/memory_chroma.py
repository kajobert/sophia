"""
This plugin provides a long-term memory storage and retrieval mechanism for Sophia,
leveraging the ChromaDB vector database for semantic search capabilities.
"""

import logging
from typing import Dict, Any, List
import chromadb
from chromadb.types import Collection
from chromadb.config import Settings
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class ChromaDBMemory(BasePlugin):
    """
    A memory plugin that stores and retrieves long-term semantic memories
    using a persistent ChromaDB vector database.

    This plugin is responsible for the technical implementation of storing textual data
    and searching it based on semantic similarity. It is not responsible for deciding
    *what* to remember or *when* to search; those cognitive functions are handled
    by other plugins that will call this one's public methods.
    """

    @property
    def name(self) -> str:
        """Returns the unique name of the plugin."""
        return "memory_chroma"

    @property
    def plugin_type(self) -> PluginType:
        """Returns the type of the plugin."""
        return PluginType.MEMORY

    @property
    def version(self) -> str:
        """Returns the version of the plugin."""
        return "1.0.0"

    def setup(self, config: Dict[str, Any]) -> None:
        """
        Initializes the ChromaDB client and gets or creates the memory collection.

        This method is called by the PluginManager during the application's setup
        phase. It uses the configuration provided in `config/settings.yaml` to
        establish a connection to the persistent database.

        Args:
            config: A dictionary containing the plugin's configuration,
                    including the 'db_path'.
        """
        db_path: str = config.get("db_path", "data/chroma_db")
        allow_reset: bool = config.get("allow_reset", False)
        try:
            self.client: chromadb.Client = chromadb.PersistentClient(
                path=db_path,
                settings=Settings(
                    allow_reset=allow_reset,
                    anonymized_telemetry=False
                )
            )
            self.collection: Collection = self.client.get_or_create_collection(
                name="sophia_long_term_memory"
            )
            logger.info(f"ChromaDB long-term memory initialized at '{db_path}'.")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB at '{db_path}': {e}", exc_info=True)
            # Depending on the desired behavior, we might want to raise the exception
            # to halt the application's startup if the memory system is critical.
            raise

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This plugin's primary role is passive. It waits for other plugins
        to call its methods to store or retrieve memories.
        """
        return context

    def add_memory(self, session_id: str, text: str) -> None:
        """
        Creates an embedding for a piece of text and stores it as a long-term memory.

        To prevent duplicate entries, a unique ID is generated based on the session ID
        and a hash of the text content.

        Args:
            session_id: The ID of the conversation session this memory belongs to.
            text: The text content to be stored as a memory.
        """
        if not text:
            logger.warning("Attempted to add an empty memory.")
            return

        try:
            doc_id = f"{session_id}_{hash(text)}"
            self.collection.add(
                documents=[text],
                metadatas=[{"session_id": session_id}],
                ids=[doc_id]
            )
            logger.info(f"Added a new long-term memory: '{text[:50]}...'")
        except Exception as e:
            logger.error(f"Failed to add memory to ChromaDB: {e}", exc_info=True)

    def search_memories(self, query_text: str, n_results: int = 3) -> List[str]:
        """
        Searches for the most relevant long-term memories based on a query text.

        Args:
            query_text: The text to search for.
            n_results: The maximum number of results to return.

        Returns:
            A list of the most relevant memory texts, or an empty list if
            no relevant memories are found or an error occurs.
        """
        if not query_text:
            logger.warning("Attempted to search with an empty query.")
            return []

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )

            memories: List[str] = results['documents'][0] if results and results.get('documents') else []
            logger.info(f"Found {len(memories)} relevant memories for query: '{query_text[:50]}...'")
            return memories
        except Exception as e:
            logger.error(f"Failed to search memories in ChromaDB: {e}", exc_info=True)
            return []
