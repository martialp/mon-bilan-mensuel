# Project Structure

## Root Level
- `backend/` - FastAPI Python backend application
- `frontend/` - React TypeScript frontend application
- `docs/` - Project documentation and database schema
- `scripts/` - Deployment and build scripts
- `docker-compose.yml` - Main Docker Compose configuration
- `.env` - Environment variables (copy from `.env.example`)

## Backend Structure (`backend/`)
```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── models.py              # SQLModel database models and schemas
├── crud.py                # Database operations
├── utils.py               # Utility functions
├── core/
│   ├── config.py          # Application configuration
│   ├── db.py              # Database connection and session
│   └── security.py        # Authentication and security utilities
├── api/
│   ├── main.py            # API router configuration
│   ├── deps.py            # Dependency injection
│   └── routes/            # API endpoint modules
└── alembic/               # Database migration files
```

## Frontend Structure (`frontend/`)
```
src/
├── main.tsx               # React application entry point
├── client/                # Auto-generated API client
├── components/
│   ├── ui/                # Reusable UI components (shadcn/ui)
│   ├── Common/            # Shared application components
│   ├── Admin/             # Admin-specific components
│   ├── Items/             # Item management components
│   ├── Sidebar/           # Navigation components
│   └── UserSettings/      # User profile components
├── hooks/                 # Custom React hooks
├── routes/                # Page components and routing
└── lib/                   # Utility functions
```

## Key Files and Conventions

### Backend
- **Models**: All database models and Pydantic schemas in `models.py`
- **API Routes**: Organized by feature in `api/routes/` (users, items, accounts, categories, transactions)
- **CRUD Operations**: Database operations in `crud.py`
- **Configuration**: Environment-based config in `core/config.py`
- **Tests**: Mirror the app structure in `tests/`

### Frontend
- **Components**: Feature-based organization with shared UI components
- **API Client**: Auto-generated from OpenAPI spec, regenerate with `npm run generate-client`
- **Routing**: File-based routing with TanStack Router
- **State**: Server state managed by TanStack Query, local state with React hooks

### Database Models
- **User**: Authentication and user management
- **Account**: Financial accounts (credit cards, bank accounts)
- **Category**: Transaction categories (shared across users)
- **Transaction**: Financial transactions with categorization
- **Item**: Legacy model from template (to be removed/replaced)

### Naming Conventions
- **Backend**: Snake_case for Python (variables, functions, files)
- **Frontend**: camelCase for TypeScript, PascalCase for components
- **Database**: Snake_case for table and column names
- **API Endpoints**: Kebab-case in URLs, follow REST conventions
- **Environment Variables**: UPPER_SNAKE_CASE

### File Organization Rules
- Group related functionality together (accounts, categories, transactions)
- Keep components small and focused on single responsibility
- Use index files for clean imports
- Place shared utilities in appropriate lib/utils directories
- Tests should mirror the structure of the code they test