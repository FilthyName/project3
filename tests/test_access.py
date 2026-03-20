def test_get_stats_with_invalid_token(client):
    response = client.get(
        "/links/test123/stats",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401

def test_delete_with_invalid_token(client):
    response = client.delete(
        "/links/test123",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401

def test_update_with_invalid_token(client):
    response = client.put(
        "/links/test123",
        json={"original_url": "https://google.com"},
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401