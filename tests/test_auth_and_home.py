def test_home_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"Book" in resp.data


def test_registration_get_redirect_if_logged_in(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 123
    resp = client.get("/registration")
    assert resp.status_code in (302, 303)
    assert resp.headers["Location"].endswith("/")


def test_registration_get_ok_if_anonymous(client):
    resp = client.get("/registration")
    assert resp.status_code == 200


def test_login_get_ok(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_logout_clears_session(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["role"] = "user"

    resp = client.get("/logout")
    assert resp.status_code in (302, 303)

    with client.session_transaction() as sess:
        assert "user_id" not in sess
        assert "role" not in sess
