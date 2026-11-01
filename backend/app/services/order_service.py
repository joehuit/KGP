"""Order service managing customer spare-parts orders and historical snapshotting."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import secrets
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.customer import Customer
from app.models.idempotency import IdempotencyKey
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.common import ResponseEnvelope
from app.schemas.order import (
    GuestOrderCreate,
    GuestOrderResponse,
    OrderCreate,
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdate,
)


class OrderService:
    """Service handling order creation with immutable product snapshots and lifecycle management."""

    @staticmethod
    def _generate_order_reference(db: Session) -> str:
        """Generate a collision-resistant human-readable order reference like KGP-20261029-A1B2."""
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        for _ in range(5):
            suffix = secrets.token_hex(2).upper()
            ref = f"KGP-{today_str}-{suffix}"
            exists = db.scalar(select(Order.id).where(Order.order_reference == ref))
            if not exists:
                return ref
        raise RuntimeError("Failed to generate unique order reference after multiple attempts.")

    @staticmethod
    def _generate_tracking_token(db: Session) -> str:
        """Generate an unguessable cryptographically secure tracking token."""
        for _ in range(5):
            token = secrets.token_urlsafe(32)
            exists = db.scalar(select(Order.id).where(Order.tracking_token == token))
            if not exists:
                return token
        raise RuntimeError("Failed to generate unique tracking token after multiple attempts.")

    @staticmethod
    def mask_phone_number(phone: str) -> str:
        """Mask middle digits of phone number for privacy: 0555123456 -> 0555****56."""
        if len(phone) >= 8:
            return phone[:4] + "****" + phone[-2:]
        return "****"

    @classmethod
    def create_guest_order(
        cls,
        db: Session,
        data: GuestOrderCreate,
        idempotency_key: Optional[str] = None,
        request_hash: Optional[str] = None,
    ) -> Tuple[Order, Customer]:
        """Create a new order for a guest customer with delivery and contact information."""
        if not data.items:
            raise ValidationError("Order must contain at least one item.")

        # 1. Look up existing customer by phone number, or register a new one
        customer = db.scalar(select(Customer).where(Customer.phone_number == data.phone_number))
        full_address = f"{data.commune.strip()}, {data.delivery_address.strip()}"
        if not customer:
            customer = Customer(
                full_name=data.full_name.strip(),
                phone_number=data.phone_number,
                wilaya=data.wilaya.strip(),
                address=full_address,
                is_active=True,
            )
            db.add(customer)
            db.flush()
        else:
            # If customer exists, verify active status
            if not customer.is_active:
                raise ValidationError(f"Customer account associated with phone number '{data.phone_number}' is inactive.")
            # For existing customers: preserve the existing profile to prevent unauthorized
            # overwriting by unauthenticated guest submissions. The specific guest delivery
            # contact info for this order is stored on the order entity itself.

        # 2. Process order items with server-side price calculation
        order_items: List[OrderItem] = []
        grand_total = Decimal("0.00")

        item_quantities = {}
        for item in data.items:
            item_quantities[item.product_id] = item_quantities.get(item.product_id, 0) + item.quantity

        for product_id, quantity in item_quantities.items():
            product = db.get(Product, product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found.")
            if not product.is_active:
                raise ValidationError(f"Product '{product.name}' (SKU: {product.sku}) is currently inactive.")

            line_unit_price = product.selling_price
            line_total = (line_unit_price * Decimal(quantity)).quantize(Decimal("0.01"))
            grand_total += line_total

            order_item = OrderItem(
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                unit_price=line_unit_price,
                quantity=quantity,
                total_price=line_total,
            )
            order_items.append(order_item)

        # 3. Deduplication check (30 seconds window)
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        recent_orders = list(
            db.scalars(
                select(Order)
                .where(
                    Order.customer_id == customer.id,
                    Order.status == OrderStatus.PENDING,
                    Order.created_at >= cutoff_time,
                )
                .options(selectinload(Order.items))
            ).all()
        )
        current_items_signature = sorted(item_quantities.items())
        notes = (
            f"Destinataire: {data.full_name.strip()} | "
            f"Wilaya: {data.wilaya.strip()} | "
            f"Commune: {data.commune.strip()} | "
            f"Adresse: {data.delivery_address.strip()}"
        )
        if data.customer_notes and data.customer_notes.strip():
            notes += f"\nNote: {data.customer_notes.strip()}"

        for recent in recent_orders:
            recent_items_signature = sorted((it.product_id, it.quantity) for it in recent.items)
            if recent_items_signature == current_items_signature:
                raise ConflictError(
                    f"Duplicate order detected. An identical order ({recent.order_reference}) was submitted within the last 30 seconds."
                )

        # 4. Generate order reference and secure tracking token
        order_ref = cls._generate_order_reference(db)
        tracking_token = cls._generate_tracking_token(db)

        order = Order(
            order_reference=order_ref,
            tracking_token=tracking_token,
            customer_id=customer.id,
            status=OrderStatus.PENDING,
            total_amount=grand_total.quantize(Decimal("0.01")),
            customer_notes=notes,
            items=order_items,
        )
        db.add(order)

        if idempotency_key and request_hash:
            db.flush()
            guest_resp = GuestOrderResponse(
                id=order.id,
                order_reference=order.order_reference,
                tracking_token=order.tracking_token,
                status=order.status,
                total_amount=order.total_amount,
                customer_name=customer.full_name,
                customer_phone_masked=cls.mask_phone_number(customer.phone_number),
                wilaya=data.wilaya,
                commune=data.commune,
                delivery_address=data.delivery_address,
                customer_notes=data.customer_notes,
                items=[OrderItemResponse.model_validate(it) for it in order.items],
                created_at=order.created_at or datetime.now(timezone.utc),
            )
            envelope = ResponseEnvelope(
                data=guest_resp,
                message="Order placed successfully.",
            )
            now = datetime.now(timezone.utc)
            idemp_record = IdempotencyKey(
                key=idempotency_key,
                request_hash=request_hash,
                response_code=201,
                response_body=json.dumps(envelope.model_dump(mode="json"), default=str),
                expires_at=now + timedelta(hours=24),
            )
            db.add(idemp_record)

        try:
            db.commit()
            db.refresh(order)
            return order, customer
        except Exception:
            db.rollback()
            raise

    @classmethod
    def get_order_by_tracking_token(cls, db: Session, tracking_token: str) -> Order:
        """Securely look up a guest order by unguessable tracking token."""
        query = (
            select(Order)
            .where(Order.tracking_token == tracking_token)
            .options(selectinload(Order.items), selectinload(Order.customer))
        )
        order = db.scalar(query)
        if not order:
            raise NotFoundError("Order not found or invalid tracking token.")
        return order

    @classmethod
    def parse_order_delivery_details(
        cls, order: Order, customer: Customer
    ) -> Tuple[str, str, str, str, Optional[str]]:
        """Extract recipient name, wilaya, commune, delivery address, and notes.
        Prefers frozen order metadata in customer_notes if present, falling back to customer profile.
        Returns: (recipient_name, wilaya, commune, delivery_address, custom_notes)
        """
        recipient_name = customer.full_name
        wilaya = customer.wilaya or ""
        commune = ""
        delivery_address = customer.address or ""
        if "," in delivery_address:
            parts = delivery_address.split(",", 1)
            commune = parts[0].strip()
            delivery_address = parts[1].strip()
        custom_notes: Optional[str] = order.customer_notes

        raw_notes = order.customer_notes or ""
        lines = raw_notes.split("\n", 1)
        header_line = lines[0].strip()
        if header_line.startswith("Destinataire:"):
            # Format: Destinataire: {name} | Wilaya: {wilaya} | Commune: {commune} | Adresse: {address}
            segments = [seg.strip() for seg in header_line.split("|")]
            for seg in segments:
                if seg.startswith("Destinataire:"):
                    recipient_name = seg.replace("Destinataire:", "").strip()
                elif seg.startswith("Wilaya:"):
                    wilaya = seg.replace("Wilaya:", "").strip()
                elif seg.startswith("Commune:"):
                    commune = seg.replace("Commune:", "").strip()
                elif seg.startswith("Adresse:"):
                    delivery_address = seg.replace("Adresse:", "").strip()

            if len(lines) > 1 and lines[1].startswith("Note:"):
                custom_notes = lines[1].replace("Note:", "").strip()
            elif len(lines) > 1:
                custom_notes = lines[1].strip()
            else:
                custom_notes = None

        return recipient_name, wilaya, commune, delivery_address, custom_notes

    @classmethod
    def create_order(
        cls,
        db: Session,
        data: OrderCreate,
        idempotency_key: Optional[str] = None,
        request_hash: Optional[str] = None,
    ) -> Order:
        """Create a new order with snapshotting of product names, SKUs, and prices.
        If idempotency_key is provided, persists the idempotency record in the SAME transaction.
        """
        # 1. Validate customer existence and active status
        customer = db.get(Customer, data.customer_id)
        if not customer:
            raise NotFoundError(f"Customer with ID {data.customer_id} does not exist.")
        if not customer.is_active:
            raise ValidationError(f"Customer '{customer.full_name}' is inactive. Cannot place orders.")

        if not data.items:
            raise ValidationError("Order must contain at least one item.")

        # 2. Process each ordered item and preserve immutable snapshots
        order_items: List[OrderItem] = []
        grand_total = Decimal("0.00")

        # Group duplicate item requests if any
        item_quantities = {}
        for item in data.items:
            item_quantities[item.product_id] = item_quantities.get(item.product_id, 0) + item.quantity

        for product_id, quantity in item_quantities.items():
            product = db.get(Product, product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found.")
            if not product.is_active:
                raise ValidationError(f"Product '{product.name}' (SKU: {product.sku}) is currently inactive.")

            line_unit_price = product.selling_price
            line_total = (line_unit_price * Decimal(quantity)).quantize(Decimal("0.01"))
            grand_total += line_total

            # Snapshot historical state at purchase time
            order_item = OrderItem(
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                unit_price=line_unit_price,
                quantity=quantity,
                total_price=line_total,
            )
            order_items.append(order_item)

        # 3. Prevent duplicate order submissions within short deduplication window (30 seconds)
        cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=30)
        recent_orders = list(
            db.scalars(
                select(Order)
                .where(
                    Order.customer_id == customer.id,
                    Order.status == OrderStatus.PENDING,
                    Order.created_at >= cutoff_time,
                )
                .options(selectinload(Order.items))
            ).all()
        )
        current_items_signature = sorted(item_quantities.items())
        current_notes = (data.customer_notes or "").strip()
        for recent in recent_orders:
            recent_items_signature = sorted((it.product_id, it.quantity) for it in recent.items)
            recent_notes = (recent.customer_notes or "").strip()
            if recent_items_signature == current_items_signature and recent_notes == current_notes:
                raise ConflictError(
                    f"Duplicate order detected. An identical order ({recent.order_reference}) was submitted within the last 30 seconds."
                )

        # 4. Create the order entity (Inventory is NOT decremented in Phase 1 per architecture spec)
        order = Order(
            order_reference=cls._generate_order_reference(db),
            customer_id=customer.id,
            status=OrderStatus.PENDING,
            total_amount=grand_total.quantize(Decimal("0.01")),
            customer_notes=data.customer_notes,
            items=order_items,
        )

        db.add(order)

        if idempotency_key and request_hash:
            # Flush so order gets its generated primary key and timestamps before serialization
            db.flush()
            envelope = ResponseEnvelope(
                data=OrderResponse.model_validate(order),
                message="Order placed successfully.",
            )
            now = datetime.now(timezone.utc)
            idemp_record = IdempotencyKey(
                key=idempotency_key,
                request_hash=request_hash,
                response_code=201,
                response_body=json.dumps(envelope.model_dump(mode="json"), default=str),
                expires_at=now + timedelta(hours=24),
            )
            db.add(idemp_record)

        try:
            db.commit()
            db.refresh(order)
            return order
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_order_by_id(db: Session, order_id: int) -> Order:
        """Retrieve order with its immutable line items."""
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        order = db.scalar(query)
        if not order:
            raise NotFoundError(f"Order with ID {order_id} not found.")
        return order

    @staticmethod
    def list_orders(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        customer_id: Optional[int] = None,
        status_filter: Optional[OrderStatus] = None,
    ) -> Tuple[List[Order], int]:
        """List orders with optional customer or status filtering."""
        query = select(Order).options(selectinload(Order.items))

        if customer_id is not None:
            query = query.where(Order.customer_id == customer_id)

        if status_filter is not None:
            query = query.where(Order.status == status_filter)

        count_query = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_query) or 0

        offset = (page - 1) * page_size
        items = list(
            db.scalars(
                query.order_by(Order.created_at.desc()).offset(offset).limit(page_size)
            ).all()
        )

        return items, total

    # Allowed order lifecycle state transitions
    VALID_STATUS_TRANSITIONS = {
        OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
        OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
        OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
        OrderStatus.SHIPPED: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
        OrderStatus.DELIVERED: set(),
        OrderStatus.CANCELLED: set(),
    }

    @classmethod
    def update_order_status(cls, db: Session, order_id: int, data: OrderStatusUpdate) -> Order:
        """Update order lifecycle status according to valid state machine transitions."""
        order = cls.get_order_by_id(db, order_id)

        # Disallow modifications to cancelled or delivered orders
        if order.status in (OrderStatus.CANCELLED, OrderStatus.DELIVERED):
            raise ValidationError(
                f"Cannot change status of an order that is already {order.status.value}."
            )

        allowed_next = cls.VALID_STATUS_TRANSITIONS.get(order.status, set())
        if data.status not in allowed_next:
            allowed_str = ", ".join(s.value for s in sorted(allowed_next, key=lambda x: x.value)) or "None"
            raise ValidationError(
                f"Invalid order status transition from '{order.status.value}' to '{data.status.value}'. "
                f"Permitted next status: [{allowed_str}]."
            )

        order.status = data.status
        try:
            db.commit()
            db.refresh(order)
            return order
        except Exception:
            db.rollback()
            raise
