from flask import Blueprint, render_template, session, request, redirect, url_for
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from db import SessionLocal
from models.reservation import Restaurant, Reservation, Table, ReservationStatus, Zone

from .profile import auto_complete_old_reservations

provider = Blueprint("provider", __name__)

@provider.route("/my_restaurants")
def provider_restaurants():
    db = SessionLocal()
    restaurants_list = db.execute(select(Restaurant)
                                  .where(Restaurant.owner_id == session['user_id'])).scalars().all()
    db.close()
    return render_template("provider/provider_restaurants.html",
                           restaurants=restaurants_list)

@provider.route("/reservations")
def provider_reservations():
    db = SessionLocal()

    auto_complete_old_reservations(db)

    reservations = db.execute(select(Reservation)
                              .options(joinedload(Reservation.restaurant),
                            joinedload(Reservation.table).joinedload(Table.zone)
                        ).where(Reservation.provider_id == session['user_id'])).scalars().all()

    db.close()

    return render_template("provider/provider_reservations.html",
                           reservations=reservations, ReservationStatus=ReservationStatus)

@provider.route("/reservations/<int:reservation_id>/change-status", methods=["GET", "POST"])
def provider_reservation_change_status(reservation_id):
    db = SessionLocal()

    status = request.form.get("status")

    reservation = db.execute(select(Reservation)
                             .where(Reservation.id == reservation_id)).scalars().first()

    if not reservation:
        db.close()
        return "Reservation not found", 404

    if status not in ("accepted", "canceled"):
        db.close()
        return redirect(url_for("provider.provider_reservations"))

    reservation.status = ReservationStatus(status)
    db.commit()
    db.close()

    return redirect(url_for("provider.provider_reservations"))

@provider.route("/reservations/<int:reservation_id>/edit", methods=["GET", "POST"])
def provider_reservation_edit(reservation_id: int):
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

    session["edit_redirect"] = "provider.provider_reservations"

    db.close()

    return redirect(url_for("reservation.choose_date", restaurant_id=restaurant.id))
