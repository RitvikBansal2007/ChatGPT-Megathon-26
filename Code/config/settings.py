from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# The signing secret used when none is configured. Fine on a developer laptop,
# never acceptable anywhere else.
DEFAULT_JWT_SECRET = "DEFAULT_SECRET_DO_NOT_USE_IN_PROD"
_INSECURE_SECRETS = frozenset({
    DEFAULT_JWT_SECRET.lower(), "super_secret_key_for_hackathon_demo", "secret",
    "changeme", "jwt_secret", "password",
})
MIN_JWT_SECRET_CHARS = 32
# Only these environments may run with the placeholder secret. ANY other value
# (demo, staging, production, a typo, different case) is treated as deployed.
_LOCAL_ENVS = frozenset({"development", "dev", "test"})


class Settings(BaseSettings):
    database_url: str = "sqlite:///greendash.db"
    ENV: str = "development"
    DEMO_MODE: str = "cached"
    demo_mode: str = "cached"
    jwt_secret: str = DEFAULT_JWT_SECRET
    # GEMINI_API_KEY is what greendash.llm.client reads; LLM_API_KEY is accepted too.
    llm_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("GEMINI_API_KEY", "LLM_API_KEY"))
    # Field-encryption keys (security/crypto.py). Read through settings so a value in
    # .env works, not only one exported into the process environment.
    data_key: str = Field(default="", validation_alias=AliasChoices("DATA_KEY", "data_key"))
    data_key_old: str = Field(default="", validation_alias=AliasChoices("DATA_KEY_OLD", "data_key_old"))
    # File path used by greendash.db.{repo,migrate,audit}. Empty means: derive it from
    # database_url (sqlite:///<path>). Override with the DB_PATH environment variable.
    DB_PATH: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore",
                                      populate_by_name=True)

    @model_validator(mode="after")
    def _derive_db_path(self):
        if not self.DB_PATH:
            self.DB_PATH = self.database_url.removeprefix("sqlite:///")
        return self

    @model_validator(mode="after")
    def _validate_secrets(self):
        """Fail closed: a deployed environment must have a real signing secret.

        The check is an allow-list of local environments, not a match on the word
        "production", so an unset, misspelt or differently cased ENV cannot start
        with the placeholder secret.
        """
        env = (self.ENV or "").strip().lower()
        if env in _LOCAL_ENVS:
            return self
        secret = self.jwt_secret or ""
        if (not secret.strip() or secret.lower() in _INSECURE_SECRETS
                or len(secret) < MIN_JWT_SECRET_CHARS):
            raise ValueError(
                "Production cannot start with placeholder or insecure JWT secret "
                f"(ENV is not a local environment; JWT_SECRET must be >= {MIN_JWT_SECRET_CHARS} "
                "characters and not a placeholder)"
            )
        return self


settings = Settings()
