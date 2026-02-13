import os
import bcrypt

from sqlalchemy import select

from db import SessionLocal
from models.user import User, UserRole

def create_admin_if_not_exist():
    db = SessionLocal()

    admin = db.execute(select(User).where(User.role == UserRole.admin)).scalars().first()

    if admin:
        db.close()
        return

    password = os.getenv('ADMIN_PASSWORD')
    hashed_password = bcrypt.hashpw(password.encode('UTF-8'), bcrypt.gensalt())

    admin = User(username=os.getenv('ADMIN_USERNAME'),
                 password=hashed_password.decode('UTF-8'),
                 email=os.getenv('ADMIN_EMAIL'),
                 role=UserRole.admin)

    db.add(admin)
    db.commit()
    db.close()
