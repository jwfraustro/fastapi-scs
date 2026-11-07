"""This module contains dependencies for connecting the application to the database."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_scs.settings import get_settings

engine = create_engine(get_settings().DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """Yield a database session for the duration of a request.

    FastAPI handles generator dependencies itself, so this must not be wrapped in @contextmanager.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
