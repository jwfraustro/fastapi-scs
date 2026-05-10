"""This module contains dependencies for connecting the application to the database."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()