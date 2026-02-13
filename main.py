import os

from dotenv import load_dotenv
from flask import Flask, render_template

from routers.admin import admin
from routers.auth import auth
from routers.provider import provider
from routers.restaurants import restaurants
from routers.create_restaurant import create_restaurant
from routers.reservation import reservation
from routers.profile import profile
from routers.create_review import review

from seed_admin import create_admin_if_not_exist

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

@app.route('/')
def home():
    return render_template('home.html')

app.register_blueprint(auth)
app.register_blueprint(restaurants)
app.register_blueprint(admin)
app.register_blueprint(provider)
app.register_blueprint(create_restaurant)
app.register_blueprint(reservation)
app.register_blueprint(profile)
app.register_blueprint(review)

if __name__ == '__main__':
    create_admin_if_not_exist()
    app.run(debug=True)
