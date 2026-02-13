import enum

from sqlalchemy import Column, Integer, String, Enum
from sqlalchemy.orm import relationship

from db import Base

class UserRole(enum.Enum):
    user = "user"
    provider = "provider"
    admin = "admin"

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)

    username = Column(String(50), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)

    client_reservations = relationship("Reservation",
                                      foreign_keys="Reservation.client_id",
                                      back_populates="client")

    provider_reservations = relationship("Reservation",
                                        foreign_keys="Reservation.provider_id",
                                        back_populates="provider")

    restaurants = relationship("Restaurant", back_populates="owner", cascade="all, delete-orphan")

    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
