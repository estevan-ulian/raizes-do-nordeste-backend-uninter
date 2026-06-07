from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api import api_router
from src.auth.exceptions import register_auth_exception_handlers
from src.config import config
from src.exceptions import register_global_exception_handlers
from src.middlewares import register_middlewares
from src.on_startup import create_first_admin_if_not_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Iniciando a aplicação...")
    await create_first_admin_if_not_exists()
    yield
    print("Encerrando a aplicação...")


fastapi_config = {
    "title": "Raízes do Nordeste - Backend",
    "description": "Backend para o projeto Raízes do Nordeste.",
    "root_path": "/api",
    "redoc_url": "/redoc",
    "docs_url": "/docs",
    "version": "0.1.0",
    "lifespan": lifespan,
}

SHOW_DOCS_ENVIRONMENT = ("development", "staging")
if config.ENVIRONMENT not in SHOW_DOCS_ENVIRONMENT:
    fastapi_config["docs_url"] = None
    fastapi_config["redoc_url"] = None

app = FastAPI(**fastapi_config)

register_global_exception_handlers(app)
register_auth_exception_handlers(app)

register_middlewares(app)

app.include_router(api_router)
