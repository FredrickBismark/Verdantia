from app.config import settings


class WeatherService:
    """Fetches weather data for garden locations. Uses Open-Meteo by default (no API key needed)."""

    def __init__(self):
        self.api_url = settings.weather_api_url
        self.api_key = settings.weather_api_key
