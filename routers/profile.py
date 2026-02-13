import datetime

from flask import Blueprint, session, redirect, render_template, url_for
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy import update

from db import SessionLocal
from models import Reservation, User
from models.reservation import ReservationStatus, Table

profile = Blueprint('profile', __name__)

def auto_complete_old_reservations(db):
    now = datetime.datetime.now()

    one_hour_ago = now - datetime.timedelta(hours=1)

    db.execute(update(Reservation).where(Reservation.status == ReservationStatus.accepted,
                            Reservation.date <= one_hour_ago).values(status=ReservationStatus.completed))
    db.commit()


@profile.route("/my_reservations")
def my_reservations():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    db = SessionLocal()

    auto_complete_old_reservations(db)

    user_id = session.get("user_id")

    user = db.execute(select(User).where(User.id == user_id)).scalars().first()

    reservations = db.execute(
        select(Reservation)
        .options(
            joinedload(Reservation.restaurant),
            joinedload(Reservation.table).joinedload(Table.zone)
        )
        .where(Reservation.client_id == session["user_id"])
        .order_by(Reservation.date.desc())
    ).scalars().all()

    db.close()

    return render_template("profile/my_reservations.html", user=user,
                           reservations=reservations, ReservationStatus=ReservationStatus)

@profile.route("/my_reservations/cancel/<int:reservation_id>", methods=["GET", "POST"])
def cancel_reservation(reservation_id: int):
    db = SessionLocal()

    reservation = db.execute(select(Reservation)
                             .where(Reservation.id == reservation_id)).scalars().one()

    if not reservation:
        db.close()
        return "Reservation not found.", 404

    reservation.status = ReservationStatus.canceled
    db.commit()
    db.close()

    return redirect(url_for("profile.my_reservations"))

@profile.route("/my_reservations/<int:reservation_id>/edit", methods=["GET", "POST"])
def profile_reservation_edit(reservation_id: int):
    db = SessionLocal()

    reservation = db.execute(select(Reservation)
                             .options(joinedload(Reservation.restaurant),
                                      joinedload(Reservation.table).joinedload(Table.zone))
                             .where(Reservation.id == reservation_id)).scalars().first()

    if not reservation:
        db.close()
        return "Reservation not found", 404

    restaurant = reservation.restaurant

    session["edit_reservation_id"] = reservation.id
    session["edit_reservation_date"] = reservation.date.date().isoformat()
    session["edit_reservation_time"] = reservation.date.time().strftime("%H:%M")
    session["edit_reservation_people_count"] = reservation.table.capacity
    session["edit_reservation_zone"] = reservation.table.zone_id
    session["edit_reservation_zone_name"] = reservation.table.zone.name

    session["edit_redirect"] = "profile.my_reservations"

    db.close()

    return redirect(url_for("reservation.choose_date", restaurant_id=restaurant.id))
