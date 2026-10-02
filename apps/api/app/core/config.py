from functools import lru_cache
from typing import cast

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "nomos-api"
    app_env: str = "development"
    database_url: str
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return cast(Settings, Settings())  # type: ignore[call-arg]
