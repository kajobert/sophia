from typing import Any, Dict, List, Optional
import threading


class ShortTermMemory:
    """In-memory short-term memory (working memory) used for MVP/testing.

    Simple thread-safe dict-based store mapped by session_id.
    """

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def get(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            return self._store.get(session_id, {})

    def set(self, session_id: str, data: Dict[str, Any]) -> None:
        with self._lock:
            self._store[session_id] = data

    # Compatibility methods expected by some tests and mocks
    # Older tests/mock fixtures expect ShortTermMemory to expose
    # save_state/load_state. Provide thin wrappers to preserve
    # backwards compatibility while keeping the clearer get/set API.
    def save_state(self, session_id: str, state: Dict[str, Any]) -> None:
        """Compatibility wrapper for saving state (alias for set)."""
        self.set(session_id, state)

    def load_state(self, session_id: str) -> Dict[str, Any]:
        """Compatibility wrapper for loading state (alias for get)."""
        return self.get(session_id)

    def update(self, session_id: str, partial: Dict[str, Any]) -> None:
        with self._lock:
            data = self._store.setdefault(session_id, {})
            data.update(partial)

    def clear(self, session_id: str) -> None:
        with self._lock:
            if session_id in self._store:
                del self._store[session_id]


class LongTermMemory:
    """Placeholder long-term memory. For MVP this is an in-memory store with
    a very small semantic "search" implemented via substring matching.
    """

    def __init__(self):
        # simple list of records: {"id": str, "text": str, "tags": List[str]}
        self._records: List[Dict[str, Any]] = []
        self._next_id = 1

    def add_record(self, text: str, tags: Optional[List[str]] = None) -> str:
        rid = f"rec-{self._next_id}"
        self._next_id += 1
        self._records.append({"id": rid, "text": text, "tags": tags or []})
        return rid

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        # naive substring match and ranking by length of match
        matches: List[Dict[str, Any]] = []
        q = query.lower()
        for r in self._records:
            if q in r["text"].lower() or any(q in t.lower() for t in r.get("tags", [])):
                matches.append(r)
        # return up to top_k matches
        return matches[:top_k]
