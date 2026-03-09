# Verdanta — Claude Code Guidelines

## Project Overview

Verdanta is a local-first, single-user garden management application with LLM-curated plant intelligence. It runs entirely locally with optional cloud API enhancements (weather, LLM). The LLM is the intelligence layer — not a chatbot — curating plant data, generating schedules, and providing proactive advice.

## Core Principles

- **Local-first**: No cloud dependency required. Cloud APIs are optional enhancers with offline fallbacks.
- **Data transparency**: Users can always see what sources informed a recommendation.
- **No paywall, no subscription, no telemetry, no cloud accounts required.**
- **Keep it simple**: Avoid over-engineering. This is a single-user app on local hardware.

## Tech Stack

### Backend (Python 3.11+)
- **Framework**: FastAPI (async)
- **Package manager**: uv (replaces pip+venv+poetry)
- **ORM**: SQLAlchemy 2.0+ (async, mapped_column style)
- **Database**: SQLite (single file)
- **Migrations**: Alembic
- **HTTP client**: httpx (async, all external API calls)
- **Task scheduling**: APScheduler (background jobs)
- **MQTT**: aiomqtt (IoT sensor ingestion)

### Frontend (TypeScript)
- **Framework**: React 18 + TypeScript
- **Build**: Vite
- **CSS**: TailwindCSS v4
- **State management**: Zustand
- **Data fetching**: TanStack React Query v5
- **Calendar**: FullCalendar React
- **Charts**: Recharts
- **Icons**: Lucide React
- **Dates**: date-fns
- **Markdown**: react-markdown

### Infrastructure
- **Containerization**: Docker Compose (optional, not required for dev)

## Directory Structure

```
verdanta/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── database.py          # SQLAlchemy engine, session factory
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── plant.py
│   │   │   ├── garden.py
│   │   │   ├── task.py
│   │   │   └── sensor.py
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── plant.py
│   │   │   ├── garden.py
│   │   │   ├── task.py
│   │   │   └── sensor.py
│   │   ├── api/                 # FastAPI routers
│   │   │   ├── __init__.py
│   │   │   ├── plants.py
│   │   │   ├── gardens.py
│   │   │   ├── tasks.py
│   │   │   └── sensors.py
│   │   ├── services/            # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── plant_service.py
│   │   │   ├── garden_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── weather_service.py
│   │   │   └── scheduler_service.py
│   │   └── utils/               # Shared utilities
│   │       ├── __init__.py
│   │       └── constants.py
│   ├── alembic/                 # Database migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Route-level page components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── stores/              # Zustand stores
│   │   ├── api/                 # API client and query hooks
│   │   ├── types/               # TypeScript type definitions
│   │   └── utils/               # Frontend utilities
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
├── docker-compose.yml           # Optional containerization
├── CLAUDE.md
├── Verdanta.txt
└── LICENSE
```

## Code Conventions

### Python (Backend)
- Use `async def` for all route handlers and service methods that do I/O
- Use SQLAlchemy 2.0 `mapped_column` style, not legacy Column()
- Type-annotate all function signatures
- Use pydantic models for all API request/response schemas
- Import ordering: stdlib, third-party, local (enforced by ruff)
- Use `snake_case` for functions, variables, modules; `PascalCase` for classes

### TypeScript (Frontend)
- Functional components only, no class components
- Use named exports, not default exports
- Co-locate component-specific types in the component file
- Shared types go in `src/types/`
- Use TanStack Query for all server state; Zustand only for client-only UI state

### Database
- All tables use `id` as integer primary key with autoincrement
- Use `created_at` and `updated_at` timestamps on all tables
- Foreign keys use `<table>_id` naming convention

## Commands

### Backend
```bash
cd backend
uv sync                    # Install dependencies
uv run fastapi dev app/main.py  # Run dev server (auto-reload)
uv run alembic upgrade head     # Run migrations
uv run pytest                   # Run tests
uv run ruff check .             # Lint
uv run ruff format .            # Format
```

### Frontend
```bash
cd frontend
npm install                # Install dependencies
npm run dev                # Run dev server
npm run build              # Production build
npm run lint               # Lint
npm run type-check         # TypeScript check
```

## Development Notes
- SQLite database file lives at `backend/verdanta.db`
- Backend runs on port 8000, frontend on port 5173
- API docs available at http://localhost:8000/docs when backend is running
- Environment config via `.env` file in `backend/` directory (not committed)
