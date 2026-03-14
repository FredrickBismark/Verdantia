import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from verdanta.core.config import settings
from verdanta.core.database import init_db
from verdanta.routes import (
    advisor,
    alerts,
    app_settings,
    calendar,
    gardens,
    harvest,
    journal,
    photos,
    plantings,
    plants,
    sensors,
    soil,
    weather,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    import asyncio

    from verdanta.services.alert_service import check_all_gardens_alerts
    from verdanta.services.sensor_service import start_mqtt_listener
    from verdanta.services.weather_service import close_http_client, sync_all_gardens

    await init_db()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        sync_all_gardens,
        "interval",
        hours=settings.weather_sync_interval_hours,
        id="weather_sync",
        replace_existing=True,
        misfire_grace_time=300,  # allow up to 5-min delay before skipping
    )
    scheduler.add_job(
        check_all_gardens_alerts,
        "interval",
        minutes=30,
        id="alert_check",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    logger.info(
        "Schedulers started — weather sync: %dh, alert check: 30m",
        settings.weather_sync_interval_hours,
    )

    # Start MQTT sensor listener as a background task
    mqtt_task = None
    if settings.mqtt_enabled:
        mqtt_task = asyncio.create_task(start_mqtt_listener())
        logger.info("MQTT sensor listener task started")

    yield

    if mqtt_task and not mqtt_task.done():
        mqtt_task.cancel()
    scheduler.shutdown(wait=False)
    await close_http_client()


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
app.include_router(journal.router, prefix="/api/v1", tags=["journal"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(advisor.router, prefix="/api/v1", tags=["advisor"])
app.include_router(app_settings.router, prefix="/api/v1", tags=["settings"])


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
