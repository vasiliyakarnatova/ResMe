import bcrypt

from flask import render_template, request, redirect, url_for, session, Blueprint
from sqlalchemy import select

from db import SessionLocal

from models.user import User

auth = Blueprint('auth', __name__)

@auth.route("/registration", methods=['GET', 'POST'])
def registration():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('home'))
        return render_template('auth/registration.html')

    db = SessionLocal()

    data = request.form

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if email == "":
        db.close()
        return "Email cannot be empty", 400

    if password == "":
        db.close()
        return "Password cannot be empty", 400

    user_by_username = (db.execute(select(User).where(User.username == username))).scalar()
    if user_by_username is not None:
        db.close()
        return "Username already exists"

    user_by_email = (db.execute(select(User).where(User.email == email))).scalar()
    if user_by_email is not None:
        db.close()
        return "Email already exists"

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user = User(username=username, email=email, password=hashed_password.decode('utf-8'))

    db.add(new_user)
    db.commit()
    db.close()

    return redirect(url_for('home'))

@auth.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if "user_id" in session:
            return redirect(url_for('home'))
        return render_template('auth/login.html')

    db = SessionLocal()

    data = request.form

    username_or_email = data.get('usernameOrEmail')
    password = data.get('password')

    if username_or_email == "":
        db.close()
        return "Email cannot be empty", 400

    if password == "":
        db.close()
        return "Password cannot be empty", 400

    if '@' in username_or_email:
        user = (db.execute(select(User).where(User.email == username_or_email))).scalar()
    else:
        user = (db.execute(select(User).where(User.username == username_or_email))).scalar()

    if user is None:
        db.close()
        return "User does not exist", 400

    check_password = bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8'))

    if not check_password:
        db.close()
        return "Invalid password", 400

    db.close()

    session['user_id'] = user.id
    session['role'] = user.role.value

    return redirect(url_for('home'))

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))
