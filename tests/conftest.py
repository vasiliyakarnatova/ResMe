import datetime
import pytest

from main import app
from db import Base, engine, SessionLocal
from models.user import User, UserRole
from models.reservation import Restaurant, Zone, Table, Reservation, ReservationStatus


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def sample_data(db_session):
    admin = User(username="admin", email="admin@example.com", password="secret", role=UserRole.admin)
    provider = User(username="provider", email="provider@example.com", password="secret", role=UserRole.provider)
    client_user = User(username="client", email="client@example.com", password="secret", role=UserRole.user)

    db_session.add_all([admin, provider, client_user])
    db_session.commit()

    open_time = datetime.time(9, 0)
    close_time = datetime.time(22, 0)

    restaurant = Restaurant(
        name="Test Restaurant",
        address="Test Street 1",
        category="Italian",
        description="Test description",
        open_time=open_time,
        close_time=close_time,
        owner_id=provider.id,
        image_url=None,
    )
    db_session.add(restaurant)
    db_session.commit()

    zone = Zone(name="Main hall", restaurant_id=restaurant.id)
    db_session.add(zone)
    db_session.commit()

    table = Table(name="T1", capacity=4, restaurant_id=restaurant.id, zone_id=zone.id)
    db_session.add(table)
    db_session.commit()

    res_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    reservation = Reservation(
        date=res_date,
        status=ReservationStatus.pending,
        client_id=client_user.id,
        provider_id=provider.id,
        restaurant_id=restaurant.id,
        table_id=table.id,
        additional_notes="Test reservation",
    )
    db_session.add(reservation)
    db_session.commit()

    return {
        "admin": admin,
        "provider": provider,
        "client": client_user,
        "restaurant": restaurant,
        "zone": zone,
        "table": table,
        "reservation": reservation,
    }