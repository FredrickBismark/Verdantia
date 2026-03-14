# Verdanta — Development Guide

## Project Overview

Verdanta is a local-first garden management application with LLM-curated plant intelligence.
Monorepo: Python 3.11+ backend (FastAPI) + TypeScript frontend (React 18 + Vite).

## Repository Layout

```
backend/                 # Python backend (FastAPI)
  src/verdanta/          # Main package
    models/              # SQLAlchemy 2.0 ORM models
    schemas/             # Pydantic request/response schemas
    routes/              # FastAPI routers (one per domain)
    services/            # Business logic layer
    core/                # Config, database, dependencies
  tests/                 # pytest tests (mirrors src structure)
  alembic/               # Database migrations
  pyproject.toml         # uv-managed dependencies
frontend/                # React + TypeScript frontend
  src/
    components/          # Reusable UI components (8 components)
    pages/               # Page-level components (9 pages)
    hooks/               # Custom React hooks (gardens, plants, plantings)
    stores/              # Zustand state stores (gardenStore)
    api/                 # API client functions (13 modules)
    types/               # TypeScript type definitions
  package.json
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2.0 (async, mapped_column), SQLite, Alembic, httpx, APScheduler, aiomqtt, Pillow
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS v4, Zustand, TanStack React Query v5, FullCalendar, Recharts, React Router v6, Lucide React icons
- **Package management**: `uv` (backend), `npm` (frontend)

## Commands

### Backend
```bash
cd backend
uv sync                          # Install dependencies
uv run alembic upgrade head      # Run migrations
uv run pytest                    # Run all tests (100 tests)
uv run pytest tests/test_foo.py  # Run single test file
uv run pytest -x                 # Stop on first failure
uv run uvicorn verdanta.main:app --reload  # Dev server (port 8000)
uv run ruff check src/           # Lint
uv run ruff format src/          # Format
```

### Frontend
```bash
cd frontend
npm install                      # Install dependencies
npm run dev                      # Dev server (port 5173)
npm run build                    # Production build
npm run lint                     # ESLint
npm run type-check               # TypeScript type checking
```

## Code Conventions

### Python (Backend)
- **Python 3.11+** — use `X | None` union syntax, not `Optional[X]`
- **SQLAlchemy 2.0** — `DeclarativeBase`, `Mapped`, `mapped_column` style exclusively
- **Async everywhere** — all database operations, HTTP calls, and service methods are async
- **Pydantic v2** — `model_config = ConfigDict(from_attributes=True)` for ORM integration
- **Type hints** — all function signatures must have full type annotations
- **Imports** — use absolute imports from `verdanta.` package
- **Naming** — snake_case for everything except class names (PascalCase)
- **Tests** — pytest with `pytest-asyncio`, fixtures in `conftest.py`, use factory functions not fixtures for model instances
- **Error handling** — raise `HTTPException` in routes only; services return values or raise domain exceptions
- **Timestamps** — always UTC, use `datetime` from stdlib

### TypeScript (Frontend)
- **Strict TypeScript** — no `any` types, no `@ts-ignore`
- **Functional components** — arrow functions with explicit return types
- **State** — Zustand stores for global state, React Query for server state
- **API calls** — all go through `src/api/` client functions, never raw fetch in components
- **Naming** — PascalCase components, camelCase functions/variables, UPPER_SNAKE_CASE constants
- **File naming** — PascalCase for components (`PlantCard.tsx`), camelCase for utilities (`dateUtils.ts`)

### API Design
- All routes prefixed with `/api/v1/`
- RESTful resource naming (plural nouns)
- Consistent response shapes: single items `{ data: T }`, lists `{ data: T[], count: number }`
- Pagination via `?skip=0&limit=20` query params
- Filter parameters as query strings, not request bodies

### Database
- SQLite single-file database at `{data_dir}/verdanta.db`
- All migrations via Alembic — never modify schema outside of migrations
- JSON columns for flexible structured data (companion_plants, custom_fields, raw_data)
- Cascade deletes configured in relationships, not at DB level
- Performance indexes on frequently queried columns (weather_records, calendar_events, sensor_readings, llm_interactions, plantings)

### LLM Integration
- All LLM calls go through `LLMService` — never call provider APIs directly
- Provider abstraction: Ollama (default), Anthropic, OpenAI, Venice, OpenRouter, Custom
- Every LLM interaction is logged to `llm_interactions` table for transparency
- Context assembly via `ContextProvider` protocol (garden, planting, weather, species providers)
- Task-specific model overrides via `AppSettings`
- Streaming support via SSE for advisor chat

## Architecture Principles

1. **Local-first** — everything works offline; cloud APIs are optional enhancers
2. **Transparency** — users see exactly what data the LLM receives and what sources informed recommendations
3. **Service layer pattern** — routes are thin (validation + delegation), services contain business logic
4. **No magic** — explicit dependency injection via FastAPI `Depends()`, no global mutable state
5. **Graceful degradation** — if LLM is unavailable, app functions normally without AI features; if weather API is down, use cached data

## Implemented Features

### Backend (14 route files, ~50 endpoints, 100 tests)

**Core CRUD** — Gardens, Plant Species, Plantings, Settings (fully tested)

**Intelligence Layer**
- Multi-provider LLM service (Ollama, Anthropic, OpenAI, Venice, OpenRouter, Custom)
- Plant curation pipeline: OpenFarm data fetch → LLM dossier generation (7 sections)
- Knowledge entries system for cross-feature learning

**Calendar & Weather**
- Auto-schedule generation from plant dossier data + frost dates
- Open-Meteo weather integration (current, forecast, historical)
- GDD calculations, frost date estimation
- Weather-responsive event rescheduling
- Weather alert generation (frost, extreme temps, wind)

**Advisor & Alerts**
- LLM-powered garden advisor chat with streaming (SSE)
- Context assembly from garden, plantings, weather, species data
- Proactive alert system (frost, extreme weather, pest/disease)
- Alert lifecycle: create → acknowledge → dismiss

**Data Capture**
- Photo upload with thumbnail generation (Pillow) and EXIF parsing
- Harvest logging with per-planting stats and garden-wide summaries
- Garden journal/observations with category, tags, mood tracking
- Soil test recording

**IoT & Sensors**
- MQTT sensor integration with auto-discovery and background listener (aiomqtt)
- Sensor list, status, and health tracking endpoints
- Manual sensor reading entry

**Photo Diagnosis**
- LLM-powered photo diagnosis via vision models
- Context-aware analysis using planting and garden data

### Frontend (10 pages, 9 components, 14 API modules)

**Pages**: Dashboard, Gardens, Plants (with dossier tabs), Calendar, Weather, Journal, Sensors, Advisor (streaming chat), Alerts, Settings

**Components**: AppShell (nav/layout), AlertPanel, PhotoUpload, PhotoGallery, PhotoDiagnosis, HarvestLogger, HarvestChart, JournalEntryForm, JournalFeed

**State**: Zustand gardenStore (persisted selection), TanStack React Query v5 (server state, 30s stale time)

## Implementation Phases

### Phase 1 — Foundation ✅
Core models, database setup, Garden CRUD, Plant Species CRUD, basic Planting management, Settings API, skeleton frontend with navigation and pages.

### Phase 2 — Intelligence Layer ✅
LLM service with multi-provider support, plant curation pipeline, dossier generation, OpenFarm integration, knowledge entries.

### Phase 3 — Calendar & Weather ✅
Calendar service with auto-scheduling, weather service with Open-Meteo, weather-responsive rescheduling, GDD/frost calculations, weather alerts.

### Phase 4 — Advisor & IoT ✅
- ✅ Garden advisor chat with context assembly and streaming
- ✅ Proactive alerts (frost, extreme weather, pest/disease)
- ✅ Interaction history and user feedback
- ✅ Photo diagnosis via LLM (vision model analysis with context)
- ✅ MQTT sensor integration (aiomqtt listener, auto-discovery, manual entry)
- ✅ Sensor dashboard (list, status, readings, manual entry form)

### Phase 5 — Polish ⚠️ Partially Complete
- ✅ Photo management (upload, thumbnails, gallery)
- ✅ Harvest logging with stats and charts
- ✅ Garden journal/observations
- ✅ Dashboard with weather, tasks, journal, season progress
- ❌ Season comparisons / year-over-year analytics
- ❌ Data import/export
- ❌ Docker Compose setup

## Next Steps (Recommended Development Path)

1. **Complete Phase 4 IoT** — Implement MQTT sensor service, sensor list/status endpoints, sensor dashboard page
2. **Photo diagnosis** — Wire up LLM image analysis for plant disease/pest identification
3. **Season comparisons** — Add year-over-year harvest and growth analytics with Recharts
4. **Import/Export** — Garden data export (JSON/CSV) and import for backup/migration
5. **Docker Compose** — Production deployment with backend, frontend, and optional Mosquitto broker
6. **Frontend polish** — Add missing React Query hooks for alerts, journal, harvest, weather, calendar; add loading/error states across all pages
