import pytest
import os
import threading
import time

def test_parallel_snapshot_write(snapshot, tmp_path):
    # Simuluje paralelní zápis do snapshotu
    results = []
    def write_snapshot(val):
        # Každé vlákno zapisuje jinou hodnotu
        results.append(snapshot(f"parallel={val}"))
    threads = [threading.Thread(target=write_snapshot, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    # Ověř, že snapshot helper nezpůsobil race condition (např. žádný výstup není None)
    assert all(r is not None for r in results)
