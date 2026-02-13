from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine(
    "postgresql+psycopg2://postgres:password@localhost:5432/reservations_db"
)

# postgresql+psycopg2://postgres:password@localhost:5432/reservations_db
# sqlite:///:memory:

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass
