
import os
import redis
import hashlib
import json
from memory.inmemory_redis import InMemoryRedisMock

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.environ.get("LLM_CACHE_TTL", 3600))  # default 1 hodina

def get_redis_client():
    if os.environ.get("SOPHIA_TEST_MODE") == "1":
        return InMemoryRedisMock()
    return redis.Redis.from_url(REDIS_URL)

redis_client = get_redis_client()

def make_cache_key(prompt, user=None):
    # Hashujeme prompt + user email (pokud je)
    base = prompt.strip()
    if user and isinstance(user, dict):
        base += f"|{user.get('email','')}"
    return "llm:reply:" + hashlib.sha256(base.encode("utf-8")).hexdigest()

def get_cached_reply(prompt, user=None):
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
    key = make_cache_key(prompt, user)
    redis_client.setex(key, CACHE_TTL, json.dumps(reply, ensure_ascii=False))
