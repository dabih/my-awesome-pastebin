from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import DATABASE_URL


engine = create_engine(DATABASE_URL)
SESSION_LOCAL = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SESSION_LOCAL()
    try:
        yield db
    finally:
        db.close()
