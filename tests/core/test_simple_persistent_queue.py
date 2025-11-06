import os
import tempfile
from core.simple_persistent_queue import SimplePersistentQueue


def test_enqueue_and_dequeue_and_mark_done(tmp_path):
    dbp = tmp_path / "q.sqlite"
    q = SimplePersistentQueue(db_path=str(dbp))

    tid = q.enqueue({"instruction": "do something"}, priority=10)
    assert isinstance(tid, int)

    item = q.dequeue_and_lock()
    assert item is not None
    assert item["id"] == tid
    payload = item["payload"]
    assert payload.get("instruction") == "do something"

    q.mark_done(tid)
    # No pending tasks now
    assert q.pending_count() == 0
