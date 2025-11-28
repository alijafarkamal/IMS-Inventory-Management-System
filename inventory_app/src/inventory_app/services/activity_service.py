"""Activity logging service."""
from datetime import datetime
from sqlalchemy.orm import Session
from inventory_app.models.audit import ActivityLog
from inventory_app.models.user import User


def log_activity(
    db: Session,
    user: User,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    details: str | None = None,
):
    entry = ActivityLog(
        user_id=user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        timestamp=datetime.utcnow(),
    )
    db.add(entry)
    db.commit()
