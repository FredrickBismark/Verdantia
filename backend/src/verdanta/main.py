from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from verdanta.core.config import settings
from verdanta.core.database import init_db
from verdanta.routes import gardens, plants, plantings, calendar, weather, sensors, photos, harvest, soil, advisor, app_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield


app = FastAPI(
    title="Verdanta",
    description="Garden management with LLM-curated plant intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(gardens.router, prefix="/api/v1", tags=["gardens"])
app.include_router(plants.router, prefix="/api/v1", tags=["plants"])
app.include_router(plantings.router, prefix="/api/v1", tags=["plantings"])
app.include_router(calendar.router, prefix="/api/v1", tags=["calendar"])
app.include_router(weather.router, prefix="/api/v1", tags=["weather"])
app.include_router(sensors.router, prefix="/api/v1", tags=["sensors"])
app.include_router(photos.router, prefix="/api/v1", tags=["photos"])
app.include_router(harvest.router, prefix="/api/v1", tags=["harvest"])
app.include_router(soil.router, prefix="/api/v1", tags=["soil"])
app.include_router(advisor.router, prefix="/api/v1", tags=["advisor"])
app.include_router(app_settings.router, prefix="/api/v1", tags=["settings"])


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
