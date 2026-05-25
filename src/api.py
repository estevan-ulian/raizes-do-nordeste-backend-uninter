from fastapi import APIRouter


api_router = APIRouter()


@api_router.get("/health", tags=["health"], status_code=200)
async def health_check():
    """Endpoint to check the health of the API."""
    return {"status": "ok"}
