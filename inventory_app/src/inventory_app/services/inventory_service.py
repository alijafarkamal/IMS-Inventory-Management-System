"""Inventory management service with stock adjustments and audit logging."""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from inventory_app.models.stock import StockLevel, Warehouse, Batch
from inventory_app.models.product import Product
from inventory_app.models.audit import InventoryAudit
from inventory_app.models.user import User
from inventory_app.utils.logging import logger
from inventory_app.config import ROLE_STAFF
from inventory_app.services.auth_service import require_permission
from inventory_app.services.inventory_domain import (
    StockRepository,
    AuditFactory,
    InventoryAdjuster,
)
import json


def adjust_stock(
    db: Session,
    product_id: int,
    warehouse_id: int,
    quantity: int,
    user: User,
    reason: str,
    batch_id: int = None,
) -> StockLevel:
    """Adjust stock and create audit via domain classes (no commit here)."""
    require_permission(user, ROLE_STAFF)

    repo = StockRepository(db)
    adjuster = InventoryAdjuster(repo=repo, audit_factory=AuditFactory())
    stock = adjuster.adjust_stock(
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        user=user,
        reason=reason,
        batch_id=batch_id,
    )

    logger.info(
        f"Stock adjusted: Product {product_id}, Warehouse {warehouse_id}, change: {quantity:+d} by {user.username}"
    )
    return stock


def get_stock(db: Session, product_id: int) -> int:
    """Get total stock across all warehouses for a product."""
    total = db.query(StockLevel).filter(
        StockLevel.product_id == product_id
    ).with_entities(
        func.sum(StockLevel.quantity).label("total")
    ).scalar()
    return total or 0


def get_warehouse_stock(db: Session, product_id: int, warehouse_id: int) -> int:
    """Get stock level for a product in a specific warehouse."""
    stock = db.query(StockLevel).filter(
        and_(
            StockLevel.product_id == product_id,
            StockLevel.warehouse_id == warehouse_id
        )
    ).first()
    return stock.quantity if stock else 0


def get_stock_levels(db: Session, product_id: int) -> list[StockLevel]:
    """Get all stock levels for a product across warehouses."""
    return db.query(StockLevel).filter(
        StockLevel.product_id == product_id
    ).all()


def create_batch(
    db: Session,
    product_id: int,
    warehouse_id: int,
    batch_number: str,
    quantity: int,
    expiry_date: datetime = None,
    user: User = None
) -> Batch:
    """Create a new batch/lot."""
    if user:
        require_permission(user, ROLE_STAFF)
    
    batch = Batch(
        product_id=product_id,
        warehouse_id=warehouse_id,
        batch_number=batch_number,
        quantity=quantity,
        expiry_date=expiry_date,
        received_date=datetime.utcnow()
    )
    db.add(batch)
    # Flush so batch.id is available for adjust_stock to update the specific batch
    db.flush()

    # Adjust stock and associate to the created batch
    adjust_stock(
        db=db,
        product_id=product_id,
        warehouse_id=warehouse_id,
        quantity=quantity,
        user=user,
        reason=f"Batch created: {batch_number}",
        batch_id=batch.id
    )
    
    db.commit()
    db.refresh(batch)
    logger.info(f"Created batch: {batch_number} for product {product_id}")
    return batch


def get_batches(db: Session, product_id: int = None, warehouse_id: int = None) -> list[Batch]:
    """Get batches, optionally filtered by product or warehouse."""
    q = db.query(Batch)
    if product_id:
        q = q.filter(Batch.product_id == product_id)
    if warehouse_id:
        q = q.filter(Batch.warehouse_id == warehouse_id)
    return q.order_by(Batch.expiry_date).all()


def get_low_stock_items(db: Session, threshold: int = None) -> list[dict]:
    """
    Get products with low stock levels.
    
    Returns:
        List of dicts with product info and stock levels
    """
    from inventory_app.config import LOW_STOCK_THRESHOLD
    
    if threshold is None:
        threshold = LOW_STOCK_THRESHOLD
    
    # Get all stock levels below threshold
    low_stocks = db.query(StockLevel).filter(
        StockLevel.quantity < threshold
    ).all()
    
    result = []
    for stock in low_stocks:
        product = db.query(Product).filter(Product.id == stock.product_id).first()
        if product and product.is_active:
            result.append({
                "product_id": product.id,
                "product_name": product.name,
                "sku": product.sku,
                "warehouse_id": stock.warehouse_id,
                "warehouse_name": db.query(Warehouse).filter(
                    Warehouse.id == stock.warehouse_id
                ).first().name if stock.warehouse_id else None,
                "quantity": stock.quantity,
                "threshold": threshold
            })
    
    return result


def get_all_warehouses(db: Session) -> list[Warehouse]:
    """Get all active warehouses."""
    return db.query(Warehouse).filter(Warehouse.is_active == True).order_by(Warehouse.name).all()


def create_warehouse(db: Session, name: str, location: str = None) -> Warehouse:
    """Create a new warehouse."""
    if db.query(Warehouse).filter(Warehouse.name == name).first():
        raise ValueError(f"Warehouse '{name}' already exists")
    
    warehouse = Warehouse(name=name, location=location, is_active=True)
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)
    return warehouse

