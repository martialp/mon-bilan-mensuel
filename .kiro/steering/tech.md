---
inclusion: always
---

# Technology Stack & Development Guidelines

## Core Technologies

### Backend (FastAPI + Python)
- **Framework**: FastAPI with Python 3.10+
- **Database**: PostgreSQL 17 with SQLModel ORM (combines SQLAlchemy + Pydantic)
- **Authentication**: JWT tokens with bcrypt password hashing
- **Migrations**: Alembic for database schema management
- **Package Management**: uv for Python dependencies
- **Code Quality**: Ruff for linting/formatting, MyPy for type checking, Pytest for testing

### Frontend (React + TypeScript)
- **Framework**: React 19 with TypeScript (strict mode enabled)
- **Build Tool**: Vite with hot module replacement
- **Routing**: TanStack Router (file-based routing)
- **State Management**: TanStack Query for server state, React hooks for local state
- **UI Components**: Tailwind CSS + shadcn/ui + Radix UI primitives
- **Forms**: React Hook Form with Zod validation schemas
- **Testing**: Playwright for E2E tests

## Architecture Patterns

### Backend Patterns
- **Single Model File**: All SQLModel models and Pydantic schemas in `backend/app/models.py`
- **CRUD Operations**: Centralized database operations in `backend/app/crud.py`
- **Dependency Injection**: Use FastAPI's dependency system for database sessions and auth
- **API Structure**: Feature-based routes in `backend/app/api/routes/`
- **Error Handling**: Use HTTPException with appropriate status codes
- **Type Safety**: All functions must have type hints, use SQLModel for database models

### Frontend Patterns
- **Component Organization**: Feature-based folders with shared UI components
- **API Integration**: Auto-generated client from OpenAPI spec (regenerate with `npm run generate-client`)
- **State Management**: Server state via TanStack Query, avoid prop drilling
- **Form Handling**: React Hook Form + Zod for validation, consistent error display
- **Routing**: File-based routing with TanStack Router, use route loaders for data fetching

## Code Style Guidelines

### Python (Backend)
- Use `snake_case` for variables, functions, and file names
- Use `PascalCase` for class names
- Follow PEP 8 conventions, enforced by Ruff
- Use type hints for all function parameters and return values
- Prefer SQLModel over raw SQLAlchemy for database operations
- Use `uv` commands instead of pip for dependency management

### TypeScript (Frontend)
- Use `camelCase` for variables and functions
- Use `PascalCase` for components and types
- Prefer function components with hooks over class components
- Use strict TypeScript configuration
- Import shadcn/ui components from `@/components/ui/`
- Use Zod schemas for form validation and API response validation

## Development Workflow

### Environment Setup
```bash
# Copy and configure environment
cp .env.example .env

# Start development stack
docker compose up -d
docker compose watch  # For hot reloading
```

### Backend Development
```bash
cd backend
uv sync                              # Install dependencies
source .venv/bin/activate           # Activate virtual environment
bash ./scripts/test.sh              # Run tests
bash ./scripts/format.sh            # Format code
bash ./scripts/lint.sh              # Lint code

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Frontend Development
```bash
cd frontend
npm install                         # Install dependencies
npm run dev                         # Start development server
npm run generate-client             # Regenerate API client after backend changes
npm run build                       # Build for production
npx playwright test                 # Run E2E tests
```

### Testing Strategy
- **Backend**: Use pytest with fixtures, test database isolation
- **Frontend**: Playwright for E2E tests, focus on user workflows
- **API Testing**: Test endpoints through FastAPI test client
- **Database Testing**: Use test database with transaction rollback

```bash
# Backend tests (with Docker)
docker compose exec backend bash scripts/tests-start.sh

# Frontend E2E tests (requires running stack)
docker compose up -d --wait backend
npx playwright test
docker compose down -v
```

## Key Conventions

### Database Models
- Use SQLModel for all database models (combines SQLAlchemy + Pydantic)
- Define both table models and API schemas in `models.py`
- Use UUID primary keys for all models
- Include `created_at` and `updated_at` timestamps
- Use proper foreign key relationships with cascade deletes

### API Design
- Follow REST conventions for endpoint naming
- Use appropriate HTTP status codes (200, 201, 400, 401, 404, 422, 500)
- Include proper error responses with detail messages
- Use Pydantic models for request/response validation
- Implement pagination for list endpoints

### Security
- All API endpoints require authentication except login/signup
- Use JWT tokens with proper expiration
- Hash passwords with bcrypt
- Validate all user inputs with Pydantic/Zod
- Use CORS configuration for frontend integration

### External Integrations
- **Claude API**: Used for PDF extraction and transaction categorization
- **Environment Variables**: Store all secrets in `.env` file
- **Docker**: All services containerized for consistent development