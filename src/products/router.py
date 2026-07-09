import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.dependencies import RoleChecker
from src.auth.exceptions import InsufficientPermissionException
from src.auth.models import Role, User
from src.database import get_async_session
from src.exceptions import error_responses
from src.products.exceptions import (
    ProductImageInvalidException,
    ProductImageTooLargeException,
    ProductNotFoundException,
)
from src.products.schemas import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from src.products.service import ProductService
from src.schemas import SuccessSchema
from src.storage import storage
from src.units.exceptions import UnitNotFoundException
from src.units.service import UnitService

router = APIRouter(prefix="/products", tags=["products"])
product_service = ProductService()
unit_service = UnitService()
manage_products_role_checker = RoleChecker(allowed_roles=[Role.ADMIN, Role.MANAGER])
read_products_role_checker = RoleChecker(
    allowed_roles=[Role.ADMIN, Role.MANAGER, Role.CUSTOMER, Role.SERVER, Role.KITCHEN]
)
AUTHORIZATION_OPENAPI_EXTRA = {
    "parameters": [
        {
            "name": "Authorization",
            "in": "header",
            "required": True,
            "description": "The access token to use for authentication.",
            "schema": {"type": "string", "example": "Bearer eyJhbGciOiJIUzI1NiIs..."},
        }
    ]
}


async def get_submitted_form_fields(request: Request) -> set[str]:
    form = await request.form()
    return set(form.keys())


async def save_product_image(image: UploadFile | None) -> str | None:
    if image is None:
        return None
    try:
        return await storage.save_product_image(image)
    except ValueError as exc:
        if str(exc) == "image_too_large":
            raise ProductImageTooLargeException() from exc
        raise ProductImageInvalidException() from exc


@router.post(
    "/",
    response_model=SuccessSchema[ProductResponse],
    responses=error_responses(
        InsufficientPermissionException,
        ProductImageInvalidException,
        ProductImageTooLargeException,
        UnitNotFoundException,
    ),
    status_code=status.HTTP_201_CREATED,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def create_product(
    unit_id: uuid.UUID = Form(...),
    name: str = Form(..., min_length=1, max_length=255),
    price: Decimal = Form(..., gt=0),
    category: str = Form(..., min_length=1, max_length=100),
    description: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(manage_products_role_checker),
):
    """Create a new product. Requires ADMIN or MANAGER role."""
    unit = await unit_service.get_unit_by_id(unit_id, session)
    if not unit:
        raise UnitNotFoundException()

    image_url = None
    try:
        image_url = await save_product_image(image)
        product_data = ProductCreate(
            unit_id=unit_id,
            name=name,
            description=description,
            price=price,
            category=category,
            image_url=image_url,
        )
        new_product = await product_service.create_product(product_data, session)
    except Exception:
        storage.delete_by_public_url(image_url)
        raise
    return SuccessSchema(message="Produto criado com sucesso.", result=new_product)


@router.get(
    "/",
    response_model=SuccessSchema[ProductListResponse],
    responses=error_responses(InsufficientPermissionException, UnitNotFoundException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def list_products(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    unit_id: uuid.UUID | None = Query(default=None, alias="unitId"),
    category: str | None = Query(default=None, min_length=1, max_length=100),
    include_inactive: bool = Query(default=False, alias="includeInactive"),
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(read_products_role_checker),
):
    """List products with pagination and filters."""
    if unit_id:
        unit = await unit_service.get_unit_by_id(unit_id, session)
        if not unit:
            raise UnitNotFoundException()

    products, total = await product_service.list_products(
        session,
        page=page,
        limit=limit,
        unit_id=unit_id,
        category=category,
        include_inactive=include_inactive,
    )
    return SuccessSchema(
        message="Produtos obtidos com sucesso.",
        result=ProductListResponse(items=products, total=total, page=page, limit=limit),
    )


@router.get(
    "/{product_id}",
    response_model=SuccessSchema[ProductResponse],
    responses=error_responses(InsufficientPermissionException, ProductNotFoundException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def get_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(read_products_role_checker),
):
    """Get a product by id."""
    product = await product_service.get_product_by_id(product_id, session)
    if not product:
        raise ProductNotFoundException()
    return SuccessSchema(message="Produto obtido com sucesso.", result=product)


@router.patch(
    "/{product_id}",
    response_model=SuccessSchema[ProductResponse],
    responses=error_responses(
        InsufficientPermissionException,
        ProductImageInvalidException,
        ProductImageTooLargeException,
        ProductNotFoundException,
        UnitNotFoundException,
    ),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def update_product(
    product_id: uuid.UUID,
    request: Request,
    unit_id: uuid.UUID | None = Form(default=None),
    name: str | None = Form(default=None, min_length=1, max_length=255),
    price: Decimal | None = Form(default=None, gt=0),
    category: str | None = Form(default=None, min_length=1, max_length=100),
    description: str | None = Form(
        default=None, description="Send a empty string to remove the description."
    ),
    is_active: bool | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(manage_products_role_checker),
):
    """Update a product. Requires ADMIN or MANAGER role."""
    product = await product_service.get_product_by_id(product_id, session)
    if not product:
        raise ProductNotFoundException()
    if unit_id:
        unit = await unit_service.get_unit_by_id(unit_id, session)
        if not unit:
            raise UnitNotFoundException()

    submitted_fields = await get_submitted_form_fields(request)
    field_values = {
        "unit_id": unit_id,
        "name": name,
        "description": None if description == "" else description,
        "price": price,
        "category": category,
        "is_active": is_active,
    }
    update_data = {key: value for key, value in field_values.items() if key in submitted_fields}

    image_url = None
    old_image_url = product.image_url
    try:
        image_url = await save_product_image(image)
        if image_url is not None:
            update_data["image_url"] = image_url
        product_data = ProductUpdate(**update_data)
        updated_product = await product_service.update_product(product, product_data, session)
    except Exception:
        storage.delete_by_public_url(image_url)
        raise

    if image_url is not None and old_image_url != image_url:
        storage.delete_by_public_url(old_image_url)
    return SuccessSchema(message="Produto atualizado com sucesso.", result=updated_product)


@router.delete(
    "/{product_id}",
    response_model=SuccessSchema[ProductResponse],
    responses=error_responses(InsufficientPermissionException, ProductNotFoundException),
    status_code=status.HTTP_200_OK,
    openapi_extra=AUTHORIZATION_OPENAPI_EXTRA,
)
async def deactivate_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    _current_user: User = Depends(manage_products_role_checker),
):
    """Deactivate a product. Requires ADMIN or MANAGER role."""
    product = await product_service.get_product_by_id(product_id, session)
    if not product:
        raise ProductNotFoundException()
    deactivated_product = await product_service.deactivate_product(product, session)
    return SuccessSchema(message="Produto desativado com sucesso.", result=deactivated_product)
