from sqlalchemy import create_engine, text
from .config import get_settings
engine = create_engine(get_settings().database_url, pool_pre_ping=True)
def database_ready() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return True
    except Exception:
        return False
