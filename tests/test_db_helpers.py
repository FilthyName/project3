from main import User, Link, get_user_by_username, get_user_by_email, get_link_by_code, hash_password

def test_get_user_by_username(db):
    user = User(
        username="helperuser",
        email="helper@example.com",
        password_hash=hash_password("12345678")
    )
    db.add(user)
    db.commit()
    found = get_user_by_username(db, "helperuser")
    assert found is not None
    assert found.username == "helperuser"

def test_get_user_by_email(db):
    user = User(
        username="emailuser",
        email="emailuser@example.com",
        password_hash=hash_password("12345678")
    )
    db.add(user)
    db.commit()
    found = get_user_by_email(db, "emailuser@example.com")
    assert found is not None
    assert found.email == "emailuser@example.com"

def test_get_link_by_code(db):
    link = Link(
        original_url="https://google.com/",
        short_code="helper1",
        owner_id=None
    )
    db.add(link)
    db.commit()
    found = get_link_by_code(db, "helper1")
    assert found is not None
    assert found.short_code == "helper1"