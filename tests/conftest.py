import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def user(client):
    response = client.post("/auth/register", json={
        "username": "testMalyshev",
        "email": "test@example.com",
        "password": "12345678"
    })
    return response.json()

@pytest.fixture
def token(client):
    client.post("/auth/register", json={
        "username": "testMalyshev",
        "email": "test@example.com",
        "password": "12345678"
    })
    response = client.post(
        "/auth/login",
        data={"username": "testMalyshev", "password": "12345678"}
    )
    return response.json().get("access_token")