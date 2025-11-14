"""Authentication and authorization service."""
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from inventory_app.models.user import User
from inventory_app.config import ROLE_ADMIN, ROLE_MANAGER, ROLE_STAFF
from inventory_app.utils.logging import logger

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticate a user.
    
    Returns:
        User object if authentication succeeds, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.warning(f"Authentication failed: user '{username}' not found")
        return None
    
    if not user.is_active:
        logger.warning(f"Authentication failed: user '{username}' is inactive")
        return None
    
    if not verify_password(password, user.password_hash):
        logger.warning(f"Authentication failed: invalid password for user '{username}'")
        return None
    
    logger.info(f"User '{username}' authenticated successfully")
    return user


def create_user(
    db: Session,
    username: str,
    password: str,
    email: str,
    full_name: str,
    role: str = ROLE_STAFF
) -> User:
    """Create a new user."""
    if db.query(User).filter(User.username == username).first():
        raise ValueError(f"Username '{username}' already exists")
    
    if db.query(User).filter(User.email == email).first():
        raise ValueError(f"Email '{email}' already exists")
    
    if role not in [ROLE_ADMIN, ROLE_MANAGER, ROLE_STAFF]:
        raise ValueError(f"Invalid role: {role}")
    
    user = User(
        username=username,
        password_hash=hash_password(password),
        email=email,
        full_name=full_name,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created user: {username} with role {role}")
    return user


def check_permission(user: User, required_role: str) -> bool:
    """
    Check if user has required permission.
    
    Role hierarchy: Admin > Manager > Staff
    """
    role_hierarchy = {ROLE_ADMIN: 3, ROLE_MANAGER: 2, ROLE_STAFF: 1}
    user_level = role_hierarchy.get(user.role, 0)
    required_level = role_hierarchy.get(required_role, 999)
    return user_level >= required_level


def require_permission(user: User, required_role: str):
    """Raise PermissionError if user doesn't have required permission."""
    if not check_permission(user, required_role):
        raise PermissionError(f"User '{user.username}' does not have required role: {required_role}")

