"""Inventory domain components for SRP/DI.

Contains small focused classes used by `inventory_service`:
- StockRepository: data access for stock levels and batches
- AuditFactory: builds audit records for stock adjustments
- InventoryAdjuster: applies stock change rules and creates audits

Public service functions should delegate to these to improve structure
without changing external APIs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
import json

from sqlalchemy.orm import Session

from inventory_app.models.stock import StockLevel, Batch
from inventory_app.models.product import Product
from inventory_app.config import LOW_STOCK_THRESHOLD
from inventory_app.services.notification_domain import INotifier
from inventory_app.services.notification_store import create_notification
from inventory_app.models.audit import InventoryAudit
from inventory_app.models.user import User


class StockRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_stock_level(self, product_id: int, warehouse_id: int) -> Optional[StockLevel]:
        return (
            self.db.query(StockLevel)
            .filter(StockLevel.product_id == product_id, StockLevel.warehouse_id == warehouse_id)
            .first()
        )

    def create_stock_level(self, product_id: int, warehouse_id: int) -> StockLevel:
        stock = StockLevel(product_id=product_id, warehouse_id=warehouse_id, quantity=0)
        self.db.add(stock)
        return stock

    def find_batch(self, batch_id: int) -> Optional[Batch]:
        return self.db.query(Batch).filter(Batch.id == batch_id).first()

    def add(self, entity) -> None:
        self.db.add(entity)

    def flush(self) -> None:
        self.db.flush()

    def refresh(self, entity) -> None:
        try:
            self.db.refresh(entity)
        except Exception:
            pass


class AuditFactory:
    def build_stock_adjust_audit(
        self,
        *,
        user_id: int,
        stock_id: int,
        old_quantity: int,
        new_quantity: int,
        reason: str,
    ) -> InventoryAudit:
        return InventoryAudit(
            user_id=user_id,
            action="STOCK_ADJUST",
            entity_type="StockLevel",
            entity_id=stock_id,
            old_values=json.dumps({"quantity": old_quantity}),
            new_values=json.dumps({"quantity": new_quantity}),
            reason=reason,
            timestamp=datetime.utcnow(),
        )


class InventoryAdjuster:
    def __init__(self, repo: StockRepository, audit_factory: AuditFactory, notifier: Optional[INotifier] = None) -> None:
        self.repo = repo
        self.audit_factory = audit_factory
        # Optional notifier adhering to the INotifier interface (dependency inversion)
        self.notifier = notifier

    def adjust_stock(
        self,
        *,
        product_id: int,
        warehouse_id: int,
        quantity: int,
        user: User,
        reason: str,
        batch_id: Optional[int] = None,
    ) -> StockLevel:
        stock = self.repo.find_stock_level(product_id, warehouse_id)
        old_quantity = stock.quantity if stock else 0

        if not stock:
            stock = self.repo.create_stock_level(product_id, warehouse_id)

        new_quantity = stock.quantity + quantity
        if new_quantity < 0:
            raise ValueError(
                f"Insufficient stock. Available: {stock.quantity}, Requested: {abs(quantity)}"
            )
        stock.quantity = new_quantity

        if batch_id:
            batch = self.repo.find_batch(batch_id)
            if batch:
                new_batch_qty = batch.quantity + quantity
                if new_batch_qty < 0:
                    raise ValueError(
                        f"Insufficient batch stock for batch {batch.batch_number}. "
                        f"Available: {batch.quantity}, Requested: {abs(quantity)}"
                    )
                batch.quantity = new_batch_qty

        self.repo.flush()

        audit = self.audit_factory.build_stock_adjust_audit(
            user_id=user.id,
            stock_id=stock.id,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            reason=reason,
        )
        self.repo.add(audit)

        self.repo.flush()
        self.repo.refresh(stock)
        # Notify if below global low-stock threshold (non-intrusive, only if notifier provided)
        try:
            threshold = LOW_STOCK_THRESHOLD
        except Exception:
            threshold = None

        if self.notifier and threshold is not None and new_quantity < threshold:
            # fetch product info for context if available
            try:
                product = self.repo.db.query(Product).filter(Product.id == product_id).first()
            except Exception:
                product = None
            try:
                self.notifier.notify_low_stock(stock=stock, product=product, threshold=threshold)
            except Exception:
                # Do not let notifier failures affect inventory operations
                pass
            # Also create an in-app notification targeted to Manager and Admin (non-email)
            try:
                # Build a concise message
                title = f"Low stock: {getattr(product, 'name', f'Product {product_id}') if product else f'Product {product_id}'}"
                message = f"Stock for product {getattr(product, 'name', product_id)} (id={product_id}) is {new_quantity} in warehouse {warehouse_id}. Threshold: {threshold}."
                # recipients: Manager and Admin roles
                create_notification(self.repo.db, title=title, message=message, sender=str(user.username), recipients=["Manager", "Admin"])
            except Exception:
                # swallow DB notification errors
                pass

        return stock
