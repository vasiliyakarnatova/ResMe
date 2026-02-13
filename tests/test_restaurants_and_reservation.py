import datetime


def login_as(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["role"] = user.role.value


def test_restaurants_list_page(client, sample_data):
    resp = client.get("/restaurants")
    assert resp.status_code == 200
    assert sample_data["restaurant"].name.encode() in resp.data


def test_restaurant_details_page(client, sample_data):
    restaurant = sample_data["restaurant"]
    resp = client.get(f"/restaurants/{restaurant.id}/details")
    assert resp.status_code == 200
    assert restaurant.name.encode() in resp.data


def test_choose_date_page(client, sample_data):
    restaurant = sample_data["restaurant"]
    resp = client.get(f"/restaurant/reserve/{restaurant.id}/date-choosing")
    assert resp.status_code == 200


def test_select_people_count_page(client, sample_data):
    restaurant = sample_data["restaurant"]
    today = sample_data["reservation"].date.date().isoformat()
    resp = client.get(
        f"/restaurant/reserve/{restaurant.id}/people-count-selecting",
        query_string={"date": today},
    )
    assert resp.status_code == 200


def test_choose_time_page(client, sample_data):
    restaurant = sample_data["restaurant"]
    day = sample_data["reservation"].date.date().isoformat()
    resp = client.get(
        f"/restaurant/reserve/{restaurant.id}/time-choosing",
        query_string={"date": day, "people": 2},
    )
    assert resp.status_code == 200


def test_choose_zone_page(client, sample_data):
    restaurant = sample_data["restaurant"]
    res = sample_data["reservation"]
    date_str = res.date.date().isoformat()
    time_str = res.date.time().replace(microsecond=0).isoformat(timespec="minutes")
    resp = client.get(
        f"/restaurant/reserve/{restaurant.id}/zone-choosing",
        query_string={"date": date_str, "time": time_str, "people": 2},
    )
    assert resp.status_code == 200
