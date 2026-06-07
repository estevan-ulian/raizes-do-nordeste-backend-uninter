from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import config


def register_middlewares(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_methods=["PUT", "GET", "POST", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=True,
        allow_origins=[config.FRONTEND_URL] if config.FRONTEND_URL else ["*"],
    )
