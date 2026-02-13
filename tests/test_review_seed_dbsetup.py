import importlib

from sqlalchemy import select

from db import SessionLocal
from models import Review, User
from models.user import UserRole
from seed_admin import create_admin_if_not_exist


def login_as(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["role"] = user.role.value


def test_create_review_restaurant_not_found(client):

    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "user"

    resp = client.get("/restaurants/99999/reviews")
    assert resp.status_code == 400
    assert b"Restaurant not found" in resp.data


def test_create_review_success(client, sample_data):
    restaurant = sample_data["restaurant"]
    client_user = sample_data["client"]

    login_as(client, client_user)

    resp = client.post(
        f"/restaurants/{restaurant.id}/reviews",
        data={"rating": "5", "comment": "Very nice!"},
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    assert f"/restaurants/{restaurant.id}/details" in resp.headers["Location"]

    db = SessionLocal()
    reviews = db.execute(
        select(Review).where(Review.restaurant_id == restaurant.id)
    ).scalars().all()
    db.close()

    assert len(reviews) == 1
    assert reviews[0].rating == 5
    assert reviews[0].comment == "Very nice!"


def test_create_admin_if_not_exist_creates_admin(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "super-secret")

    create_admin_if_not_exist()

    db = SessionLocal()
    admin = db.execute(
        select(User).where(User.role == UserRole.admin)
    ).scalars().first()
    db.close()

    assert admin is not None
    assert admin.email == "admin@example.com"


def test_create_admin_if_not_exist_does_not_duplicate(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin_user")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "super-secret")

    create_admin_if_not_exist()
    create_admin_if_not_exist()

    db = SessionLocal()
    admins = db.execute(
        select(User).where(User.role == UserRole.admin)
    ).scalars().all()
    db.close()

    assert len(admins) == 1


def test_db_setup_import_runs():
    import db_setup

    importlib.reload(db_setup)
