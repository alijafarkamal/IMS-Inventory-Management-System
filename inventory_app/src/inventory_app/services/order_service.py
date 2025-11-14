"""Order service for sales, purchases, and returns."""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from inventory_app.models.order import Order, OrderItem
from inventory_app.models.product import Product
from inventory_app.models.user import User
from inventory_app.services.inventory_service import adjust_stock
from inventory_app.config import ORDER_TYPE_SALE, ORDER_TYPE_PURCHASE, ORDER_TYPE_RETURN
from inventory_app.utils.logging import logger
from inventory_app.services.auth_service import require_permission
from inventory_app.config import ROLE_STAFF
from decimal import Decimal


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
    items: list[dict],
    notes: str = None
) -> Order:
    """
    Create an order (sale, purchase, or return).
    
    Args:
        db: Database session
        order_type: ORDER_TYPE_SALE, ORDER_TYPE_PURCHASE, or ORDER_TYPE_RETURN
        user: User creating the order
        items: List of dicts with keys: product_id, quantity, unit_price, warehouse_id
        notes: Optional notes
        
    Returns:
        Created Order
    """
    require_permission(user, ROLE_STAFF)
    
    if order_type not in [ORDER_TYPE_SALE, ORDER_TYPE_PURCHASE, ORDER_TYPE_RETURN]:
        raise ValueError(f"Invalid order type: {order_type}")
    
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
    try:
        for item_data, order_item in zip(items, order_items):
            quantity = item_data["quantity"]
            warehouse_id = item_data["warehouse_id"]
            product_id = item_data["product_id"]
            
            # Determine quantity change direction
            if order_type == ORDER_TYPE_SALE:
                # Sale reduces stock
                qty_change = -quantity
                reason = f"Sale order {order_number}"
            elif order_type == ORDER_TYPE_PURCHASE:
                # Purchase increases stock
                qty_change = quantity
                reason = f"Purchase order {order_number}"
            elif order_type == ORDER_TYPE_RETURN:
                # Return increases stock
                qty_change = quantity
                reason = f"Return order {order_number}"
            else:
                qty_change = 0
                reason = ""
            
            if qty_change != 0:
                adjust_stock(
                    db=db,
                    product_id=product_id,
                    warehouse_id=warehouse_id,
                    quantity=qty_change,
                    user=user,
                    reason=reason
                )
        
        # Mark order as completed
        order.status = "Completed"
        db.commit()
        db.refresh(order)
        
        logger.info(f"Created {order_type} order: {order_number} by {user.username}")
        return order
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create order: {e}")
        raise


def get_orders(
    db: Session,
    order_type: str = None,
    user_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None
) -> list[Order]:
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


def get_order(db: Session, order_id: int) -> Order:
    """Get an order by ID."""
    return db.query(Order).filter(Order.id == order_id).first()

