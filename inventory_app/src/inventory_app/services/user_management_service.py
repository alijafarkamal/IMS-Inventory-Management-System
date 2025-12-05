"""User management service for admin operations."""
from sqlalchemy.orm import Session
from inventory_app.models.user import User
from inventory_app.services.auth_service import hash_password, create_user
from inventory_app.config import ROLE_ADMIN, ROLE_MANAGER, ROLE_STAFF
from inventory_app.utils.logging import logger


def get_all_users(db: Session) -> list[User]:
    """Get all users."""
    return db.query(User).order_by(User.username).all()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def create_new_user(
    db: Session,
    username: str,
    password: str,
    role: str = ROLE_STAFF
) -> User:
    """Create a new user (admin operation)."""
    # Validate role (admins cannot be created from UI/service)
    if role not in [ROLE_MANAGER, ROLE_STAFF]:
        raise ValueError(f"Invalid role: {role}. Must be one of: {ROLE_MANAGER}, {ROLE_STAFF}")
    
    # Check if username already exists
    if get_user_by_username(db, username):
        raise ValueError(f"Username '{username}' already exists")
    
    # Create user with minimal fields
    return create_user(db, username=username, password=password, role=role)


def update_user(
    db: Session,
    user_id: int,
    username: str = None,
    email: str = None,
    full_name: str = None,
    role: str = None,
    is_active: bool = None
) -> User:
    """Update user details (admin operation)."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    # Validate role if provided (do not allow setting ROLE_ADMIN via UI/service)
    if role and role not in [ROLE_MANAGER, ROLE_STAFF]:
        raise ValueError(f"Invalid role: {role}. Must be one of: {ROLE_MANAGER}, {ROLE_STAFF}")
    # Protect default admin from role changes
    if role and user.id == 1:
        raise ValueError("Cannot change the default admin's role")
    
    # Check if new username already exists (skip if same username)
    if username and username != user.username:
        if db.query(User).filter(User.username == username).first():
            raise ValueError(f"Username '{username}' already exists")

    # Check if new email already exists (skip if same email)
    if email and email != user.email:
        if db.query(User).filter(User.email == email).first():
            raise ValueError(f"Email '{email}' already exists")
    
    # Update fields
    if username:
        user.username = username
    if email:
        user.email = email
    if full_name:
        user.full_name = full_name
    if role:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    
    db.commit()
    db.refresh(user)
    logger.info(f"Updated user: {user.username}")
    return user


def reset_password(db: Session, user_id: int, new_password: str) -> User:
    """Reset user password (admin operation)."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    logger.info(f"Password reset for user: {user.username}")
    return user


def deactivate_user(db: Session, user_id: int) -> User:
    """Deactivate a user (soft delete)."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    if user.id == 1:  # Prevent deactivating first admin
        raise ValueError("Cannot deactivate the default admin user")
    
    user.is_active = False
    db.commit()
    db.refresh(user)
    logger.info(f"Deactivated user: {user.username}")
    return user


def activate_user(db: Session, user_id: int) -> User:
    """Activate a user."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    user.is_active = True
    db.commit()
    db.refresh(user)
    logger.info(f"Activated user: {user.username}")
    return user


def delete_user(db: Session, user_id: int) -> None:
    """Hard delete a user. Prefer deactivate_user to avoid FK issues."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    if user.id == 1 or user.role == "Admin":
        raise ValueError("Cannot delete the default admin user")

    # Safety: if activity log entries exist, recommend deactivation
    from inventory_app.models.audit import ActivityLog
    has_activity = db.query(ActivityLog).filter(ActivityLog.user_id == user_id).first() is not None
    if has_activity:
        raise ValueError("User has activity logs; deactivate instead of delete")

    db.delete(user)
    db.commit()
    logger.info(f"Deleted user: {user.username}")


def deactivate_user(db: Session, user_id: int) -> None:
    """Soft deactivate a user to preserve FK integrity."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")
    if user.id == 1:
        raise ValueError("Cannot deactivate the default admin user")
    user.is_active = False
    db.commit()
    logger.info(f"Deactivated user: {user.username}")
    db.delete(user)
    db.commit()
    logger.info(f"Deleted user: {user.username}")