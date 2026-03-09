from sqlalchemy.ext.asyncio import AsyncSession


class GardenService:
    def __init__(self, db: AsyncSession):
        self.db = db
