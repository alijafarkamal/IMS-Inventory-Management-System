"""User and role models."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from inventory_app.db.session import Base
from inventory_app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """User model with role-based access."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, default="Staff")  # Admin, Manager, Staff
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    audit_logs = relationship("InventoryAudit", back_populates="user")


class Role(Base):
    """Role definitions (for future extensibility)."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), unique=True, nullable=False)
    description = Column(String(255))

