"""Order service for sales, purchases, and returns.

Thin wrapper delegating orchestration to `OrderProcessor` for SRP/DI.
Preserves existing behavior and commit/rollback semantics.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from inventory_app.models.order import Order
from inventory_app.models.user import User
from inventory_app.services.inventory_service import adjust_stock
from inventory_app.services.order_processor import OrderProcessor
from inventory_app.config import (
    ORDER_TYPE_SALE,
    ORDER_TYPE_PURCHASE,
    ORDER_TYPE_RETURN,
    ROLE_STAFF,
)
from inventory_app.services.auth_service import require_permission


def generate_order_number(order_type: str, db: Session) -> str:
    """Generate unique order number."""
    prefix = {
        ORDER_TYPE_SALE: "SO",
        ORDER_TYPE_PURCHASE: "PO",
        ORDER_TYPE_RETURN: "RT"
    }.get(order_type, "ORD")
    
    # Get highest sequence
    last_order = db.query(Order).filter(
        Order.order_number.like(f"{prefix}-%")
    ).order_by(Order.id.desc()).first()
    
    if last_order:
        try:
            seq = int(last_order.order_number.split("-")[-1])
            new_seq = seq + 1
        except (ValueError, IndexError):
            new_seq = 1
    else:
        new_seq = 1
    
    return f"{prefix}-{new_seq:05d}"


def create_order(
    db: Session,
    order_type: str,
    user: User,
    items: List[dict],
    notes: Optional[str] = None,
) -> Order:
    """Validate and delegate to `OrderProcessor` for orchestration."""
    require_permission(user, ROLE_STAFF)

    if order_type not in [ORDER_TYPE_SALE, ORDER_TYPE_PURCHASE, ORDER_TYPE_RETURN]:
        raise ValueError(f"Invalid order type: {order_type}")

    processor = OrderProcessor(adjust_stock_fn=adjust_stock)
    return processor.process(
        db=db,
        generate_order_number_fn=generate_order_number,
        order_type=order_type,
        user=user,
        items=items,
        notes=notes,
    )


def get_orders(
    db: Session,
    order_type: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Order]:
    """Get orders with optional filters."""
    q = db.query(Order)
    
    if order_type:
        q = q.filter(Order.order_type == order_type)
    if user_id:
        q = q.filter(Order.user_id == user_id)
    if start_date:
        q = q.filter(Order.order_date >= start_date)
    if end_date:
        q = q.filter(Order.order_date <= end_date)
    
    return q.order_by(Order.order_date.desc()).all()


def get_order(db: Session, order_id: int) -> Optional[Order]:
    """Get an order by ID."""
    return db.query(Order).filter(Order.id == order_id).first()

