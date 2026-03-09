from app.config import settings


class LLMService:
    """Handles interactions with the LLM for plant intelligence and recommendations."""

    def __init__(self):
        self.api_key = settings.llm_api_key
        self.api_url = settings.llm_api_url
        self.model = settings.llm_model
