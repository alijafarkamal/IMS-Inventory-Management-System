"""Product management service.

Thin wrappers delegating to domain classes for SRP/DI.
Public API and commit behavior preserved. Merged with activity logging additions.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from inventory_app.models.product import Product, Category, Supplier
from inventory_app.models.user import User
from inventory_app.utils.logging import logger
from inventory_app.config import ROLE_STAFF
from inventory_app.services.auth_service import require_permission
from decimal import Decimal
from inventory_app.services.activity_service import log_activity
from inventory_app.services.product_domain import (
    ProductRepository,
    CategoryRepository,
    SupplierRepository,
    SkuGenerator,
    ProductManager,
)


def create_product(
    db: Session,
    name: str,
    category_id: int,
    price: Decimal,
    supplier_id: int = None,
    description: str = None,
    user: User = None
) -> Product:
    """Create a new product."""
    if user:
        require_permission(user, ROLE_STAFF)
    
    manager = ProductManager(
        products=ProductRepository(db),
        categories=CategoryRepository(db),
        suppliers=SupplierRepository(db),
        sku_gen=SkuGenerator(),
    )
    product = manager.create_product(
        name=name,
        category_id=category_id,
        price=price,
        supplier_id=supplier_id,
        description=description,
        db=db,
    )
    logger.info(f"Created product: {product.name} (SKU: {product.sku})")
    try:
        if user:
            log_activity(db, user, action="PRODUCT_CREATE", entity_type="Product", entity_id=product.id, details=f"SKU={product.sku}")
    except Exception:
        pass
    return product


def update_product(
    db: Session,
    product_id: int,
    name: str = None,
    category_id: int = None,
    price: Decimal = None,
    supplier_id: int = None,
    description: str = None,
    is_active: bool = None,
    user: User = None
) -> Product:
    """Update a product."""
    if user:
        require_permission(user, ROLE_STAFF)
    
    manager = ProductManager(
        products=ProductRepository(db),
        categories=CategoryRepository(db),
        suppliers=SupplierRepository(db),
        sku_gen=SkuGenerator(),
    )
    product = manager.update_product(
        product_id=product_id,
        name=name,
        category_id=category_id,
        price=price,
        supplier_id=supplier_id,
        description=description,
        is_active=is_active,
    )
    logger.info(f"Updated product: {product.name} (ID: {product_id})")
    try:
        if user:
            log_activity(db, user, action="PRODUCT_UPDATE", entity_type="Product", entity_id=product.id)
    except Exception:
        pass
    return product


def delete_product(db: Session, product_id: int, user: User = None) -> bool:
    """Delete a product (soft delete by setting is_active=False)."""
    # Only Manager or Admin may deactivate/delete products
    if user:
        from inventory_app.config import ROLE_MANAGER
        require_permission(user, ROLE_MANAGER)
    
    manager = ProductManager(
        products=ProductRepository(db),
        categories=CategoryRepository(db),
        suppliers=SupplierRepository(db),
        sku_gen=SkuGenerator(),
    )
    result = manager.deactivate_product(product_id=product_id)
    logger.info(f"Deactivated product (ID: {product_id})")
    try:
        if user:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                log_activity(db, user, action="PRODUCT_DEACTIVATE", entity_type="Product", entity_id=product.id)
    except Exception:
        pass
    return result


def search_products(
    db: Session,
    query: str = None,
    category_id: int = None,
    active_only: bool = True
) -> list[Product]:
    """Search products by name, SKU, or category."""
    # Delegate search to repository for consistency
    return ProductRepository(db).search(query=query, category_id=category_id, active_only=active_only)


def get_product(db: Session, product_id: int) -> Product:
    """Get a product by ID."""
    return db.query(Product).filter(Product.id == product_id).first()


def get_all_categories(db: Session) -> list[Category]:
    """Get all categories."""
    return db.query(Category).order_by(Category.name).all()


def get_all_suppliers(db: Session) -> list[Supplier]:
    """Get all suppliers."""
    return db.query(Supplier).order_by(Supplier.name).all()


def create_category(db: Session, name: str, description: str = None) -> Category:
    """Create a new category."""
    if db.query(Category).filter(Category.name == name).first():
        raise ValueError(f"Category '{name}' already exists")
    
    category = Category(name=name, description=description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def create_supplier(
    db: Session,
    name: str,
    contact_person: str = None,
    email: str = None,
    phone: str = None,
    address: str = None
) -> Supplier:
    """Create a new supplier."""
    if db.query(Supplier).filter(Supplier.name == name).first():
        raise ValueError(f"Supplier '{name}' already exists")
    
    supplier = Supplier(
        name=name,
        contact_person=contact_person,
        email=email,
        phone=phone,
        address=address
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier

