from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    message: str
    planting_id: int | None = None


class ChatResponse(BaseModel):
    response: str
    model_used: str
    provider: str
    context_summary: str
    interaction_id: int


class AlertResponse(BaseModel):
    priority: str
    category: str
    description: str
    timestamp: datetime


class InteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    garden_id: int | None
    planting_id: int | None
    interaction_type: str
    user_prompt: str
    system_context: str
    response: str
    model_used: str
    provider: str
    timestamp: datetime
    feedback: str | None
    tokens_used: int | None


class FeedbackRequest(BaseModel):
    feedback: str  # helpful, not_helpful, incorrect
