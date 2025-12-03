"""Notification domain interfaces for stock-level events."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from inventory_app.models.stock import StockLevel


class INotifier(ABC):
    """Notifier interface for decoupling notification implementations.

    Implementations should be lightweight and side-effecting (logging, email, webhooks).
    """

    @abstractmethod
    def notify_low_stock(self, stock: StockLevel, product: Optional[object], threshold: int) -> None:
        """Notify that a stock level fell below `threshold`.

        Args:
            stock: The `StockLevel` instance that is low.
            product: Optional product object for extra context (may be None).
            threshold: The numeric threshold considered as "low".
        """
        raise NotImplementedError()
