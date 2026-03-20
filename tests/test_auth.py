def test_register(client):
    response = client.post("/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "12345678"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_register_duplicate_username(client):
    client.post("/auth/register", json={
        "username": "sameuser",
        "email": "one@example.com",
        "password": "12345678"
    })
    response = client.post("/auth/register", json={
        "username": "sameuser",
        "email": "two@example.com",
        "password": "12345678"
    })
    assert response.status_code == 400

def test_register_duplicate_email(client):
    client.post("/auth/register", json={
        "username": "userone",
        "email": "same@example.com",
        "password": "12345678"
    })
    response = client.post("/auth/register", json={
        "username": "usertwo",
        "email": "same@example.com",
        "password": "12345678"
    })
    assert response.status_code == 400

def test_login(client):
    client.post("/auth/register", json={
        "username": "user1",
        "email": "user1@example.com",
        "password": "12345678"
    })
    response = client.post(
        "/auth/login",
        data={"username": "user1", "password": "12345678"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "12345678"
    })
    response = client.post(
        "/auth/login",
        data={"username": "user2", "password": "wrong"}
    )
    assert response.status_code == 400

def test_login_user_not_found(client):
    response = client.post(
        "/auth/login",
        data={"username": "nouser", "password": "12345678"}
    )
    assert response.status_code == 400

def test_register_invalid_email(client):
    response = client.post("/auth/register", json={
        "username": "badmailuser",
        "email": "not-an-email",
        "password": "12345678"
    })
    assert response.status_code == 422

def test_register_short_password_validation(client):
    response = client.post("/auth/register", json={
        "username": "shortpass",
        "email": "shortpass@example.com",
        "password": "123"
    })
    assert response.status_code == 200

def test_login_missing_password(client):
    response = client.post(
        "/auth/login",
        data={"username": "user1"}
    )
    assert response.status_code == 422