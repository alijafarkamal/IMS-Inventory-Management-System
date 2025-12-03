"""Service to create and retrieve in-app notifications stored in DB."""
from __future__ import annotations
from typing import List
from sqlalchemy.orm import Session
from inventory_app.models.notification import Notification
from inventory_app.utils.logging import logger
from datetime import datetime


def create_notification(db: Session, title: str, message: str, sender: str, recipients: List[str]) -> Notification:
    """Create a notification targeted to recipients (roles or usernames).

    Recipients is a list of strings (e.g. ["Manager", "Admin"]).
    """
    notif = Notification(
        title=title,
        message=message,
        sender=sender,
        recipients=",".join(recipients),
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(notif)
    try:
        db.commit()
        db.refresh(notif)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create notification: {e}")
        raise
    return notif


def get_notifications_for_user(db: Session, user) -> List[Notification]:
    """Return notifications visible to a given `user`.

    A notification is visible if the user's role or username appears in the recipients CSV.
    """
    q = db.query(Notification).order_by(Notification.created_at.desc())
    results = []
    for n in q.all():
        recipients = [r.strip() for r in (n.recipients or "").split(",") if r.strip()]
        if user.role in recipients or user.username in recipients:
            results.append(n)
    return results


def mark_notification_read(db: Session, notification_id: int) -> None:
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if not n:
        return
    n.is_read = True
    try:
        db.commit()
    except Exception:
        db.rollback()
