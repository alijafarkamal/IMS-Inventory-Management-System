"""Notification model for in-app notifications (manager/admin view)."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from inventory_app.db.session import Base
from inventory_app.models.base import TimestampMixin


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    sender = Column(String(100), nullable=False)
    # recipients stored as CSV of roles/usernames (simple approach)
    recipients = Column(String(200), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
