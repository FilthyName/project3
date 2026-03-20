import asyncio
import json
import main
from main import Link

class FakeRedis:
    def __init__(self):
        self.store = {}
        self.deleted = []
    async def get(self, key):
        return self.store.get(key)
    async def setex(self, key, ttl, value):
        self.store[key] = value
    async def delete(self, key):
        self.deleted.append(key)
        self.store.pop(key, None)

def test_get_link_info_from_cache(client):
    fake = FakeRedis()
    fake.store["link:cached1"] = json.dumps({
        "id": 1,
        "original_url": "https://google.com/",
        "short_code": "cached1",
        "created_at": "2026-03-20T00:00:00",
        "expires_at": None,
        "clicks": 5,
        "owner_id": None
    })
    main.redis_client = fake
    response = client.get("/links/cached1")
    assert response.status_code == 200
    assert response.json()["short_code"] == "cached1"
    main.redis_client = None

def test_get_link_info_sets_cache(client):
    fake = FakeRedis()
    main.redis_client = fake
    client.post("/links/shorten", json={"original_url": "https://google.com", "custom_alias": "cacheme"})
    response = client.get("/links/cacheme")
    assert response.status_code == 200
    assert "link:cacheme" in fake.store
    main.redis_client = None

def test_redirect_from_cache_updates_clicks(client, db):
    fake = FakeRedis()
    fake.store["redirect:cachedredir"] = "https://google.com/"
    main.redis_client = fake
    link = Link(
        original_url="https://google.com/",
        short_code="cachedredir",
        owner_id=None
    )
    db.add(link)
    db.commit()
    response = client.get("/cachedredir", follow_redirects=False)
    assert response.status_code == 307
    db.refresh(link)
    assert link.clicks == 1
    main.redis_client = None

def test_redirect_sets_cache(client):
    fake = FakeRedis()
    main.redis_client = fake
    client.post("/links/shorten", json={"original_url": "https://google.com", "custom_alias": "redirset"})
    response = client.get("/redirset", follow_redirects=False)
    assert response.status_code == 307
    assert "redirect:redirset" in fake.store
    main.redis_client = None

def test_invalidate_link_cache_deletes_keys():
    fake = FakeRedis()
    fake.store["link:abc"] = "x"
    fake.store["redirect:abc"] = "y"
    main.redis_client = fake
    asyncio.run(main.invalidate_link_cache("abc"))
    assert "link:abc" in fake.deleted
    assert "redirect:abc" in fake.deleted
    main.redis_client = None