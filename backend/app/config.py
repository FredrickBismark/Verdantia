from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Verdanta"
    debug: bool = False

    # Database
    database_url: str = f"sqlite+aiosqlite:///{Path(__file__).resolve().parent.parent / 'verdanta.db'}"

    # Weather API (optional)
    weather_api_key: str | None = None
    weather_api_url: str = "https://api.open-meteo.com/v1/forecast"

    # LLM (optional)
    llm_api_key: str | None = None
    llm_api_url: str | None = None
    llm_model: str = "claude-sonnet-4-20250514"

    # MQTT (optional)
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
