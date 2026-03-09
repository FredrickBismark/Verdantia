from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    planting_id: int | None
    garden_id: int
    file_path: str
    thumbnail_path: str | None
    caption: str | None
    taken_at: datetime
    tags: list[str] | None
    created_at: datetime
