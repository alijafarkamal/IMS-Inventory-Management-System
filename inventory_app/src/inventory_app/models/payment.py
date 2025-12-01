"""Payment models with method polymorphism (initial minimal schema)."""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from inventory_app.db.session import Base
from inventory_app.models.base import TimestampMixin


class PaymentMethod(Base, TimestampMixin):
    """Base payment method (joined-table inheritance-ready in future)."""
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    # type of method: 'Card' | 'Cash' | 'Banking'
    method_type = Column(String(20), nullable=False, index=True)

    # Generic display fields (optional, non-sensitive)
    display_name = Column(String(50))  # e.g., 'Visa **** 4242', 'Cash', 'Bank Transfer'

    # Relationships
    payments = relationship("Payment", back_populates="method")


class Payment(Base, TimestampMixin):
    """Payment record linked to an order."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    method_id = Column(Integer, ForeignKey("payment_methods.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)

    # statuses: 'Authorized' | 'Captured' | 'Refunded' | 'Failed'
    status = Column(String(20), default="Authorized", nullable=False)

    # external reference (gateway transaction ID, receipt no., etc.)
    reference = Column(String(100))

    # Relationships
    method = relationship("PaymentMethod", back_populates="payments")
    order = relationship("Order", back_populates="payments")
