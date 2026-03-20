def test_create_link_empty_body(client):
    response = client.post("/links/shorten", json={})
    assert response.status_code == 422

def test_create_link_missing_url(client):
    response = client.post("/links/shorten", json={
        "custom_alias": "test"
    })
    assert response.status_code == 422

def test_update_link_empty_payload(client, token):
    res = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = res.json()["short_code"]
    response = client.put(
        f"/links/{code}",
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in (200, 422)

def test_delete_link_twice(client, token):
    res = client.post(
        "/links/shorten",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    code = res.json()["short_code"]
    client.delete(
        f"/links/{code}",
        headers={"Authorization": f"Bearer {token}"}
    )
    response = client.delete(
        f"/links/{code}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code in (404, 400)

def test_redirect_after_delete_owned_link(client, token):
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
    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code in (404, 410)

def test_get_link_info_after_delete_owned_link(client, token):
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