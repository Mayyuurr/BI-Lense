import importlib
import pkgutil

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import app.models


DATABASE_URL = "postgresql://postgres:root@localhost:5432/BI-Lens"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def create_tables():

    # Automatically import every model inside app.models
    for module in pkgutil.iter_modules(app.models.__path__):
        importlib.import_module(
            f"app.models.{module.name}"
        )

    # Create all registered models
    Base.metadata.create_all(bind=engine)