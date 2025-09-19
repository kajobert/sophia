import os
import redis
import hashlib
import json
from memory.inmemory_redis import InMemoryRedisMock

# Force IPv4 connection by using 127.0.0.1 instead of localhost
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
CACHE_TTL = int(os.environ.get("LLM_CACHE_TTL", 3600))  # default 1 hodina


_mock_redis_instance = None


def get_redis_client():
    """
    Factory function for the Redis client.
    In test mode, it returns a singleton instance of the mock client.
    """
    global _mock_redis_instance
    if os.environ.get("SOPHIA_TEST_MODE") == "1":
        if _mock_redis_instance is None:
            _mock_redis_instance = InMemoryRedisMock()
        return _mock_redis_instance
    return redis.Redis.from_url(REDIS_URL)


def make_cache_key(prompt, user=None):
    # Hashujeme prompt + user email (pokud je)
    base = prompt.strip()
    if user and isinstance(user, dict):
        base += f"|{user.get('email','')}"
    return "llm:reply:" + hashlib.sha256(base.encode("utf-8")).hexdigest()


def get_cached_reply(prompt, user=None):
    redis_client = get_redis_client()
    key = make_cache_key(prompt, user)
    val = redis_client.get(key)
    if val:
        try:
            if isinstance(val, bytes):
                val = val.decode("utf-8")
            return json.loads(val)
        except Exception:
            return val
    return None


def set_cached_reply(prompt, user, reply):
    redis_client = get_redis_client()
    key = make_cache_key(prompt, user)
    redis_client.setex(key, CACHE_TTL, json.dumps(reply, ensure_ascii=False))
