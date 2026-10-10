from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///greendash.db"
    DB_PATH: str = "greendash.db"
    ENV: str = "demo"
    DEMO_MODE: str = "cached"
    demo_mode: str = "cached"
    jwt_secret: str = "DEFAULT_SECRET_DO_NOT_USE_IN_PROD"
    llm_api_key: str | None = None
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
