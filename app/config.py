from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    openai_vision_model: str = "gpt-4o-2024-08-06"
    openai_text_model: str = "gpt-4o-2024-08-06"
    database_url: str = "sqlite:///./data/seam.db"
    upload_dir: str = "./uploads"
    secret_key: str = "change-me"


settings = Settings()
