import time

import pytest
from services.llm_cache import (
    get_cached_reply,
    get_redis_client,
    make_cache_key,
    set_cached_reply,
)


@pytest.fixture(autouse=True)
def clear_redis():
    """Ensures the mock redis is cleared before and after each test."""
    redis_client = get_redis_client()
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


def test_cache_ttl_expires(monkeypatch):
    """Test that a cached item correctly expires after its TTL."""
    prompt = "Ahoj, test TTL"
    user = None
    reply = "Odpověď TTL"

    start_time = time.time()

    # 1. Set the initial time
    monkeypatch.setattr(time, 'time', lambda: start_time)
    set_cached_reply(prompt, user, reply)
    key = make_cache_key(prompt, user)

    # 2. Set the TTL and verify the item is present
    redis_client = get_redis_client()
    redis_client.expire(key, 1)  # Set TTL to 1 second
    assert get_cached_reply(prompt, user) == reply

    # 3. Simulate time passing beyond the TTL
    monkeypatch.setattr(time, 'time', lambda: start_time + 1.2)

    # 4. Verify the item has expired
    assert get_cached_reply(prompt, user) is None
