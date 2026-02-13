from models.reservation import ReservationStatus


def login_as(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["role"] = user.role.value


def test_restaurant_details_not_found(client):
    resp = client.get("/restaurants/99999/details")
    assert resp.status_code == 404
    assert b"Restaurant not found" in resp.data


def test_edit_restaurant_sets_session_and_redirects(client, sample_data):
    restaurant = sample_data["restaurant"]
    provider = sample_data["provider"]

    login_as(client, provider)

    resp = client.get(
        f"/restaurants/{restaurant.id}/edit",
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)
    assert "/restaurants/add_new_restaurant" in resp.headers["Location"]

    with client.session_transaction() as sess:
        assert sess["edit_restaurant_id"] == restaurant.id
        assert sess["edit_restaurant_name"] == restaurant.name
        assert sess["edit_restaurant_address"] == restaurant.address
        assert sess["edit_restaurant_category"] == restaurant.category


def test_provider_change_status_reservation_not_found(client, sample_data):
    provider = sample_data["provider"]
    login_as(client, provider)

    resp = client.post(
        "/reservations/99999/change-status",
        data={"status": "accepted"},
    )

    assert resp.status_code == 404
    assert b"Reservation not found" in resp.data


def test_provider_change_status_invalid_status_does_not_change(client, sample_data, db_session):
    provider = sample_data["provider"]
    reservation = sample_data["reservation"]

    assert reservation.status == ReservationStatus.pending

    login_as(client, provider)

    resp = client.post(
        f"/reservations/{reservation.id}/change-status",
        data={"status": "something-invalid"},
        follow_redirects=False,
    )

    assert resp.status_code in (302, 303)

    db_session.refresh(reservation)
    assert reservation.status == ReservationStatus.pending
