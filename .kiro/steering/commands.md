---
inclusion: always
---

# Quick Command Reference

## Docker (Full Stack)

```bash
# Start all services
docker compose up -d

# Start with hot reloading
docker compose watch

# Stop all services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Rebuild containers
docker compose build --no-cache
```

## Backend (Python/FastAPI)

```bash
# Testing (run inside Docker)
docker compose exec backend bash scripts/tests-start.sh                    # Run all tests with coverage
docker compose exec backend pytest tests/ -v                               # Run tests verbose
docker compose exec backend pytest tests/api/routes/test_accounts.py       # Run specific test file
docker compose exec backend pytest tests/api/routes/ -v                    # Run all route tests
docker compose exec backend pytest tests/crud/ -v                          # Run all CRUD tests
docker compose exec backend pytest -k "test_name"                          # Run tests matching pattern
docker compose exec backend pytest tests/api/routes/test_accounts.py::test_create_account  # Run single test

# Code Quality (local, requires venv)
cd backend
uv sync                                    # Install/sync dependencies
source .venv/bin/activate                  # Activate venv
bash ./scripts/format.sh                   # Format code (ruff)
bash ./scripts/lint.sh                     # Lint + type check (ruff + mypy)

# Database Migrations (inside Docker)
docker compose exec backend alembic revision --autogenerate -m "description"
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1
docker compose exec backend alembic history
```

## Frontend (React/TypeScript)

```bash
cd frontend

# Dependencies
npm install                    # Install dependencies

# Development
npm run dev                    # Start dev server (port 5173)
npm run build                  # Production build
npm run preview                # Preview production build

# Code Quality
npm run lint                   # Lint + format (biome)

# API Client
npm run generate-client        # Regenerate from OpenAPI spec

# E2E Tests (requires running backend)
npx playwright test                           # Run all tests
npx playwright test tests/accounts.spec.ts   # Run specific test
npx playwright test --ui                      # Interactive UI mode
npx playwright test --debug                   # Debug mode
```

## Database Access

```bash
# Via Adminer (web UI)
# URL: http://localhost:8080 (when using docker compose)

# Direct psql access
docker compose exec db psql -U postgres -d app
```

## Common Workflows

```bash
# After backend model changes
docker compose exec backend alembic revision --autogenerate -m "description"
docker compose exec backend alembic upgrade head
cd frontend && npm run generate-client

# Full test run
docker compose up -d --wait backend
docker compose exec backend bash scripts/tests-start.sh
cd frontend && npx playwright test
```
