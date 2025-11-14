"""Product management service."""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from inventory_app.models.product import Product, Category, Supplier
from inventory_app.models.user import User
from inventory_app.utils.sku import generate_sku
from inventory_app.utils.logging import logger
from inventory_app.config import ROLE_STAFF
from inventory_app.services.auth_service import require_permission
from decimal import Decimal


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
    
    # Generate SKU
    sku = generate_sku(name, category_id, db_session=db)
    
    product = Product(
        name=name,
        sku=sku,
        category_id=category_id,
        price=price,
        supplier_id=supplier_id,
        description=description,
        is_active=True
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    logger.info(f"Created product: {name} (SKU: {sku})")
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
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product with ID {product_id} not found")
    
    if name is not None:
        product.name = name
    if category_id is not None:
        product.category_id = category_id
    if price is not None:
        product.price = price
    if supplier_id is not None:
        product.supplier_id = supplier_id
    if description is not None:
        product.description = description
    if is_active is not None:
        product.is_active = is_active
    
    db.commit()
    db.refresh(product)
    logger.info(f"Updated product: {product.name} (ID: {product_id})")
    return product


def delete_product(db: Session, product_id: int, user: User = None) -> bool:
    """Delete a product (soft delete by setting is_active=False)."""
    if user:
        require_permission(user, ROLE_STAFF)
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product with ID {product_id} not found")
    
    product.is_active = False
    db.commit()
    logger.info(f"Deactivated product: {product.name} (ID: {product_id})")
    return True


def search_products(
    db: Session,
    query: str = None,
    category_id: int = None,
    active_only: bool = True
) -> list[Product]:
    """Search products by name, SKU, or category."""
    q = db.query(Product)
    
    if active_only:
        q = q.filter(Product.is_active == True)
    
    if query:
        q = q.filter(
            or_(
                Product.name.ilike(f"%{query}%"),
                Product.sku.ilike(f"%{query}%")
            )
        )
    
    if category_id:
        q = q.filter(Product.category_id == category_id)
    
    return q.order_by(Product.name).all()


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

