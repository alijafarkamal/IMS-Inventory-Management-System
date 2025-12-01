"""
Order processing orchestrator for SRP/DI.

Encapsulates order creation, FEFO batch consumption, stock adjustments,
commit/rollback, and logging. Public service delegates to this class.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Callable, List, Optional

from sqlalchemy.orm import Session

from inventory_app.models.order import Order, OrderItem
from inventory_app.models.stock import Batch
from inventory_app.models.user import User
from inventory_app.services.inventory_service import adjust_stock
from inventory_app.config import (
    ORDER_TYPE_SALE,
    ORDER_TYPE_PURCHASE,
    ORDER_TYPE_RETURN,
)
from inventory_app.utils.logging import logger


GenerateOrderNumberFn = Callable[[str, Session], str]
ActivityLoggerFn = Callable[[Session, User, str, str, int, str], None]


class OrderProcessor:
    def __init__(self, adjust_stock_fn: Callable = adjust_stock) -> None:
        self.adjust_stock = adjust_stock_fn

    def process(
        self,
        *,
        db: Session,
        generate_order_number_fn: GenerateOrderNumberFn,
        order_type: str,
        user: User,
        items: List[dict],
        notes: Optional[str] = None,
        customer_id: Optional[int] = None,
        activity_logger: Optional[ActivityLoggerFn] = None,
    ) -> Order:
        order_number = generate_order_number_fn(order_type, db)

        total_amount = Decimal("0.00")
        order_items: List[OrderItem] = []

        # Prepare items
        for item_data in items:
            quantity = int(item_data["quantity"])
            unit_price = Decimal(str(item_data["unit_price"]))
            subtotal = unit_price * quantity
            total_amount += subtotal

            order_items.append(
                OrderItem(
                    product_id=item_data["product_id"],
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                    warehouse_id=item_data["warehouse_id"],
                )
            )

        # Create order
        order = Order(
            order_number=order_number,
            order_type=order_type,
            user_id=user.id,
            customer_id=customer_id,
            total_amount=total_amount,
            status="Pending",
            notes=notes,
            order_date=datetime.utcnow(),
        )

        try:
            db.add(order)
            db.flush()

            # Insert items
            for oi in order_items:
                oi.order_id = order.id
                db.add(oi)
            db.flush()

            # Stock Adjustments
            for item_data, _oi in zip(items, order_items):
                quantity = int(item_data["quantity"])
                warehouse_id = item_data["warehouse_id"]
                product_id = item_data["product_id"]

                # SALE: FEFO strategy
                if order_type == ORDER_TYPE_SALE:
                    remaining = quantity
                    reason = f"Sale order {order_number}"

                    batches = (
                        db.query(Batch)
                        .filter(
                            Batch.product_id == product_id,
                            Batch.warehouse_id == warehouse_id,
                            Batch.quantity > 0,
                        )
                        .order_by(Batch.expiry_date)
                        .all()
                    )

                    for batch in batches:
                        if remaining <= 0:
                            break
                        take = min(batch.quantity, remaining)
                        if take <= 0:
                            continue

                        self.adjust_stock(
                            db=db,
                            product_id=product_id,
                            warehouse_id=warehouse_id,
                            quantity=-take,
                            user=user,
                            reason=f"{reason} - batch {batch.batch_number}",
                            batch_id=batch.id,
                        )
                        remaining -= take

                    # If still remaining after consuming all batches
                    if remaining > 0:
                        self.adjust_stock(
                            db=db,
                            product_id=product_id,
                            warehouse_id=warehouse_id,
                            quantity=-remaining,
                            user=user,
                            reason=reason,
                        )

                # PURCHASE: add to stock
                elif order_type == ORDER_TYPE_PURCHASE:
                    reason = f"Purchase order {order_number}"
                    self.adjust_stock(
                        db=db,
                        product_id=product_id,
                        warehouse_id=warehouse_id,
                        quantity=quantity,
                        user=user,
                        reason=reason,
                    )

                # RETURN: add stock back
                elif order_type == ORDER_TYPE_RETURN:
                    reason = f"Return order {order_number}"
                    self.adjust_stock(
                        db=db,
                        product_id=product_id,
                        warehouse_id=warehouse_id,
                        quantity=quantity,
                        user=user,
                        reason=reason,
                    )

                else:
                    logger.warning(
                        "Unknown order type for stock adjustment: %s",
                        order_type,
                    )

            # Finalize order
            order.status = "Completed"
            db.commit()
            db.refresh(order)

            logger.info(
                "Created %s order: %s by %s",
                order_type, order_number, user.username
            )

            # Activity logging
            if activity_logger:
                try:
                    activity_logger(
                        db,
                        user,
                        "ORDER_CREATE",
                        "Order",
                        order.id,
                        f"{order_type} {order_number}",
                    )
                except Exception:
                    pass  # Fail-safe logging

            return order

        except Exception:
            db.rollback()
            logger.exception("Failed to create order")
            raise  # NOTE: no unreachable code after this
