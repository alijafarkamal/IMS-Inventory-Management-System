"""Product and supplier models."""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from inventory_app.db.session import Base
from inventory_app.models.base import TimestampMixin


class Supplier(Base, TimestampMixin):
    """Supplier model."""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)

    # Relationships
    products = relationship("Product", back_populates="supplier")


class Category(Base, TimestampMixin):
    """Product category model."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    description = Column(Text)

    # Relationships
    products = relationship("Product", back_populates="category")


class Product(Base, TimestampMixin):
    """Product model."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text)

    # Relationships
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    stock_levels = relationship("StockLevel", back_populates="product")
    batches = relationship("Batch", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

