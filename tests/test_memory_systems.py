
from core.memory_systems import ShortTermMemory, LongTermMemory


def test_short_term_memory_set_get_update_clear():
    stm = ShortTermMemory()
    sid = "sess-1"
    stm.set(sid, {"a": 1})
    assert stm.get(sid)["a"] == 1

    stm.update(sid, {"b": 2})
    assert stm.get(sid)["b"] == 2

    stm.clear(sid)
    assert stm.get(sid) == {}


def test_long_term_memory_add_and_search():
    ltm = LongTermMemory()
    ltm.add_record("This is about Python testing", tags=["testing", "python"])
    ltm.add_record("Advanced memory systems and embeddings", tags=["memory"])

    res = ltm.search("python")
    assert any(
        "python" in r["text"].lower() or "python" in " ".join(r.get("tags", []))
        for r in res
    )
