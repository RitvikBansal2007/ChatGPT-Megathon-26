from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///greendash.db"
    ENV: str = "demo"
    DEMO_MODE: str = "cached"
    demo_mode: str = "cached"
    jwt_secret: str = "DEFAULT_SECRET_DO_NOT_USE_IN_PROD"
    llm_api_key: str | None = None
    # File path used by greendash.db.{repo,migrate,audit}. Empty means: derive it from
    # database_url (sqlite:///<path>). Override with the DB_PATH environment variable.
    DB_PATH: str = ""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def _derive_db_path(self):
        if not self.DB_PATH:
            self.DB_PATH = self.database_url.removeprefix("sqlite:///")
        return self


settings = Settings()
