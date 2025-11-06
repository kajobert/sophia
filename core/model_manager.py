"""Minimal Model Manager for MVP.

Keeps a tiny local benchmark record and can enqueue a benchmark task to the
persistent queue when a local model exists but hasn't been benchmarked yet.
"""
import json
from pathlib import Path
from typing import Optional

from core.simple_persistent_queue import SimplePersistentQueue


class ModelManager:
    def __init__(self, db_path: str | Path = ".data/tasks.sqlite", records_path: str | Path = ".data/model_benchmarks.json"):
        self.queue = SimplePersistentQueue(db_path=db_path)
        self.records_path = Path(records_path)
        self._records = None

    def _load(self):
        if self._records is not None:
            return
        self._records = {}
        if self.records_path.exists():
            try:
                with self.records_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._records = data
            except Exception:
                self._records = {}

    def is_local_benchmarked(self) -> bool:
        self._load()
        lm = self._records.get("local_model")
        return bool(lm and isinstance(lm, dict) and lm.get("score") is not None)

    def get_local_score(self) -> Optional[float]:
        self._load()
        rec = self._records.get("local_model")
        if not rec or not isinstance(rec, dict):
            return None
        try:
            return float(rec.get("score")) if rec.get("score") is not None else None
        except Exception:
            return None

    def mark_local_benchmarked(self, score: float) -> None:
        self._load()
        if not isinstance(self._records, dict):
            self._records = {}
        self._records.setdefault("local_model", {})
        self._records["local_model"]["score"] = float(score)
        with self.records_path.open("w", encoding="utf-8") as f:
            json.dump(self._records, f, indent=2)

    def ensure_benchmark_task(self) -> int | None:
        """Enqueue a benchmark task if no benchmark record exists. Returns task id or None if not enqueued."""
        if self.is_local_benchmarked():
            return None

        payload = {
            "instruction": "__benchmark_local_model__",
            "type": "benchmark_local_model",
        }
        tid = self.queue.enqueue(payload, priority=10)
        return tid
