from fastapi import APIRouter

from src.auth.router import router as auth_router
from src.schemas import HealthCheckSchema, SuccessSchema
from src.units.router import router as units_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(units_router)


@api_router.get("/health", tags=["health"], response_model=SuccessSchema[HealthCheckSchema], status_code=200)
async def health_check():
    """Endpoint to check the health of the API."""
    return SuccessSchema(message="A API está saudável.", result={"status": "ok"})
