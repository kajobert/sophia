import time


class InMemoryRedisMock:
    def __init__(self):
        self._store = {}
        self._expire = {}

    def setex(self, key, ttl, value):
        self._store[key] = value
        self._expire[key] = time.time() + ttl

    def get(self, key):
        exp = self._expire.get(key)
        if exp is not None and exp < time.time():
            self._store.pop(key, None)
            self._expire.pop(key, None)
            return None
        return self._store.get(key)

    def expire(self, key, ttl):
        if key in self._store:
            self._expire[key] = time.time() + ttl

    def flushdb(self):
        self._store.clear()
        self._expire.clear()
