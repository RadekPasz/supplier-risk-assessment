from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/supplier_risk"
    openai_api_key: str = ""
    upload_dir: str = "/data/uploads"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"


settings = Settings()
