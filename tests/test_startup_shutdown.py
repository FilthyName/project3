import asyncio
import main

class FakeRedis:
    def __init__(self):
        self.closed = False
    async def ping(self):
        return True
    async def close(self):
        self.closed = True

def test_startup_success(monkeypatch):
    fake = FakeRedis()
    class FakeRedisFactory:
        @staticmethod
        def from_url(*args, **kwargs):
            return fake
    monkeypatch.setattr(main, "Redis", FakeRedisFactory)
    asyncio.run(main.startup())
    assert main.redis_client is fake

def test_shutdown_success():
    fake = FakeRedis()
    main.redis_client = fake
    asyncio.run(main.shutdown())
    assert fake.closed is True

def test_startup_redis_failure(monkeypatch):
    class BrokenRedisFactory:
        @staticmethod
        def from_url(*args, **kwargs):
            raise Exception("redis down")
    monkeypatch.setattr(main, "Redis", BrokenRedisFactory)
    asyncio.run(main.startup())
    assert main.redis_client is None