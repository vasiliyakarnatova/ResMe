from flask import Blueprint, render_template, session, redirect, url_for
from sqlalchemy import select, exists
from sqlalchemy.orm import joinedload

from db import SessionLocal
from models import Review
from models.reservation import Restaurant, Table, Zone

restaurants = Blueprint('restaurants', __name__)

@restaurants.route("/restaurants")
def list_restaurants():
    db = SessionLocal()
    restaurants_list = db.execute(select(Restaurant)
        .where(exists().where(Zone.restaurant_id == Restaurant.id),
        exists().where(Table.restaurant_id == Restaurant.id))).scalars().all()
    db.close()
    return render_template("restaurants/restaurants.html", restaurants=restaurants_list)

@restaurants.route("/restaurants/<int:restaurant_id>/details")
def details_restaurant(restaurant_id: int):
    db = SessionLocal()
    restaurant = db.execute(select(Restaurant)
                            .options(joinedload(Restaurant.reviews).joinedload(Review.user))
                            .where(Restaurant.id == restaurant_id)).scalars().first()
    db.close()

    if not restaurant:
        return "Restaurant not found.", 404

    return render_template("restaurants/details.html", restaurant=restaurant)

@restaurants.route("/restaurants/<int:restaurant_id>/edit")
def edit_restaurant(restaurant_id: int):
    db = SessionLocal()

    restaurant = db.execute(select(Restaurant)
                            .where(Restaurant.id == restaurant_id)).scalars().first()

    if not restaurant:
        return "Restaurant not found.", 404

    session["edit_restaurant_id"] = restaurant.id

    session["edit_restaurant_name"] = restaurant.name
    session["edit_restaurant_address"] = restaurant.address
    session["edit_restaurant_category"] = restaurant.category
    session["edit_restaurant_open_time"] = restaurant.open_time.isoformat()
    session["edit_restaurant_close_time"] = restaurant.close_time.isoformat()
    session["edit_restaurant_description"] = restaurant.description

    session["edit_zone_ids"] = [zone.id for zone in restaurant.zones]
    session["edit_zone_names"] = [zone.name for zone in restaurant.zones]

    session["edit_table_ids"] = [table.id for table in restaurant.tables]
    session["edit_table_names"] = [table.name for table in restaurant.tables]
    session["edit_table_capacities"] = [table.capacity for table in restaurant.tables]
    session["edit_table_zone_ids"] = [table.zone_id for table in restaurant.tables]

    session["edit_redirect"] = "restaurants.details_restaurant"

    return redirect(url_for("create_restaurant.add_new_restaurant"))
