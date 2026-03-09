from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import gardens, plants, sensors, tasks
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plants.router, prefix="/api/plants", tags=["plants"])
app.include_router(gardens.router, prefix="/api/gardens", tags=["gardens"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(sensors.router, prefix="/api/sensors", tags=["sensors"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name}
