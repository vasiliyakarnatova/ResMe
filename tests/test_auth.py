import pytest

def test_registration_empty_email(client):
    resp = client.post(
        "/registration",
        data={"username": "user1", "email": "", "password": "secret"},
    )
    assert resp.status_code == 400
    assert b"Email cannot be empty" in resp.data


def test_registration_empty_password(client):
    resp = client.post(
        "/registration",
        data={"username": "user1", "email": "u1@example.com", "password": ""},
    )
    assert resp.status_code == 400
    assert b"Password cannot be empty" in resp.data


def test_registration_duplicate_username(client, sample_data):

    resp = client.post(
        "/registration",
        data={
            "username": "admin",  # вече съществува
            "email": "other@example.com",
            "password": "secret",
        },
    )

    assert resp.status_code == 200
    assert b"Username already exists" in resp.data


def test_registration_duplicate_email(client, sample_data):
    resp = client.post(
        "/registration",
        data={
            "username": "otheruser",
            "email": "admin@example.com",
            "password": "secret",
        },
    )
    assert resp.status_code == 200
    assert b"Email already exists" in resp.data


def test_login_empty_username_or_email(client):
    resp = client.post(
        "/login",
        data={"usernameOrEmail": "", "password": "secret"},
    )
    assert resp.status_code == 400
    assert b"Email cannot be empty" in resp.data


def test_login_empty_password(client):
    resp = client.post(
        "/login",
        data={"usernameOrEmail": "user@example.com", "password": ""},
    )
    assert resp.status_code == 400
    assert b"Password cannot be empty" in resp.data


def test_login_nonexistent_user(client):
    resp = client.post(
        "/login",
        data={"usernameOrEmail": "ghost@example.com", "password": "secret"},
    )
    assert resp.status_code == 400
    assert b"User does not exist" in resp.data


def test_login_wrong_password_after_registration(client):
    client.post(
        "/registration",
        data={
            "username": "vasya",
            "email": "vasya@example.com",
            "password": "right-password",
        },
    )

    resp = client.post(
        "/login",
        data={
            "usernameOrEmail": "vasya@example.com",
            "password": "wrong-password",
        },
    )
    assert resp.status_code == 400
    assert b"Invalid password" in resp.data
