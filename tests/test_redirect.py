from datetime import datetime, timedelta

def test_redirect(client):
    res = client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    code = res.json()["short_code"]

    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code == 307

def test_redirect_not_found(client):
    response = client.get("/invalidcode", follow_redirects=False)
    assert response.status_code == 404

def test_redirect_expired(client, token):
    res = client.post(
        "/links/shorten",
        json={
            "original_url": "https://google.com",
            "custom_alias": "expired1",
            "expires_at": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    response = client.put(
        "/links/expired1",
        json={"expires_at": "2000-01-01T00:00:00"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400