# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a full-stack web application with:
- **Backend**: FastAPI + SQLModel (ORM) + PostgreSQL
- **Frontend**: React + TypeScript + Vite + TanStack Router/Query + Tailwind CSS
- **Infrastructure**: Docker Compose for dev/prod, Traefik for reverse proxy

### Backend Architecture (backend/app/)

- **main.py**: FastAPI app initialization, middleware setup (CORS, Sentry)
- **api/main.py**: Router configuration that includes all route modules
- **api/routes/**: Endpoint modules (login, users, items, utils, private)
- **models.py**: SQLModel ORM definitions for database schema
- **crud.py**: Database CRUD operations
- **core/config.py**: Pydantic Settings for environment variables
- **core/db.py**: Database session management, SQLAlchemy engine
- **core/security.py**: JWT token utilities and password hashing
- **alembic/**: Database migrations using Alembic
- **email-templates/**: Email templates in MJML format (src/) and compiled HTML (build/)

### Frontend Architecture (frontend/src/)

- **client/**: Auto-generated OpenAPI client from backend schema
- **components/**: Reusable React components (form fields, UI elements)
- **routes/**: TanStack Router route definitions (pages/screens)
- **hooks/**: Custom React hooks

### API Versioning

The API is versioned under `/api/v1/` prefix (see `API_V1_STR` in config). The OpenAPI schema is available at `/api/v1/openapi.json`.

## Common Development Commands

### Docker Compose (Recommended)

Start the full development stack with live reloading:
```bash
docker compose watch
```

Run tests with Docker (backend container):
```bash
docker compose exec backend bash scripts/tests-start.sh
```

Enter backend container for manual operations:
```bash
docker compose exec backend bash
```

### Backend (Python/FastAPI)

From `backend/` directory with `uv`:

Install dependencies:
```bash
uv sync
```

Activate virtual environment:
```bash
source .venv/bin/activate
```

Run local dev server:
```bash
fastapi dev app/main.py
```

Run tests locally:
```bash
bash scripts/test.sh
```

Run a single test:
```bash
pytest tests/api/test_login.py::test_login_success
```

Check code with ruff (linter):
```bash
uv run ruff check --fix
```

Format code with ruff:
```bash
uv run ruff format
```

Create database migration:
```bash
alembic revision --autogenerate -m "Description of change"
```

Apply migrations:
```bash
alembic upgrade head
```

### Frontend (Node/React)

From `frontend/` directory:

Install dependencies:
```bash
npm install
```

Run dev server (live reload at localhost:5173):
```bash
npm run dev
```

Build for production:
```bash
npm run build
```

Lint/format with Biome:
```bash
npm run lint
```

Generate OpenAPI client from backend schema:
```bash
npm run generate-client
```

Run end-to-end tests (requires backend running):
```bash
npx playwright test
```

Run tests in UI mode:
```bash
npx playwright test --ui
```

### Code Linting (Pre-commit)

The project uses `prek` (modern replacement for pre-commit). To install hooks that run before each commit:

From `backend/` directory:
```bash
uv run prek install -f
```

To manually run all linting hooks:
```bash
uv run prek run --all-files
```

This runs: TOML/YAML checks, ruff (check + format), and Biome for frontend.

## Development Workflow

### Local Stack

Start with `docker compose watch` - this mounts source code as volumes and auto-reloads on changes.

**Available URLs:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- API Docs (ReDoc): http://localhost:8000/redoc
- Database Admin (Adminer): http://localhost:8080
- Traefik UI: http://localhost:8090
- Email Viewer (Mailcatcher): http://localhost:1080

### Alternative Local Development

To iterate faster on individual services, you can stop a service in Docker and run it locally on the same port:

Stop backend: `docker compose stop backend`
Then run: `cd backend && fastapi dev app/main.py`

Stop frontend: `docker compose stop frontend`
Then run: `cd frontend && npm run dev`

### Database Migrations

After modifying SQLModel definitions in `backend/app/models.py`:

1. Enter backend container: `docker compose exec backend bash`
2. Create migration: `alembic revision --autogenerate -m "Describe change"`
3. Review generated migration in `backend/app/alembic/versions/`
4. Apply: `alembic upgrade head`
5. Commit the migration file

Never skip migrations in production - they track schema evolution.

### Updating Frontend Client

When backend API endpoints change:

1. Ensure backend is running
2. From project root: `./scripts/generate-client.sh`
3. This downloads the OpenAPI schema and generates TypeScript client in `frontend/src/client/`
4. Commit the generated client code

## Environment Configuration

Configuration is managed with Pydantic Settings in `backend/app/core/config.py`. The `.env` file contains environment variables.

Key variables (never commit actual values):
- `SECRET_KEY`: For JWT signing
- `FIRST_SUPERUSER`: Initial admin email
- `FIRST_SUPERUSER_PASSWORD`: Initial admin password
- `POSTGRES_PASSWORD`: Database password
- `DOMAIN`: For deployment routing (localhost for dev, domain.com for production)

Generate secure random values:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Code Style and Linting

**Backend (Python):**
- Ruff for linting and formatting
- MyPy for strict type checking (enabled in pyproject.toml)
- Pre-commit hooks run automatically; code must pass before commit

**Frontend (TypeScript/React):**
- Biome for linting and formatting
- TypeScript strict mode configured
- Pre-commit hooks check frontend code

All checks must pass before commit.

## Testing

**Backend:**
- Pytest for unit/integration tests in `backend/tests/`
- Run: `bash scripts/test.sh`
- Run single test: `pytest tests/api/test_login.py::test_function_name`
- Coverage report: `htmlcov/index.html` (generated after test run)

**Frontend:**
- Playwright for end-to-end tests in `frontend/e2e/`
- Run: `npx playwright test`
- UI mode: `npx playwright test --ui`
- Requires backend running; tests are run via Docker if using `docker compose`

## Deployment

See `deployment.md` for production deployment instructions.

- Uses Docker Compose with Traefik as reverse proxy
- Handles HTTPS certificate automation
- Scales with multiple service instances

## Project Status

This is a reference template maintained by the FastAPI team. Check `release-notes.md` for recent changes.