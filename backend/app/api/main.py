from fastapi import APIRouter

from app.api.routes import accounts, analysis, categories, imports, items, login, private, transactions, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(accounts.router)
api_router.include_router(categories.router)
api_router.include_router(transactions.router)
api_router.include_router(analysis.router)
api_router.include_router(imports.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
