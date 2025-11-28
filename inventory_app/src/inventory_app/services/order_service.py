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
    customer_id: Optional[int] = None,
) -> Order:
    """Validate and delegate to `OrderProcessor` for orchestration."""
    require_permission(user, ROLE_STAFF)

    if order_type not in [ORDER_TYPE_SALE, ORDER_TYPE_PURCHASE, ORDER_TYPE_RETURN]:
        raise ValueError(f"Invalid order type: {order_type}")
<<<<<<< HEAD
    
    # Generate order number
    order_number = generate_order_number(order_type, db)
    
    # Calculate total
    total_amount = Decimal("0.00")
    order_items = []
    
    for item_data in items:
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        if not product:
            raise ValueError(f"Product {item_data['product_id']} not found")
        
        quantity = item_data["quantity"]
        unit_price = Decimal(str(item_data["unit_price"]))
        subtotal = unit_price * quantity
        total_amount += subtotal
        
        order_item = OrderItem(
            product_id=item_data["product_id"],
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
            warehouse_id=item_data["warehouse_id"]
        )
        order_items.append(order_item)
    
    
    # Create order and perform stock adjustments
    try:
        with db.begin():
            # Create order
            order = Order(
                order_number=order_number,
                order_type=order_type,
                user_id=user.id,
                total_amount=total_amount,
                status="Pending",
                notes=notes,
                order_date=datetime.utcnow()
            )
            db.add(order)
            db.flush()  # Get order ID

        # Add items
        for item in order_items:
            item.order_id = order.id
            db.add(item)

        db.flush()

        # Adjust stock based on order type
        for item_data, order_item in zip(items, order_items):
            quantity = item_data["quantity"]
            warehouse_id = item_data["warehouse_id"]
            product_id = item_data["product_id"]

            # Determine quantity change direction
            if order_type == ORDER_TYPE_SALE:
                # Sale reduces stock. Prefer consuming from batches (FEFO) if available.
                remaining = quantity
                reason = f"Sale order {order_number}"

                # Get batches for this product/warehouse with available quantity, ordered by expiry (earliest first)
                batches = db.query(Batch).filter(
                    Batch.product_id == product_id,
                    Batch.warehouse_id == warehouse_id,
                    Batch.quantity > 0
                ).order_by(Batch.expiry_date).all()

                for batch in batches:
                    if remaining <= 0:
                        break
                    take = min(batch.quantity, remaining)
                    if take <= 0:
                        continue
                    # Adjust stock and decrease specific batch
                    adjust_stock(
                        db=db,
                        product_id=product_id,
                        warehouse_id=warehouse_id,
                        quantity=-take,
                        user=user,
                        reason=f"{reason} - batch {batch.batch_number}",
                        batch_id=batch.id
                    )
                    remaining -= take

                # If still remaining (no batches or insufficient batch qty), adjust general stock
                if remaining > 0:
                    adjust_stock(
                        db=db,
                        product_id=product_id,
                        warehouse_id=warehouse_id,
                        quantity=-remaining,
                        user=user,
                        reason=reason
                    )

            elif order_type == ORDER_TYPE_PURCHASE:
                # Purchase increases stock
                qty_change = quantity
                reason = f"Purchase order {order_number}"
                adjust_stock(
                    db=db,
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    quantity=qty_change,
                    user=user,
                    reason=reason
                )

            elif order_type == ORDER_TYPE_RETURN:
                # Return increases stock
                qty_change = quantity
                reason = f"Return order {order_number}"
                adjust_stock(
                    db=db,
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    quantity=qty_change,
                    user=user,
                    reason=reason
                )
            else:
                # Unknown type: skip
                logger.warning(f"Unknown order type for stock adjustment: {order_type}")

        # Mark order as completed
        order.status = "Completed"
        
        # Commit the transaction
        db.commit()
        db.refresh(order)
        logger.info(f"Created {order_type} order: {order_number} by {user.username}")
        try:
            log_activity(db, user, action="ORDER_CREATE", entity_type="Order", entity_id=order.id, details=f"{order_type} {order_number}")
        except Exception:
            pass
        return order

    except Exception as e:
        # Rollback on error
        db.rollback()
        logger.error(f"Failed to create order: {e}")
        raise
=======

    processor = OrderProcessor(adjust_stock_fn=adjust_stock)
    # Optional activity logger: try to import if available
    activity_logger = None
    try:
        # Optional dependency: only used if present in the codebase
        from inventory_app.services.activity_service import log_activity as _log_activity  # type: ignore
        activity_logger = _log_activity
    except Exception:
        activity_logger = None
    return processor.process(
        db=db,
        generate_order_number_fn=generate_order_number,
        order_type=order_type,
        user=user,
        items=items,
        notes=notes,
        customer_id=customer_id,
        activity_logger=activity_logger,
    )
>>>>>>> 97fef683a5de477951478023c7ab2c1b1760a180


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

