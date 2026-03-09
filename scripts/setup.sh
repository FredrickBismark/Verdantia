#!/bin/bash
# One-command setup for Verdanta

set -e

echo "Setting up Verdanta..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3.11+ required"; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js 18+ required"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }

# Backend setup
cd backend
uv sync
uv run alembic upgrade head
cd ..

# Frontend setup
cd frontend
npm install
cd ..

# Create data directories
mkdir -p data/photos

# Copy env file if not exists
cp -n .env.example .env 2>/dev/null || true

echo ""
echo "Setup complete!"
echo ""
echo "To start the backend:  cd backend && uv run uvicorn verdanta.main:app --reload"
echo "To start the frontend: cd frontend && npm run dev"
echo ""
echo "Optional: Install Ollama for local LLM support: https://ollama.ai"
