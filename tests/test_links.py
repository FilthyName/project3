from datetime import datetime, timedelta

def test_create_link(client):
    response = client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    assert response.status_code == 200
    assert "short_code" in response.json()

def test_search_links(client):
    client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    response = client.get("/links/search", params={"original_url": "https://google.com/"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

def test_update_link_unauthorized(client):
    res = client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    code = res.json()["short_code"]
    response = client.put(
        f"/links/{code}",
        json={"original_url": "https://youtube.com"}
    )
    assert response.status_code == 401

def test_get_link_stats_unauthorized(client):
    res = client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    code = res.json()["short_code"]
    response = client.get(f"/links/{code}/stats")
    assert response.status_code == 401

def test_create_link_auth(client, token):
    response = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["owner_id"] is not None

def test_create_link_with_custom_alias(client):
    response = client.post("/links/shorten", json={
        "original_url": "https://google.com",
        "custom_alias": "myalias"
    })
    assert response.status_code == 200
    assert response.json()["short_code"] == "myalias"

def test_create_link_with_duplicate_custom_alias(client):
    client.post("/links/shorten", json={
        "original_url": "https://google.com",
        "custom_alias": "samealias"
    })
    response = client.post("/links/shorten", json={
        "original_url": "https://youtube.com",
        "custom_alias": "samealias"
    })
    assert response.status_code == 400

def test_create_link_with_past_expiration(client):
    response = client.post("/links/shorten", json={
        "original_url": "https://google.com",
        "expires_at": "2000-01-01T00:00:00"
    })
    assert response.status_code == 400

def test_get_link_info(client):
    res = client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    code = res.json()["short_code"]
    response = client.get(f"/links/{code}")
    assert response.status_code == 200
    assert response.json()["short_code"] == code

def test_get_link_info_not_found(client):
    response = client.get("/links/notfound123")
    assert response.status_code == 404

def test_update_link(client, token):
    res = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = res.json()["short_code"]
    response = client.put(
        f"/links/{code}",
        json={"original_url": "https://youtube.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["original_url"] == "https://youtube.com/"

def test_update_link_with_past_expiration(client, token):
    res = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = res.json()["short_code"]
    response = client.put(
        f"/links/{code}",
        json={"expires_at": "2000-01-01T00:00:00"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400

def test_update_link_forbidden(client, token):
    res = client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    code = res.json()["short_code"]
    response = client.put(
        f"/links/{code}",
        json={"original_url": "https://youtube.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_get_link_stats(client, token):
    res = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = res.json()["short_code"]
    client.get(f"/{code}", follow_redirects=False)
    client.get(f"/{code}", follow_redirects=False)
    response = client.get(
        f"/links/{code}/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["clicks"] >= 2

def test_get_link_stats_forbidden(client, token):
    res = client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    code = res.json()["short_code"]
    response = client.get(
        f"/links/{code}/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_delete_link(client, token):
    res = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = res.json()["short_code"]
    response = client.delete(
        f"/links/{code}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200

def test_delete_link_not_found(client, token):
    response = client.delete(
        "/links/notfound123",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

def test_delete_link_forbidden(client, token):
    res = client.post("/links/shorten", json={
        "original_url": "https://google.com"
    })
    code = res.json()["short_code"]
    response = client.delete(
        f"/links/{code}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_update_link_not_found(client, token):
    response = client.put(
        "/links/notfound123",
        json={"original_url": "https://youtube.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

def test_get_link_stats_not_found(client, token):
    response = client.get(
        "/links/notfound123/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

def test_delete_then_get_info_returns_404(client, token):
    res = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = res.json()["short_code"]
    delete_response = client.delete(
        f"/links/{code}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_response.status_code == 200
    response = client.get(f"/links/{code}")
    assert response.status_code == 404

def test_create_link_invalid_url(client):
    response = client.post("/links/shorten", json={
        "original_url": "not-a-url"
    })
    assert response.status_code == 422