from models.reservation import ReservationStatus


def login_as(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["role"] = user.role.value


def test_my_reservations_requires_login(client):
    resp = client.get("/my_reservations")
    assert resp.status_code in (302, 303)


def test_my_reservations_ok_for_client(client, sample_data):
    login_as(client, sample_data["client"])
    resp = client.get("/my_reservations")
    assert resp.status_code == 200
    assert sample_data["restaurant"].name.encode() in resp.data


def test_profile_cancel_reservation(client, sample_data, db_session):
    login_as(client, sample_data["client"])
    reservation = sample_data["reservation"]
    resp = client.post(f"/my_reservations/cancel/{reservation.id}")
    assert resp.status_code in (302, 303)

    db_session.refresh(reservation)
    assert reservation.status == ReservationStatus.canceled


def test_provider_restaurants_page(client, sample_data):
    login_as(client, sample_data["provider"])
    resp = client.get("/my_restaurants")
    assert resp.status_code == 200


def test_provider_reservations_page(client, sample_data):
    login_as(client, sample_data["provider"])
    resp = client.get("/reservations")
    assert resp.status_code == 200


def test_provider_change_status_accept(client, sample_data, db_session):
    login_as(client, sample_data["provider"])
    reservation = sample_data["reservation"]
    resp = client.post(
        f"/reservations/{reservation.id}/change-status",
        data={"status": "accepted"},
    )
    assert resp.status_code in (302, 303)
    db_session.refresh(reservation)
    assert reservation.status == ReservationStatus.accepted


def test_admin_reservations_page(client, sample_data):
    login_as(client, sample_data["admin"])
    resp = client.get("/reservations", follow_redirects=False)
    assert resp.status_code == 200


def test_admin_users_page(client, sample_data):
    login_as(client, sample_data["admin"])
    resp = client.get("/users", follow_redirects=False)
    assert resp.status_code == 200


def test_admin_change_role_and_delete_user(client, sample_data, db_session):
    login_as(client, sample_data["admin"])
    user_to_change = sample_data["client"]

    resp = client.post(
        "/users/change-role",
        data={"user_id": str(user_to_change.id), "role": "provider"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)

    db_session.refresh(user_to_change)
    assert user_to_change.role.value == "provider"

    resp = client.post(
        "/users/delete",
        data={"user_id": str(user_to_change.id)},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 303)
