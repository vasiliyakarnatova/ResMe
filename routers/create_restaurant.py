import datetime

from flask import Blueprint, session, request, render_template, redirect, url_for
from sqlalchemy import select, delete

from db import SessionLocal
from models import Restaurant
from models.reservation import Zone, Table

create_restaurant = Blueprint("create_restaurant", __name__)

@create_restaurant.route("/restaurants/add_new_restaurant", methods=['GET', 'POST'])
def add_new_restaurant():
    edit_mode = "edit_restaurant_id" in session

    if request.method == "GET":
        return render_template("restaurants/add_new_restaurant.html", edit_mode=edit_mode)

    name = request.form.get("name")
    address = request.form.get("address")
    category = request.form.get("category")
    open_time_str = request.form.get("open_time")
    close_time_str = request.form.get("close_time")
    description = request.form.get("description")

    if (not name or not address or not category
            or not open_time_str or not close_time_str or not description):
        return "Missing required fields", 400

    open_time = datetime.time.fromisoformat(open_time_str)
    close_time = datetime.time.fromisoformat(close_time_str)

    session["edit_restaurant_name"] = name
    session["edit_restaurant_address"] = address
    session["edit_restaurant_category"] = category
    session["edit_restaurant_open_time"] = open_time_str
    session["edit_restaurant_close_time"] = close_time_str
    session["edit_restaurant_description"] = description

    db = SessionLocal()

    if edit_mode:
        restaurant_id = session.get("edit_restaurant_id")

        restaurant = db.execute(select(Restaurant)
                                .where(Restaurant.id == restaurant_id)).scalars().first()

        if not restaurant:
            db.close()
            return "Restaurant not found", 404

        restaurant.name = name
        restaurant.address = address
        restaurant.category = category
        restaurant.open_time = open_time
        restaurant.close_time = close_time
        restaurant.description = description

        restaurant_id = restaurant.id

        db.commit()
        db.close()

        return redirect(url_for("create_restaurant.add_zones", restaurant_id=restaurant_id))

    user_id = session.get("user_id")

    new_restaurant = Restaurant(name=name, address=address,
                            category=category, open_time=open_time,
                            close_time=close_time, description=description, owner_id=user_id, image_url=None)

    db.add(new_restaurant)
    db.commit()

    new_restaurant_id = new_restaurant.id

    db.close()

    return redirect(url_for("create_restaurant.add_zones", restaurant_id=new_restaurant_id))

@create_restaurant.route("/restaurants/<restaurant_id>/add_zones", methods=['GET', 'POST'])
def add_zones(restaurant_id: int):

    edit_mode = "edit_restaurant_id" in session

    db = SessionLocal()
    restaurant = db.execute(select(Restaurant)
                            .where(Restaurant.id == restaurant_id)).scalars().first()

    if not restaurant:
        db.close()
        return "Restaurant not found", 404

    restaurant_id = restaurant.id

    if request.method == "POST":

        zone_id = request.form.get("zone_id", type=int)
        zone_for_update = request.form.get("zone_name")
        zone_for_create = request.form.get("zone")

        if zone_id:

            zone = (db.execute(select(Zone).where(Zone.id == zone_id,
                                                 Zone.restaurant_id == restaurant.id))
                    .scalars().first())

            if not zone:
                db.close()
                return "Zone not found", 404

            if not zone_for_update:
                db.close()
                return "Zone name is required", 400

            zone.name = zone_for_update
            db.commit()
            db.close()

            return redirect(url_for("create_restaurant.add_zones", restaurant_id=restaurant_id))

        if not zone_for_create:
            db.close()
            return "The restaurant must own at least one zone", 404

        zone = Zone(name=zone_for_create, restaurant_id=restaurant.id)
        db.add(zone)
        db.commit()
        db.close()
        return redirect(url_for("create_restaurant.add_zones", restaurant_id=restaurant_id))

    zones = db.execute(select(Zone)
                       .where(Zone.restaurant_id == restaurant.id)).scalars().all()

    db.close()
    return render_template("restaurants/add_zones.html",
                           restaurant=restaurant, zones=zones, edit_mode=edit_mode)

@create_restaurant.route("/restaurants/<restaurant_id>/zones/<zone_id>/delete", methods=['POST'])
def delete_zones(restaurant_id: int, zone_id: int):

    db = SessionLocal()

    restaurant = db.execute(select(Restaurant)
                            .where(Restaurant.id == restaurant_id)).scalars().first()

    if not restaurant:
        db.close()
        return "Restaurant not found", 404

    zone = db.execute(select(Zone).where(Zone.id == zone_id)).scalars().first()

    if not zone or zone.restaurant_id != restaurant.id:
        db.close()
        return "Zone not found", 404

    db.execute(delete(Table).where(Table.zone_id == zone.id))
    db.execute(delete(Zone).where(Zone.id == zone.id))

    restaurant_id = restaurant.id

    db.commit()
    db.close()

    return redirect(url_for("create_restaurant.add_zones",
                            restaurant_id=restaurant_id))

def generate_tables(db, count: int, seats: int, zone: Zone, restaurant: Restaurant):
    for i in range(1, count + 1):
        table = Table(name=f"{zone.name}_{seats}seats_{i}",
                      capacity=seats, zone_id=zone.id, restaurant_id=restaurant.id)
        db.add(table)

@create_restaurant.route("/restaurants/<restaurant_id>/add_tables", methods=['GET', 'POST'])
def add_tables(restaurant_id: int):

    edit_mode = "edit_restaurant_id" in session

    db = SessionLocal()
    restaurant = db.execute(select(Restaurant).where(Restaurant.id == restaurant_id)).scalars().first()

    if not restaurant:
        db.close()
        return "Restaurant not found", 404

    restaurant_id = restaurant.id

    tables_exist = db.execute(select(Table).where(Table.restaurant_id == restaurant_id)).first()

    if tables_exist and request.method == "GET" and not edit_mode:
        db.close()
        return redirect(url_for("provider.provider_restaurants"))

    zones = db.execute(select(Zone).where(Zone.restaurant_id == restaurant.id)).scalars().all()

    if not zones:
        db.close()
        return redirect(url_for("create_restaurant.add_zones", restaurant_id=restaurant_id))

    if request.method == "POST":
        if edit_mode:
            db.execute(delete(Table).where(Table.restaurant_id == restaurant.id))
            db.commit()

        for zone in zones:
            two_seated = request.form.get(f"two_seated_{zone.id}", type=int)
            four_seated = request.form.get(f"four_seated_{zone.id}", type=int)
            six_seated = request.form.get(f"six_seated_{zone.id}", type=int)
            ten_seated = request.form.get(f"ten_seated_{zone.id}", type=int)

            generate_tables(db, two_seated, 2, zone, restaurant)
            generate_tables(db, four_seated, 4, zone, restaurant)
            generate_tables(db, six_seated, 6, zone, restaurant)
            generate_tables(db, ten_seated, 10, zone, restaurant)

        db.commit()
        db.close()

        redirect_endpoint = session.pop("edit_redirect", None)

        if redirect_endpoint:
            if redirect_endpoint == "restaurants.details_restaurant":
                return redirect(url_for(redirect_endpoint, restaurant_id=restaurant_id))
            return redirect(url_for(redirect_endpoint))

        return redirect(url_for("provider.provider_restaurants"))

    db.close()
    return render_template('restaurants/add_tables.html', restaurant=restaurant, zones=zones)
