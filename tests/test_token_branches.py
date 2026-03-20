from jose import jwt
from main import SECRET_KEY, ALGORITHM

def test_stats_with_token_without_sub(client):
    token = jwt.encode({"foo": "bar"}, SECRET_KEY, algorithm=ALGORITHM)
    response = client.get(
        "/links/test123/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401

def test_delete_with_token_without_sub(client):
    token = jwt.encode({"foo": "bar"}, SECRET_KEY, algorithm=ALGORITHM)
    response = client.delete(
        "/links/test123",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401

def test_update_with_token_without_sub(client):
    token = jwt.encode({"foo": "bar"}, SECRET_KEY, algorithm=ALGORITHM)
    response = client.put(
        "/links/test123",
        json={"original_url": "https://google.com"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401