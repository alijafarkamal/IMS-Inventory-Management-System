"""Concrete notifier implementations (log, email placeholder)."""
from __future__ import annotations
from typing import Optional

from inventory_app.services.notification_domain import INotifier
from inventory_app.models.stock import StockLevel
from inventory_app.utils.logging import logger


class LogNotifier(INotifier):
    """Simple notifier that writes low-stock events to the app logger."""

    def notify_low_stock(self, stock: StockLevel, product: Optional[object], threshold: int) -> None:
        prod_str = f"{product.id} - {getattr(product, 'name', '')}" if product else f"product={stock.product_id}"
        logger.warning(
            f"Low stock alert: {prod_str} in warehouse {stock.warehouse_id} has {stock.quantity} < {threshold}"
        )


class EmailNotifier(INotifier):
    """Placeholder for an email notifier — left intentionally minimal and easily extendable.

    In production, implement sending via SMTP, SES, or another provider and keep this class
    focused only on the transport. This keeps SRP and open/closed principle intact.
    """

    def __init__(self, sender: str = None, recipients: list[str] | None = None) -> None:
        self.sender = sender
        self.recipients = recipients or []

    def notify_low_stock(self, stock: StockLevel, product: Optional[object], threshold: int) -> None:
        # Minimal placeholder behavior: log the intent to email; real implementations send email.
        prod_str = f"{product.id} - {getattr(product, 'name', '')}" if product else f"product={stock.product_id}"
        logger.info(
            f"(Email) Low stock notification planned: {prod_str} in warehouse {stock.warehouse_id} has {stock.quantity} < {threshold}; recipients={self.recipients}"
        )
