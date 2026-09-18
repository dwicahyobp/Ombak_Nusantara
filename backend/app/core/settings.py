from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "fast_api_ombak_nusantara"
    db_url: str = "sqlite:///./dev.db"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str
    tavily_api_key: str

    model_config = SettingsConfigDict(extra="ignore", env_file=".env")

settings = Settings()