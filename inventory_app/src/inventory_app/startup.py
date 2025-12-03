"""Application startup bootstrap.

Responsibilities:
- Initialize database tables on first run.
- Ensure default admin user exists.

Keeps side-effects out of UI classes to respect SRP at the composition root.
"""
from inventory_app.db.session import init_db, get_db_session
from inventory_app.models.user import User
from inventory_app.services.auth_service import create_user
from inventory_app.config import ROLE_MANAGER, ROLE_STAFF
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

        # Ensure default manager user
        manager = db.query(User).filter(User.username == "manager").first()
        if not manager:
            try:
                create_user(
                    db,
                    username="manager",
                    password="manager123",
                    email="manager@inventory.local",
                    full_name="Manager",
                    role=ROLE_MANAGER,
                )
                logger.info("Default manager user created")
            except Exception as e:
                logger.error(f"Failed creating default manager: {e}")
        else:
            logger.info("Default manager user ensured")

        # Ensure default staff user
        staff = db.query(User).filter(User.username == "staff").first()
        if not staff:
            try:
                create_user(
                    db,
                    username="staff",
                    password="staff123",
                    email="staff@inventory.local",
                    full_name="Staff Member",
                    role=ROLE_STAFF,
                )
                logger.info("Default staff user created")
            except Exception as e:
                logger.error(f"Failed creating default staff: {e}")
        else:
            logger.info("Default staff user ensured")
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass
