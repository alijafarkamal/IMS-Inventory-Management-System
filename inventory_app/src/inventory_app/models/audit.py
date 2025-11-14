"""Audit log model for tracking inventory changes."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from inventory_app.db.session import Base


class InventoryAudit(Base):
    """Audit log for all inventory changes."""
    __tablename__ = "inventory_audit"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, STOCK_ADJUST, ORDER_CREATE, etc.
    entity_type = Column(String(50), nullable=False)  # Product, Order, StockLevel, etc.
    entity_id = Column(Integer, nullable=False)
    old_values = Column(JSON)  # JSON of old state
    new_values = Column(JSON)  # JSON of new state
    reason = Column(Text)
    timestamp = Column(DateTime, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

