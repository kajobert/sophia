import pytest
from services.llm_cache import make_cache_key, set_cached_reply, get_cached_reply, redis_client
import time

@pytest.fixture(autouse=True)
def clear_redis():
    redis_client.flushdb()
    yield
    redis_client.flushdb()

def test_cache_set_and_get():
    prompt = "Ahoj, kdo jsi?"
    user = {"email": "test@example.com"}
    reply = "Sophia říká: Jsem Sophia."
    set_cached_reply(prompt, user, reply)
    cached = get_cached_reply(prompt, user)
    assert cached == reply

def test_cache_key_differs_by_user():
    prompt = "Ahoj, kdo jsi?"
    user1 = {"email": "a@a.cz"}
    user2 = {"email": "b@b.cz"}
    reply1 = "Odpověď 1"
    reply2 = "Odpověď 2"
    set_cached_reply(prompt, user1, reply1)
    set_cached_reply(prompt, user2, reply2)
    assert get_cached_reply(prompt, user1) == reply1
    assert get_cached_reply(prompt, user2) == reply2

def test_cache_ttl_expires():
    prompt = "Ahoj, test TTL"
    user = None
    reply = "Odpověď TTL"
    set_cached_reply(prompt, user, reply)
    key = make_cache_key(prompt, user)
    redis_client.expire(key, 1)  # nastavíme TTL na 1 sekundu
    assert get_cached_reply(prompt, user) == reply
    time.sleep(1.2)
    assert get_cached_reply(prompt, user) is None
