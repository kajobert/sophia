"""
Tests for the ChromaDBMemory plugin.
"""

import pytest
from typing import Generator
from plugins.memory_chroma import ChromaDBMemory
import chromadb
from chromadb.config import Settings

# Define a database path for testing that is separate from the application's data.
TEST_DB_PATH = "test_chroma_db"


@pytest.fixture
def chroma_memory_plugin() -> Generator[ChromaDBMemory, None, None]:
    """
    Pytest fixture to set up and tear down a test ChromaDB instance.
    This ensures that each test runs in a clean, isolated environment.
    """
    memory_plugin = ChromaDBMemory()
    # Use an in-memory, ephemeral instance of ChromaDB for testing
    memory_plugin.client = chromadb.Client(
        settings=Settings(allow_reset=True, anonymized_telemetry=False)
    )
    memory_plugin.collection = memory_plugin.client.get_or_create_collection(
        name="sophia_long_term_memory"
    )

    yield memory_plugin

    # Teardown: Reset the database to ensure a clean state for the next test.
    memory_plugin.client.reset()


def test_chroma_memory_add_and_search_successfully(chroma_memory_plugin: ChromaDBMemory) -> None:
    """
    Tests the core functionality: adding a memory and then retrieving it
    via a semantic search.
    """
    session_id = "test_session_1"
    memory_text = "The quick brown fox jumps over the lazy dog."
    query_text = "What does the fox do?"

    # 1. Add a memory
    chroma_memory_plugin.add_memory(session_id, memory_text)

    # 2. Search for a semantically similar concept
    results = chroma_memory_plugin.search_memories(query_text, n_results=1)

    # 3. Verify the result
    assert len(results) == 1
    assert results[0] == memory_text


def test_search_for_nonexistent_memory_returns_empty(chroma_memory_plugin: ChromaDBMemory) -> None:
    """
    Tests that searching for a concept that has not been stored returns
    an empty list, not an error.
    """
    # Search for a concept that is not in the database
    results = chroma_memory_plugin.search_memories("unrelated concept", n_results=1)

    # Verify that the result is an empty list
    assert len(results) == 0
    assert results == []


def test_add_empty_memory_is_ignored(chroma_memory_plugin: ChromaDBMemory) -> None:
    """
    Tests that attempting to add an empty string as a memory is handled
    gracefully and does not add a record to the database.
    """
    session_id = "test_session_empty"
    chroma_memory_plugin.add_memory(session_id, "")

    # To verify, we search for something; if the DB is empty, we get no results.
    results = chroma_memory_plugin.search_memories("any query", n_results=1)
    assert len(results) == 0


def test_search_with_empty_query_returns_empty(chroma_memory_plugin: ChromaDBMemory) -> None:
    """
    Tests that searching with an empty query string is handled gracefully
    and returns an empty list.
    """
    # Add a memory first so the database is not empty
    chroma_memory_plugin.add_memory("test_session_3", "some memory")

    # Search with an empty query
    results = chroma_memory_plugin.search_memories("", n_results=1)
    assert len(results) == 0
    assert results == []


def test_get_history_returns_empty_list(chroma_memory_plugin: ChromaDBMemory) -> None:
    """
    Tests that the get_history method returns an empty list, fulfilling the
    memory plugin contract.
    """
    session_id = "test_session_history"
    history = chroma_memory_plugin.get_history(session_id)
    assert history == []
