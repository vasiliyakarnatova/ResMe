import enum

from sqlalchemy import (Column, Integer, DateTime, Enum,
                        ForeignKey, Text, Time, String, CheckConstraint)
from sqlalchemy.orm import relationship

from db import Base

class Restaurant(Base):
    __tablename__ = 'restaurant'

    id = Column(Integer, primary_key=True)

    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)

    owner_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    owner = relationship("User", back_populates="restaurants")

    image_url = Column(String(255), nullable=True)

    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")

    reservations = relationship("Reservation", back_populates="restaurant",
                                cascade="all, delete-orphan")

    tables = relationship("Table", back_populates="restaurant", cascade="all, delete-orphan")

    zones = relationship("Zone", back_populates="restaurant", cascade="all, delete-orphan")

class Table(Base):
    __tablename__ = 'table'
    id = Column(Integer, primary_key=True)

    name = Column(String(30), nullable=False)
    capacity = Column(Integer, nullable=False)

    zone_id = Column(Integer, ForeignKey('zone.id'), nullable=False)
    zone = relationship("Zone", back_populates="tables")

    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=False)
    restaurant = relationship("Restaurant", back_populates="tables")

    reservations = relationship("Reservation", back_populates="table")

class Zone(Base):
    __tablename__ = 'zone'
    id = Column(Integer, primary_key=True)

    name = Column(String(30), nullable=False)

    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=False)
    restaurant = relationship("Restaurant", back_populates="zones")

    tables = relationship("Table", back_populates="zone", cascade="all, delete-orphan")

class ReservationStatus(enum.Enum):
    pending = 'pending'
    accepted = 'accepted'
    canceled = 'canceled'
    completed = 'completed'

class Reservation(Base):
    __tablename__ = 'reservation'

    id = Column(Integer, primary_key=True)

    date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.pending, nullable=False)

    client_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    provider_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    client = relationship("User", foreign_keys=[client_id],
                          back_populates="client_reservations")
    provider = relationship("User", foreign_keys=[provider_id],
                            back_populates="provider_reservations")

    additional_notes = Column(Text, nullable=True)

    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=False)
    restaurant = relationship("Restaurant", back_populates="reservations")

    table_id = Column(Integer, ForeignKey('table.id'), nullable=False)
    table = relationship("Table", back_populates="reservations")

class Review(Base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user = relationship("User", back_populates="reviews")

    restaurant_id = Column(Integer, ForeignKey('restaurant.id'), nullable=False)
    restaurant = relationship("Restaurant", back_populates="reviews")

    rating = Column(Integer, nullable=False)
    __table_args__ = (CheckConstraint('rating >= 1 AND rating <= 5', name='rating_range'),)

    comment = Column(Text, nullable=True)
