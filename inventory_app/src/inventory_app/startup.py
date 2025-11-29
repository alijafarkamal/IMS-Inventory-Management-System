"""Application startup bootstrap.

Responsibilities:
- Initialize database tables on first run.
- Ensure default admin user exists.

Keeps side-effects out of UI classes to respect SRP at the composition root.
"""
from inventory_app.db.session import init_db, get_db_session
from inventory_app.models.user import User
from inventory_app.services.auth_service import create_user
from inventory_app.utils.logging import logger


def bootstrap():
    """Initialize infrastructure and seed minimal required data."""
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed initializing database: {e}")

    db = None
    try:
        db = get_db_session()
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            try:
                create_user(
                    db,
                    username="admin",
                    password="admin123",
                    email="admin@inventory.local",
                    full_name="Administrator",
                    role="Admin",
                )
                logger.info("Default admin user created")
            except Exception as e:
                logger.error(f"Failed creating default admin: {e}")
        else:
            logger.info("Default admin user ensured")
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass
