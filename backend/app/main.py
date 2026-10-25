from fastapi import FastAPI

from app.api import (
    datasets_router,
    predictions_router
)

from app.core.database import create_tables


app = FastAPI()


# Create all database tables
create_tables()


app.include_router(
    datasets_router,
    prefix="/api/v1"
)


app.include_router(
    predictions_router,
    prefix="/api/v1"
)