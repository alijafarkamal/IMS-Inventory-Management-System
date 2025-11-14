"""Stock, warehouse, and batch models."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from inventory_app.db.session import Base
from inventory_app.models.base import TimestampMixin


class Warehouse(Base, TimestampMixin):
    """Warehouse model."""
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    location = Column(String(200))
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    stock_levels = relationship("StockLevel", back_populates="warehouse")


class Batch(Base, TimestampMixin):
    """Batch/lot tracking model."""
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    batch_number = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    expiry_date = Column(DateTime)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    received_date = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="batches")
    warehouse = relationship("Warehouse")


class StockLevel(Base, TimestampMixin):
    """Stock level per product per warehouse."""
    __tablename__ = "stock_levels"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, default=0, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="stock_levels")
    warehouse = relationship("Warehouse", back_populates="stock_levels")

    # Unique constraint on product + warehouse
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )

