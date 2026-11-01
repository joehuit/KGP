"""Product service managing spare-parts catalog business operations."""

from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.models.category import Category
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Service handling product catalog creation, updates, and filtering."""

    @staticmethod
    def create_product(db: Session, data: ProductCreate) -> Product:
        """Create a new product after verifying category and SKU uniqueness."""
        # 1. Verify Category exists
        category = db.get(Category, data.category_id)
        if not category:
            raise NotFoundError(f"Category with ID {data.category_id} does not exist.")
        if not category.is_active:
            raise ValidationError(f"Category '{category.name}' is inactive. Cannot add products to inactive categories.")

        # 2. Check SKU uniqueness
        existing_sku = db.scalars(
            select(Product).where(func.upper(Product.sku) == data.sku.upper())
        ).first()
        if existing_sku:
            raise ConflictError(f"Product with SKU '{data.sku}' already exists.")

        # 3. Create Product
        product = Product(
            sku=data.sku,
            name=data.name,
            category_id=data.category_id,
            selling_price=data.selling_price,
            available_quantity=data.available_quantity,
            description=data.description,
            is_active=data.is_active,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_product_by_id(db: Session, product_id: int) -> Product:
        """Retrieve a single product by ID or raise NotFoundError."""
        product = db.get(Product, product_id)
        if not product:
            raise NotFoundError(f"Product with ID {product_id} not found.")
        return product

    @staticmethod
    def list_products(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        active_only: bool = True,
    ) -> Tuple[List[Product], int]:
        """Query products with optional category filter, text search, and pagination."""
        query = select(Product)

        if active_only:
            query = query.where(Product.is_active.is_(True))

        if category_id is not None:
            query = query.where(Product.category_id == category_id)

        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Product.name).like(search_term),
                    func.lower(Product.sku).like(search_term),
                )
            )

        # Count total matching rows
        count_query = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_query) or 0

        # Apply ordering and pagination
        offset = (page - 1) * page_size
        items = list(
            db.scalars(
                query.order_by(Product.name.asc()).offset(offset).limit(page_size)
            ).all()
        )

        return items, total

    @staticmethod
    def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
        """Update existing product details and pricing."""
        product = ProductService.get_product_by_id(db, product_id)

        update_dict = data.model_dump(exclude_unset=True)

        # Validate category if being changed
        if "category_id" in update_dict and update_dict["category_id"] is not None:
            category = db.get(Category, update_dict["category_id"])
            if not category:
                raise NotFoundError(f"Category with ID {update_dict['category_id']} not found.")

        # Validate SKU uniqueness if being changed
        if "sku" in update_dict and update_dict["sku"] is not None:
            new_sku = update_dict["sku"]
            existing = db.scalars(
                select(Product).where(
                    func.upper(Product.sku) == new_sku.upper(),
                    Product.id != product_id,
                )
            ).first()
            if existing:
                raise ConflictError(f"Product with SKU '{new_sku}' already exists.")

        for key, value in update_dict.items():
            setattr(product, key, value)

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete_product(db: Session, product_id: int) -> dict:
        """Safely delete product or deactivate if it has historical order references."""
        from app.models.order_item import OrderItem

        product = ProductService.get_product_by_id(db, product_id)

        # Check if product is referenced in any order
        has_orders = db.scalar(
            select(func.count()).select_from(OrderItem).where(OrderItem.product_id == product_id)
        ) or 0

        if has_orders > 0:
            product.is_active = False
            db.commit()
            return {
                "deleted": False,
                "deactivated": True,
                "message": f"Product '{product.name}' has {has_orders} historical order line(s). Deactivated to preserve order integrity.",
            }

        db.delete(product)
        db.commit()
        return {
            "deleted": True,
            "deactivated": False,
            "message": f"Product '{product.name}' deleted successfully.",
        }

