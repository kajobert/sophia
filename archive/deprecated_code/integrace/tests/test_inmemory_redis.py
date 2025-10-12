from memory.inmemory_redis import InMemoryRedisMock


def test_inmemory_redis_mock_basic():
    redis = InMemoryRedisMock()
    redis.setex("foo", 10, "bar")
    assert redis.get("foo") == "bar"
    redis.expire("foo", 1)
    redis.flushdb()
    assert redis.get("foo") is None
