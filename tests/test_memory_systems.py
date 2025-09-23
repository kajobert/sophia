from core.memory_systems import ShortTermMemory, LongTermMemory


def test_short_term_memory_initialization():
    """
    Tests that ShortTermMemory can be initialized.
    """
    stm = ShortTermMemory(redis_url="redis://localhost:6379/0")
    assert stm is not None
    assert hasattr(stm, "_store")  # Check for the new in-memory store


def test_short_term_memory_save_and_load():
    """
    Tests the mock save and load functionality of ShortTermMemory.
    """
    stm = ShortTermMemory(redis_url="redis://localhost:6379/0")
    session_id = "test-session"
    state_to_save = {"key": "value", "step": 1}

    assert stm.save_state(session_id, state_to_save) is True
    loaded_state = stm.load_state(session_id)
    assert loaded_state is not None
    assert loaded_state == state_to_save

    # Test loading a non-existent key
    assert stm.load_state("non-existent-session") is None


def test_long_term_memory_initialization():
    """
    Tests that LongTermMemory can be initialized.
    """
    ltm = LongTermMemory(db_url="postgresql://user:pass@localhost:5432/db")
    assert ltm is not None
    assert ltm.conn is None  # As it's mocked for now


def test_long_term_memory_search_and_add():
    """
    Tests the mock search and add functionality of LongTermMemory.
    """
    ltm = LongTermMemory(db_url="postgresql://user:pass@localhost:5432/db")
    query = "what is the meaning of life?"
    content_to_add = "The meaning of life is 42."

    search_results = ltm.search_knowledge(query, top_k=3)
    assert len(search_results) == 3
    assert search_results[0] == f"Mock result for '{query}'"

    assert ltm.add_knowledge(content_to_add) is True
