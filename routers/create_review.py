from flask import Blueprint, request, session, redirect, url_for, render_template
from sqlalchemy import select

from db import SessionLocal
from models import Restaurant, Review

review = Blueprint('review', __name__)

@review.route('/restaurants/<int:restaurant_id>/reviews', methods=['GET', 'POST'])
def create_review(restaurant_id: int):
    db = SessionLocal()

    user_id = session.get('user_id')
    restaurant = db.execute(select(Restaurant)
                            .where(Restaurant.id == restaurant_id)).scalars().first()

    if not restaurant:
        db.close()
        return "Restaurant not found", 400

    if request.method == 'POST':
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment') or None

        new_review = Review(user_id=user_id, restaurant_id=restaurant_id,
                        rating=rating, comment=comment)
        db.add(new_review)
        db.commit()
        db.close()

        return redirect(url_for('restaurants.details_restaurant',
                                restaurant_id=restaurant_id))

    db.close()
    return render_template("review/create_review.html",
                           restaurant=restaurant)