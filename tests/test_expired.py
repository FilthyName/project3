from datetime import datetime, timedelta
from main import Link

def test_get_link_info_expired(client, db):
    link = Link(
        original_url="https://google.com/",
        short_code="expiredinfo",
        expires_at=datetime.utcnow() - timedelta(minutes=1),
        owner_id=None
    )
    db.add(link)
    db.commit()
    response = client.get("/links/expiredinfo")
    assert response.status_code == 410

def test_redirect_expired_direct(client, db):
    link = Link(
        original_url="https://google.com/",
        short_code="expiredredir",
        expires_at=datetime.utcnow() - timedelta(minutes=1),
        owner_id=None
    )
    db.add(link)
    db.commit()
    response = client.get("/expiredredir", follow_redirects=False)
    assert response.status_code == 410