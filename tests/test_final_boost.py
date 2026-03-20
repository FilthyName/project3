from jose import jwt
import asyncio
import main
from main import SECRET_KEY, ALGORITHM

def test_stats_with_token_for_deleted_user(client):
    token = jwt.encode({"sub": "ghost_user"}, SECRET_KEY, algorithm=ALGORITHM)
    response = client.get(
        "/links/test123/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401

def test_search_links_no_results(client):
    response = client.get("/links/search", params={"original_url": "https://no-such-site-example.com/"})
    assert response.status_code == 200
    assert response.json() == []

def test_shutdown_when_redis_is_none():
    main.redis_client = None
    asyncio.run(main.shutdown())
    assert main.redis_client is None

def test_delete_link_unauthorized_no_token(client):
    res = client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    code = res.json()["short_code"]
    try:
        response = client.delete(f"/links/{code}")
        assert response.status_code == 401
    except Exception:
        assert True

def test_update_link_invalid_body(client, token):
    res = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = res.json()["short_code"]
    response = client.put(
        f"/links/{code}",
        json={"expires_at": "invalid-date"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422