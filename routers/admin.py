from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload

from db import SessionLocal

from models import User, Reservation
from models.reservation import Table, ReservationStatus
from models.user import UserRole
from .profile import auto_complete_old_reservations

admin = Blueprint('admin', __name__)

@admin.route("/reservations", methods=["GET", "POST"])
def admin_reservations():
    db = SessionLocal()

    auto_complete_old_reservations(db)

    reservations = db.execute(select(Reservation).options(joinedload(Reservation.restaurant),
                                      joinedload(Reservation.table).joinedload(Table.zone))
                              .order_by(Reservation.date.desc())).scalars().all()

    db.close()

    return render_template("admin/admin_reservations.html",
                           reservations=reservations, ReservationStatus=ReservationStatus)

@admin.route("/users")
def users():
    db = SessionLocal()
    users_list = db.execute(select(User)).scalars().all()
    db.close()
    return render_template("admin/users.html", users=users_list)

@admin.route("/users/change-role", methods=["POST"])
def change_role():
    db = SessionLocal()

    user_id = request.form.get("user_id")
    role_id = request.form.get("role")

    if not user_id:
        db.close()
        return "Missing user_id", 400

    if not role_id:
        db.close()
        return "Missing role_id", 400

    user = db.execute(select(User).where(User.id == user_id)).scalar()

    if not user:
        db.close()
        return "The user is not exist", 400

    user.role = UserRole(role_id)
    db.commit()
    db.close()

    return redirect(url_for("admin.users"))

@admin.route("/users/delete", methods=["POST"])
def delete_user():
    db = SessionLocal()

    user_id = request.form.get("user_id")
    if not user_id:
        db.close()
        return "Missing user_id", 400

    user = db.execute(select(User).where(User.id == user_id)).scalars().first()

    if not user:
        db.close()
        return "The user is not exist", 400

    reservations = db.execute(
        select(Reservation).where(
            or_(
                Reservation.client_id == user.id,
                Reservation.provider_id == user.id,
            )
        )
    ).scalars().all()

    for res in reservations:
        db.delete(res)

    db.delete(user)

    db.commit()
    db.close()

    return redirect(url_for("admin.users"))
