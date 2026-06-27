import uuid
from decimal import Decimal

from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth.models import Role, User
from src.orders.exceptions import (
    OrderCannotBeCanceledException,
    OrderItemInvalidException,
    OrderNotFoundException,
    OrderStatusInvalidException,
)
from src.orders.models import Order, OrderChannel, OrderItem, OrderStatus
from src.orders.schemas import OrderCreate, OrderResponse
from src.products.models import Product
from src.units.models import Unit
from src.utils import get_utc_now


VALID_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.WAITING_FOR_PAYMENT: {OrderStatus.PAID, OrderStatus.CANCELED},
    OrderStatus.PAID: {OrderStatus.IN_THE_KITCHEN, OrderStatus.CANCELED},
    OrderStatus.IN_THE_KITCHEN: {OrderStatus.READY, OrderStatus.CANCELED},
    OrderStatus.READY: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELED: set(),
}


class OrderService:
    async def create_order(
        self, order_data: OrderCreate, current_user: User, session: AsyncSession
    ) -> OrderResponse:
        customer_id = order_data.customer_id or current_user.id
        if current_user.role == Role.CUSTOMER and customer_id != current_user.id:
            raise OrderItemInvalidException()
        customer = await self._get_customer_by_id(customer_id, session)
        if not customer:
            raise OrderItemInvalidException()

        unit = await self._get_active_unit(order_data.unit_id, session)
        if not unit:
            raise OrderItemInvalidException()

        product_ids = [item.product_id for item in order_data.items]
        products = await self._get_active_products_by_ids(product_ids, session)
        products_by_id = {product.id: product for product in products}
        if len(products_by_id) != len(set(product_ids)):
            raise OrderItemInvalidException()

        order_items: list[OrderItem] = []
        total_amount = Decimal("0.00")
        for item in order_data.items:
            product = products_by_id[item.product_id]
            if product.unit_id != unit.id:
                raise OrderItemInvalidException()
            subtotal = product.price * item.quantity
            total_amount += subtotal
            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    unit_price=product.price,
                    subtotal=subtotal,
                )
            )

        order = Order(
            customer_id=customer_id,
            unit_id=unit.id,
            order_channel=order_data.order_channel,
            status=OrderStatus.WAITING_FOR_PAYMENT,
            total_amount=total_amount,
            notes=order_data.notes,
        )
        order.items = order_items
        session.add(order)
        await session.commit()
        return await self.get_order_response(order.id, session)

    async def list_orders(
        self,
        session: AsyncSession,
        page: int = 1,
        limit: int = 20,
        order_channel: OrderChannel | None = None,
        status: OrderStatus | None = None,
        customer_id: uuid.UUID | None = None,
    ) -> tuple[list[OrderResponse], int]:
        filters = []
        if order_channel:
            filters.append(Order.order_channel == order_channel)
        if status:
            filters.append(Order.status == status)
        if customer_id:
            filters.append(Order.customer_id == customer_id)

        total_statement = select(func.count(Order.id))
        for query_filter in filters:
            total_statement = total_statement.where(query_filter)
        total_result = await session.exec(total_statement)
        total = total_result.one()

        offset = (page - 1) * limit
        statement = (
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        for query_filter in filters:
            statement = statement.where(query_filter)
        result = await session.exec(statement)
        orders = list(result.all())
        return [self._to_response(order) for order in orders], total

    async def get_order_response(self, order_id: uuid.UUID, session: AsyncSession) -> OrderResponse:
        order = await self.get_order_by_id(order_id, session)
        if not order:
            raise OrderNotFoundException()
        return self._to_response(order)

    async def get_order_by_id(self, order_id: uuid.UUID, session: AsyncSession) -> Order | None:
        statement = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        result = await session.exec(statement)
        return result.one_or_none()

    async def update_order_status(
        self, order_id: uuid.UUID, new_status: OrderStatus, session: AsyncSession
    ) -> OrderResponse:
        order = await self.get_order_by_id(order_id, session)
        if not order:
            raise OrderNotFoundException()
        if new_status not in VALID_STATUS_TRANSITIONS[order.status]:
            raise OrderStatusInvalidException()
        order.status = new_status
        order.updated_at = get_utc_now()
        await session.commit()
        return await self.get_order_response(order.id, session)

    async def mark_order_paid(self, order: Order, session: AsyncSession) -> None:
        if order.status != OrderStatus.WAITING_FOR_PAYMENT:
            raise OrderStatusInvalidException()
        order.status = OrderStatus.PAID
        order.updated_at = get_utc_now()
        session.add(order)

    async def cancel_order(self, order_id: uuid.UUID, session: AsyncSession) -> OrderResponse:
        order = await self.get_order_by_id(order_id, session)
        if not order:
            raise OrderNotFoundException()
        if OrderStatus.CANCELED not in VALID_STATUS_TRANSITIONS[order.status]:
            raise OrderCannotBeCanceledException()
        order.status = OrderStatus.CANCELED
        order.updated_at = get_utc_now()
        await session.commit()
        return await self.get_order_response(order.id, session)

    def ensure_customer_owns_order(self, current_user: User, order: Order) -> None:
        if current_user.role == Role.CUSTOMER and order.customer_id != current_user.id:
            raise OrderNotFoundException()

    async def _get_customer_by_id(self, customer_id: uuid.UUID, session: AsyncSession) -> User | None:
        statement = select(User).where(User.id == customer_id, User.role == Role.CUSTOMER)
        result = await session.exec(statement)
        return result.one_or_none()

    async def _get_active_unit(self, unit_id: uuid.UUID, session: AsyncSession) -> Unit | None:
        statement = select(Unit).where(Unit.id == unit_id, Unit.is_active)
        result = await session.exec(statement)
        return result.one_or_none()

    async def _get_active_products_by_ids(
        self, product_ids: list[uuid.UUID], session: AsyncSession
    ) -> list[Product]:
        statement = select(Product).where(Product.id.in_(product_ids), Product.is_active)
        result = await session.exec(statement)
        return list(result.all())

    def _to_response(self, order: Order) -> OrderResponse:
        return OrderResponse(
            id=order.id,
            customer_id=order.customer_id,
            unit_id=order.unit_id,
            order_channel=order.order_channel,
            status=order.status,
            total_amount=order.total_amount,
            notes=order.notes,
            items=order.items,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
