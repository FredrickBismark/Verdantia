from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="VERDANTA_")

    # Database
    database_url: str = "sqlite+aiosqlite:///data/verdanta.db"

    # Data storage
    data_dir: str = "data"
    photo_dir: str = "data/photos"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Weather
    weather_sync_interval_hours: int = 6

    # MQTT
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_topic_prefix: str = "verdanta/sensors"
    mqtt_enabled: bool = False

    # LLM defaults
    llm_default_provider: str = "ollama"
    llm_default_model: str = "llama3:8b"
    ollama_base_url: str = "http://localhost:11434"

    # API keys (optional, can also be set via UI)
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    venice_api_key: str | None = None
    openrouter_api_key: str | None = None

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
