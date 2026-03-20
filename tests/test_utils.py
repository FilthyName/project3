from datetime import timedelta
from jose import jwt

from main import (
    hash_password,
    verify_password,
    generate_short_code,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
)

def test_password_hash():
    password = "12345678"
    hashed = hash_password(password)
    assert verify_password(password, hashed)

def test_verify_password_false():
    password = "12345678"
    hashed = hash_password(password)
    assert verify_password("wrongpassword", hashed) is False

def test_generate_code():
    code = generate_short_code()
    assert isinstance(code, str)
    assert len(code) > 0

def test_generate_code_custom_length():
    code = generate_short_code(8)
    assert len(code) == 8

def test_create_access_token():
    token = create_access_token({"sub": "testuser"})
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
    assert "exp" in payload

def test_create_access_token_with_custom_expire():
    token = create_access_token({"sub": "testuser"}, expires_delta=timedelta(minutes=5))
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "testuser"
    assert "exp" in payload