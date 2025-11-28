"""Auth domain components for SRP/DI.

- PasswordHasher: wraps passlib context for hash/verify
- PermissionChecker: encapsulates role hierarchy checks
- Authenticator: looks up user and verifies password
"""
from __future__ import annotations

from typing import Optional, Dict
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from inventory_app.models.user import User
from inventory_app.config import ROLE_ADMIN, ROLE_MANAGER, ROLE_STAFF
from inventory_app.utils.logging import logger


class PasswordHasher:
    def __init__(self, schemes: list[str] | None = None, deprecated: str = "auto") -> None:
        self._ctx = CryptContext(schemes=schemes or ["bcrypt"], deprecated=deprecated)

    def hash(self, password: str) -> str:
        return self._ctx.hash(password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._ctx.verify(plain_password, hashed_password)


class PermissionChecker:
    def __init__(self, role_hierarchy: Optional[Dict[str, int]] = None) -> None:
        self._hierarchy = role_hierarchy or {ROLE_ADMIN: 3, ROLE_MANAGER: 2, ROLE_STAFF: 1}

    def has_permission(self, user: User, required_role: str) -> bool:
        user_level = self._hierarchy.get(user.role, 0)
        required_level = self._hierarchy.get(required_role, 999)
        return user_level >= required_level

    def require(self, user: User, required_role: str) -> None:
        if not self.has_permission(user, required_role):
            raise PermissionError(f"User '{user.username}' does not have required role: {required_role}")


class Authenticator:
    def __init__(self, db: Session, hasher: PasswordHasher) -> None:
        self.db = db
        self.hasher = hasher

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            logger.warning(f"Authentication failed: user '{username}' not found")
            return None
        if not user.is_active:
            logger.warning(f"Authentication failed: user '{username}' is inactive")
            return None
        if not self.hasher.verify(password, user.password_hash):
            logger.warning(f"Authentication failed: invalid password for user '{username}'")
            return None
        logger.info(f"User '{username}' authenticated successfully")
        return user
