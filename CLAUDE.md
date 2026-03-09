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
    components/          # Reusable UI components
    pages/               # Page-level components (one per nav item)
    hooks/               # Custom React hooks
    stores/              # Zustand state stores
    api/                 # API client functions (TanStack Query)
    types/               # TypeScript type definitions
    utils/               # Utility functions
  package.json
```

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy 2.0 (async, mapped_column), SQLite, Alembic, httpx, APScheduler, aiomqtt
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS v4, Zustand, TanStack React Query v5, FullCalendar, Recharts
- **Package management**: `uv` (backend), `npm` (frontend)

## Commands

### Backend
```bash
cd backend
uv sync                          # Install dependencies
uv run alembic upgrade head      # Run migrations
uv run pytest                    # Run all tests
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

### LLM Integration
- All LLM calls go through `LLMService` — never call provider APIs directly
- Provider abstraction: Ollama (default), Anthropic, OpenAI, Venice, OpenRouter, Custom
- Every LLM interaction is logged to `llm_interactions` table for transparency
- Context assembly happens in service layer, not in routes
- Task-specific model overrides via `AppSettings`

## Architecture Principles

1. **Local-first** — everything works offline; cloud APIs are optional enhancers
2. **Transparency** — users see exactly what data the LLM receives and what sources informed recommendations
3. **Service layer pattern** — routes are thin (validation + delegation), services contain business logic
4. **No magic** — explicit dependency injection via FastAPI `Depends()`, no global mutable state
5. **Graceful degradation** — if LLM is unavailable, app functions normally without AI features; if weather API is down, use cached data

## Implementation Phases

### Phase 1 — Foundation
Core models, database setup, Garden CRUD, Plant Species CRUD, basic Planting management, Settings API, skeleton frontend with navigation and pages.

### Phase 2 — Intelligence Layer
LLM service with multi-provider support, plant curation pipeline, dossier generation, OpenFarm integration.

### Phase 3 — Calendar & Weather
Calendar service with auto-scheduling, weather service with Open-Meteo, weather-responsive rescheduling, GDD/frost calculations.

### Phase 4 — Advisor & IoT
Garden advisor chat with context assembly, proactive alerts, photo diagnosis, MQTT sensor integration, sensor dashboard.

### Phase 5 — Polish
Photo management, harvest logging, data visualization, season comparisons, import/export, Docker Compose setup.
