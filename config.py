from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    openai_key: str
    download_dir: str
    archive_dir: str
    model_code: str = "gpt-5-nano-2025-08-07"

settings = Settings()