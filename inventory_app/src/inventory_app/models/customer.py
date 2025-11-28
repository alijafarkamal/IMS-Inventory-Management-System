"""Customer model for sales orders."""
from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from inventory_app.db.session import Base
from inventory_app.models.base import TimestampMixin


class Customer(Base, TimestampMixin):
    """Customer entity."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    orders = relationship("Order", back_populates="customer")
