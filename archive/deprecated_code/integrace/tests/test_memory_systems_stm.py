import pytest
from core.memory_systems import ShortTermMemory


def test_save_and_load_state_basic():
    stm = ShortTermMemory()
    sid = "s1"
    data = {"a": 1, "b": 2}

    # save_state should persist the dict
    stm.save_state(sid, data)
    loaded = stm.load_state(sid)
    assert loaded == data


def test_update_preserves_existing_keys():
    stm = ShortTermMemory()
    sid = "s2"
    stm.save_state(sid, {"x": 1, "history": []})

    # update should merge new keys
    stm.update(sid, {"y": 2, "history": ["step"]})
    loaded = stm.load_state(sid)
    assert loaded["x"] == 1
    assert loaded["y"] == 2
    assert loaded["history"] == ["step"]


def test_clear_removes_state():
    stm = ShortTermMemory()
    sid = "s3"
    stm.save_state(sid, {"foo": "bar"})
    assert stm.load_state(sid) is not None

    stm.clear(sid)
    assert stm.load_state(sid) == {}
