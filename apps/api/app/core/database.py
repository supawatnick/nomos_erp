from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings

def database_ready() -> bool:
    try:
        with create_engine(get_settings().database_url, pool_pre_ping=True).connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
