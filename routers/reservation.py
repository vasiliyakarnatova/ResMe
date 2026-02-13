import datetime

import calendar

from flask import Blueprint, render_template, request, redirect, url_for, session
from sqlalchemy import select, func

from db import SessionLocal
from models import Restaurant
from models.reservation import Table, Reservation, ReservationStatus, Zone

reservation = Blueprint("reservation", __name__)


def generate_hours(restaurant: Restaurant) -> list[datetime.time]:
    slots = []
    start = restaurant.open_time.hour
    end = restaurant.close_time.hour

    if end <= start:
        end += 24

    for hour in range(start, end):
        real_hour = hour % 24
        slots.append(datetime.time(real_hour, 0))

    return slots


def get_day_status(db, restaurant : Restaurant, day: datetime.date) -> str:
    tables = db.execute(select(Table).where(Table.restaurant_id == restaurant.id)).scalars().all()

    if not tables:
        return "full"

    slots = generate_hours(restaurant)

    for slot in slots:
        reservations = db.execute(select(func.count(Reservation.id)).
                                  where(Reservation.restaurant_id == restaurant.id,
                             Reservation.date == datetime.datetime.combine(day, slot))).scalar()

        if reservations < len(tables):
            return "free"

    return "full"


def get_free_time_slots(db, restaurant:Restaurant, day: datetime.date, people: int) -> list[datetime.time]:
    slots = generate_hours(restaurant)

    free_slots = []

    tables = db.execute(select(Table).where(Table.restaurant_id == restaurant.id,
                                            Table.capacity >= people)).scalars().all()

    if not tables:
        return free_slots

    for slot in slots:
        has_free_tables = False
        for table in tables:
            search_reservation = db.execute(select(Reservation)
                                     .where(Reservation.restaurant_id == restaurant.id,
                                    Reservation.date == datetime.datetime.combine(day, slot),
                                    Reservation.table_id == table.id)).scalars().first()

            if not search_reservation:
                has_free_tables = True
                break

        if has_free_tables:
            free_slots.append(slot)

    return free_slots


def find_free_table_in_zone(db, restaurant: Restaurant, day: datetime.datetime, people: int, zone_id: int) -> Table | None:
    query = select(Table).where(Table.restaurant_id == restaurant.id, Table.capacity >= people)

    if zone_id is not None:
        query = query.where(Table.zone_id == zone_id)

    tables = db.execute(query).scalars().all()

    for table in tables:
        search_reservation = db.execute(select(Reservation)
                                 .where(Reservation.restaurant_id == restaurant.id,
                                Reservation.table_id == table.id,
                                Reservation.date == day)).scalars().first()

        if not search_reservation:
            return table

    return None


@reservation.route("/restaurant/reserve/<restaurant_id>/date-choosing", methods=["GET", "POST"])
def choose_date(restaurant_id: int):
    db = SessionLocal()

    restaurant = db.execute(select(Restaurant)
                            .where(Restaurant.id == restaurant_id)).scalars().first()

    if not restaurant:
        db.close()
        return "Restaurant not found", 404

    today = datetime.date.today()
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if year is None or month is None:
        year = today.year
        month = today.month

    cal = calendar.Calendar(firstweekday=0)
    month_days = list(cal.itermonthdates(year, month))

    weeks = []
    week = []
    availability = {}

    for day in month_days:
        if day.month != month:
            week.append(None)
        else:
            if day < today:
                status = "past"
            else:
                status = get_day_status(db, restaurant, day)
            availability[day] = status
            week.append(day)

        if len(week) == 7:
            weeks.append(week)
            week = []

    if week:
        weeks.append(week)

    prev_year, prev_month = year, month - 1
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_year, next_month = year, month + 1
    if next_month == 13:
        next_month = 1
        next_year += 1

    db.close()

    is_edit = 'edit_reservation_id' in session
    edit_date = session.get('edit_reservation_date')

    return render_template("reservation/choose_date.html",
                           restaurant=restaurant, year=year, month=month, weeks=weeks,
                           availability=availability, prev_year=prev_year,
                           prev_month=prev_month, next_year=next_year, next_month=next_month,
                           is_edit=is_edit, edit_date=edit_date)


@reservation.route("/restaurant/reserve/<restaurant_id>/people-count-selecting",
                   methods=["GET", "POST"])
def select_people_count(restaurant_id: int):
    if request.method == "GET":
        date_str = request.args.get("date")
    else:
        date_str = request.form.get("date") or request.args.get("date")

    if not date_str:
        return redirect(url_for("reservation.choose_date", restaurant_id=restaurant_id))

    selected_date = datetime.date.fromisoformat(date_str)

    db = SessionLocal()

    restaurant = db.execute(select(Restaurant)
                            .where(Restaurant.id == restaurant_id)).scalars().first()

    if not restaurant:
        db.close()
        return "Restaurant not found", 404

    if request.method == "POST":
        people = int(request.form.get("count"))
        db.close()
        return redirect(url_for("reservation.choose_time", restaurant_id=restaurant_id,
                                people=people, date=selected_date.isoformat()))
    db.close()

    is_edit = 'edit_reservation_id' in session
    edit_people = session.get('edit_reservation_people_count')

    return render_template("reservation/select_people_count.html", selected_date=selected_date,
                           is_edit=is_edit, edit_people=edit_people)


@reservation.route("/restaurant/reserve/<restaurant_id>/time-choosing", methods=["GET", "POST"])
def choose_time(restaurant_id: int):
    if request.method == "GET":
        date_str = request.args.get("date")
        people = request.args.get("people")
    else:
        date_str = request.form.get("date")
        people = request.form.get("people")

    if not date_str:
        return redirect(url_for("reservation.choose_date", restaurant_id=restaurant_id))

    if not people:
        return redirect(url_for("reservation.select_people_count", restaurant_id=restaurant_id))

    selected_date = datetime.date.fromisoformat(date_str)

    db = SessionLocal()

    restaurant = db.execute(select(Restaurant)
                            .where(Restaurant.id == restaurant_id)).scalars().first()

    if not restaurant:
        db.close()
        return "Restaurant not found", 404

    if request.method == "POST":
        time = request.form.get("time")
        db.close()
        return redirect(url_for("reservation.choose_zone", restaurant_id=restaurant_id,
                                people=people, date=selected_date.isoformat(), time=time))

    all_slots = generate_hours(restaurant)
    free_slots = set(get_free_time_slots(db, restaurant, selected_date, people))
    db.close()

    slot_rows = []
    row = []

    for slot in all_slots:
        row.append({"time": slot, "free": slot in free_slots})

        if len(row) == 5:
            slot_rows.append(row)
            row = []

    if row:
        slot_rows.append(row)

    is_edit = 'edit_reservation_id' in session
    edit_time = session.get('edit_reservation_time')

    return render_template("reservation/choose_time.html",
                           restaurant=restaurant, date=selected_date, people=people,
                           slot_rows=slot_rows, is_edit=is_edit, edit_time=edit_time)


@reservation.route("/restaurant/reserve/<restaurant_id>/zone-choosing", methods=["GET", "POST"])
def choose_zone(restaurant_id: int):
    if request.method == "GET":
        date_str = request.args.get("date")
        people = request.args.get("people", type=int)
        time = request.args.get("time")
        zone_id = None
    else:
        date_str = request.form.get("date")
        people = int(request.form.get("people"))
        time = request.form.get("time")
        zone_id = request.form.get("zone_id", type=int)

    if not date_str:
        return redirect(url_for("reservation.choose_date", restaurant_id=restaurant_id))

    if not people:
        return redirect(url_for("reservation.select_people_count",
                                restaurant_id=restaurant_id))

    if not time:
        return redirect(url_for("reservation.choose_time",
                                restaurant_id=restaurant_id))

    selected_date = datetime.date.fromisoformat(date_str)
    selected_time = datetime.time.fromisoformat(time)
    reservation_datetime = datetime.datetime.combine(selected_date, selected_time)

    db = SessionLocal()

    restaurant = db.execute(select(Restaurant)
                            .where(Restaurant.id == restaurant_id)).scalars().first()

    if not restaurant:
        db.close()
        return "Restaurant not found", 404

    if request.method == "POST" and zone_id:
        free_table = find_free_table_in_zone(db, restaurant, reservation_datetime, people, zone_id)

        edit_id = session.pop("edit_reservation_id", None)

        if edit_id:

            existing = db.execute(select(Reservation)
                                  .where(Reservation.id == edit_id)).scalars().first()
            if not existing:
                db.close()
                return "Reservation not found", 404

            existing.date = reservation_datetime
            existing.table_id = free_table.id

            db.commit()
            db.close()

            redirect_endpoint = session.pop("edit_redirect", None)
            if redirect_endpoint:
                return redirect(url_for(redirect_endpoint))

            return redirect(url_for("restaurants.list_restaurants"))

        else:
            new_reservation = Reservation(date=reservation_datetime,
                                          status=ReservationStatus.pending,
                                          client_id=session["user_id"],
                                          provider_id=restaurant.owner_id,
                                          restaurant_id=restaurant.id,
                                          table_id=free_table.id)
            db.add(new_reservation)
            db.commit()
            db.close()
            return redirect(url_for("restaurants.list_restaurants"))

    zones = db.execute(select(Zone).where(Zone.restaurant_id == restaurant_id)).scalars().all()

    zones_template = []
    for zone in zones:
        free_table = find_free_table_in_zone(db, restaurant, reservation_datetime, people, zone.id)
        zones_template.append({"zone": zone, "free": free_table is not None})

    is_edit = 'edit_reservation_id' in session
    edit_zone_id = session.get("edit_reservation_zone")
    edit_zone_name = session.get("edit_reservation_zone_name")

    if edit_zone_name is None and edit_zone_id is not None:
        for zone in zones:
            if zone.id == edit_zone_id:
                edit_zone_name = zone.name
                break

    db.close()

    return render_template("reservation/choose_zone.html",
                           restaurant=restaurant, date=selected_date, time=selected_time,
                           people=people, zones=zones_template, is_edit=is_edit,
                           edit_zone_id=edit_zone_id, edit_zone_name=edit_zone_name)
