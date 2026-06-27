from fastapi import APIRouter

from src.auth.router import router as auth_router
from src.inventory.router import router as inventory_router
from src.loyalty.router import router as loyalty_router
from src.orders.router import router as orders_router
from src.payments.router import router as payments_router
from src.products.router import router as products_router
from src.schemas import HealthCheckSchema, SuccessSchema
from src.units.router import router as units_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(units_router)
api_router.include_router(products_router)
api_router.include_router(inventory_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)
api_router.include_router(loyalty_router)


@api_router.get("/health", tags=["health"], response_model=SuccessSchema[HealthCheckSchema], status_code=200)
async def health_check():
    """Endpoint to check the health of the API."""
    return SuccessSchema(message="A API está saudável.", result={"status": "ok"})
