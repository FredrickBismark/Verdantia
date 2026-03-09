from pydantic import BaseModel


class SettingResponse(BaseModel):
    key: str
    value: str


class SettingUpdate(BaseModel):
    value: str


class LLMTestRequest(BaseModel):
    provider: str
    model: str
    api_key: str | None = None
    base_url: str | None = None
