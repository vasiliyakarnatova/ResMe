from models.user import User, UserRole
from models.reservation import Restaurant, Zone, Table, Reservation, ReservationStatus, Review
import datetime


def test_user_model_basic(db_session):
    user = User(username="u1", email="u1@example.com", password="pw", role=UserRole.user)
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == "u1"
    assert user.role == UserRole.user


def test_restaurant_zone_table_relationships(db_session, sample_data):
    restaurant = sample_data["restaurant"]
    zone = sample_data["zone"]
    table = sample_data["table"]

    assert zone.restaurant_id == restaurant.id
    assert table.restaurant_id == restaurant.id
    assert table.zone_id == zone.id

    assert zone in restaurant.zones
    assert table in restaurant.tables


def test_reservation_and_review_models(db_session, sample_data):
    client = sample_data["client"]
    restaurant = sample_data["restaurant"]
    table = sample_data["table"]

    when = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=2)
    reservation = Reservation(
        date=when,
        status=ReservationStatus.accepted,
        client_id=client.id,
        provider_id=sample_data["provider"].id,
        restaurant_id=restaurant.id,
        table_id=table.id,
        additional_notes="notes",
    )
    db_session.add(reservation)
    db_session.commit()

    assert reservation.id is not None
    assert reservation.client_id == client.id
    assert reservation.restaurant_id == restaurant.id
    assert reservation.status == ReservationStatus.accepted

    review = Review(user_id=client.id, restaurant_id=restaurant.id, rating=5, comment="Great!")
    db_session.add(review)
    db_session.commit()

    assert review.id is not None
    assert review.user_id == client.id
    assert review.restaurant_id == restaurant.id
    assert review.rating == 5
