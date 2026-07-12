import uuid
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.audit.service import AuditAction, audit_service
from src.auth.models import Role, User
from src.inventory.models import Inventory
from src.orders.exceptions import (
    OrderCannotBeCanceledException,
    OrderItemInvalidException,
    OrderNotFoundException,
    OrderStockInsufficientException,
    OrderStatusInvalidException,
)
from src.orders.models import Order, OrderChannel, OrderItem, OrderStatus
from src.orders.schemas import OrderCreate, OrderResponse
from src.products.models import Product
from src.promotions.exceptions import PromotionNotApplicableException, PromotionNotFoundException
from src.promotions.models import OrderPromotion
from src.promotions.service import promotion_service
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
ANONYMOUS_ORDER_CHANNELS = {OrderChannel.TOTEM, OrderChannel.COUNTER}


class OrderService:
    async def create_order(
        self,
        order_data: OrderCreate,
        current_user: User | None,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> OrderResponse:
        customer_id = order_data.customer_id
        if current_user and current_user.role == Role.CUSTOMER:
            customer_id = order_data.customer_id or current_user.id
        if current_user and current_user.role == Role.CUSTOMER and customer_id != current_user.id:
            raise OrderItemInvalidException()
        if customer_id is None and order_data.order_channel not in ANONYMOUS_ORDER_CHANNELS:
            raise OrderItemInvalidException()
        if customer_id and not await self._get_customer_by_id(customer_id, session):
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
        required_quantities: dict[uuid.UUID, int] = {}
        for item in order_data.items:
            product = products_by_id[item.product_id]
            required_quantities[product.id] = required_quantities.get(product.id, 0) + item.quantity
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

        await self._debit_inventory(unit.id, required_quantities, session)

        applied_promotion = None
        discount_amount = Decimal("0.00")
        if order_data.promotion_id:
            applied_promotion = await promotion_service.get_promotion_by_id(order_data.promotion_id, session)
            if applied_promotion is None:
                raise PromotionNotFoundException()
            if not promotion_service.is_applicable(applied_promotion):
                raise PromotionNotApplicableException()
            discount_amount = (total_amount * applied_promotion.discount_percent / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        order = Order(
            customer_id=customer_id,
            unit_id=unit.id,
            order_channel=order_data.order_channel,
            status=OrderStatus.WAITING_FOR_PAYMENT,
            total_amount=total_amount - discount_amount,
            payment_method=order_data.payment_method,
            notes=order_data.notes,
        )
        order.items = order_items
        if applied_promotion:
            order.order_promotions = [
                OrderPromotion(
                    promotion_id=applied_promotion.id,
                    discount_amount=discount_amount,
                )
            ]
        session.add(order)
        await session.flush()
        await audit_service.register(
            session,
            action=AuditAction.ORDER_CREATED,
            resource="order",
            resource_id=order.id,
            user_id=actor_id or (current_user.id if current_user else None),
            details={
                "customer_id": str(customer_id) if customer_id else None,
                "unit_id": str(unit.id),
                "order_channel": order_data.order_channel.value,
                "payment_method": order_data.payment_method,
                "gross_amount": str(total_amount),
                "discount_amount": str(discount_amount),
                "total_amount": str(order.total_amount),
                "promotion_id": str(applied_promotion.id) if applied_promotion else None,
            },
            ip=ip,
        )
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
            .options(selectinload(Order.items), selectinload(Order.order_promotions))
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
        statement = (
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.order_promotions))
            .where(Order.id == order_id)
        )
        result = await session.exec(statement)
        return result.one_or_none()

    async def update_order_status(
        self,
        order_id: uuid.UUID,
        new_status: OrderStatus,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> OrderResponse:
        order = await self.get_order_by_id(order_id, session)
        if not order:
            raise OrderNotFoundException()
        if new_status not in VALID_STATUS_TRANSITIONS[order.status]:
            raise OrderStatusInvalidException()
        previous_status = order.status
        order.status = new_status
        order.updated_at = get_utc_now()
        await session.flush()
        await audit_service.register(
            session,
            action=AuditAction.ORDER_STATUS_UPDATED,
            resource="order",
            resource_id=order.id,
            user_id=actor_id,
            details={
                "previous_status": previous_status.value,
                "new_status": new_status.value,
            },
            ip=ip,
        )
        await session.commit()
        return await self.get_order_response(order.id, session)

    async def mark_order_paid(self, order: Order, session: AsyncSession) -> None:
        if order.status != OrderStatus.WAITING_FOR_PAYMENT:
            raise OrderStatusInvalidException()
        order.status = OrderStatus.PAID
        order.updated_at = get_utc_now()
        session.add(order)

    async def cancel_order(
        self,
        order_id: uuid.UUID,
        session: AsyncSession,
        actor_id: uuid.UUID | None = None,
        ip: str | None = None,
    ) -> OrderResponse:
        order = await self.get_order_by_id(order_id, session)
        if not order:
            raise OrderNotFoundException()
        if OrderStatus.CANCELED not in VALID_STATUS_TRANSITIONS[order.status]:
            raise OrderCannotBeCanceledException()
        previous_status = order.status
        order.status = OrderStatus.CANCELED
        order.updated_at = get_utc_now()
        await session.flush()
        await audit_service.register(
            session,
            action=AuditAction.ORDER_CANCELED,
            resource="order",
            resource_id=order.id,
            user_id=actor_id,
            details={"previous_status": previous_status.value},
            ip=ip,
        )
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

    async def _debit_inventory(
        self,
        unit_id: uuid.UUID,
        required_quantities: dict[uuid.UUID, int],
        session: AsyncSession,
    ) -> None:
        statement = (
            select(Inventory)
            .where(
                Inventory.unit_id == unit_id,
                Inventory.product_id.in_(list(required_quantities.keys())),
            )
            .with_for_update()
        )
        result = await session.exec(statement)
        inventory_items = list(result.all())
        inventory_by_product_id = {item.product_id: item for item in inventory_items}

        for product_id, required_quantity in required_quantities.items():
            inventory_item = inventory_by_product_id.get(product_id)
            if inventory_item is None or inventory_item.quantity < required_quantity:
                raise OrderStockInsufficientException()

        for product_id, required_quantity in required_quantities.items():
            inventory_item = inventory_by_product_id[product_id]
            inventory_item.quantity -= required_quantity
            inventory_item.updated_at = get_utc_now()
            session.add(inventory_item)

    def _to_response(self, order: Order) -> OrderResponse:
        applied_promotions = order.order_promotions
        return OrderResponse(
            id=order.id,
            customer_id=order.customer_id,
            unit_id=order.unit_id,
            order_channel=order.order_channel,
            status=order.status,
            total_amount=order.total_amount,
            payment_method=order.payment_method,
            discount_amount=sum((item.discount_amount for item in applied_promotions), Decimal("0.00")),
            promotion_ids=[item.promotion_id for item in applied_promotions],
            notes=order.notes,
            items=order.items,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
