"""Order models for sales, purchases, and returns."""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from inventory_app.db.session import Base
from inventory_app.models.base import TimestampMixin


class Order(Base, TimestampMixin):
    """Order model (sales, purchase, return)."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    order_type = Column(String(20), nullable=False)  # Sale, Purchase, Return
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    status = Column(String(20), default="Pending", nullable=False)  # Pending, Completed, Cancelled
    notes = Column(Text)
    order_date = Column(DateTime, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # For sales orders

    # Relationships
    user = relationship("User")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order")


class OrderItem(Base, TimestampMixin):
    """Order line items."""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")
    warehouse = relationship("Warehouse")

