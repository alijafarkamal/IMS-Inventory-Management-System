"""Authentication and authorization service.

Thin wrappers delegating to domain classes for SRP/DI.
Public API preserved.
"""
from sqlalchemy.orm import Session
from inventory_app.models.user import User
from inventory_app.services.activity_service import log_activity
from inventory_app.config import ROLE_ADMIN, ROLE_MANAGER, ROLE_STAFF
from inventory_app.utils.logging import logger
from inventory_app.services.auth_domain import PasswordHasher, PermissionChecker, Authenticator

# Lightweight singletons for reuse
_hasher = PasswordHasher()
_perm = PermissionChecker()


def hash_password(password: str) -> str:
    """Hash a password (delegates to PasswordHasher)."""
    return _hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (delegates to PasswordHasher)."""
    return _hasher.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticate a user.
    
    Returns:
        User object if authentication succeeds, None otherwise
    """
    # Use Authenticator for SRP; preserve original logging side-effect
    user = Authenticator(db, _hasher).authenticate(username, password)
    if user:
        try:
            log_activity(db, user, action="LOGIN", entity_type="User", entity_id=user.id, details="User logged in")
        except Exception:
            pass
    return user


def create_user(
    db: Session,
    username: str,
    password: str,
    role: str = ROLE_STAFF
) -> User:
    """Create a new user with username/password/role only."""
    if db.query(User).filter(User.username == username).first():
        raise ValueError(f"Username '{username}' already exists")

    if role not in [ROLE_ADMIN, ROLE_MANAGER, ROLE_STAFF]:
        raise ValueError(f"Invalid role: {role}")

    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created user: {username} with role {role}")
    return user


def check_permission(user: User, required_role: str) -> bool:
    """Check if user has required permission (delegates to PermissionChecker)."""
    return _perm.has_permission(user, required_role)


def require_permission(user: User, required_role: str):
    """Raise PermissionError if user doesn't have required permission (delegates)."""
    _perm.require(user, required_role)

