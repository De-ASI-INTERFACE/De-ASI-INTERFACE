"""
src/api/auth/user_model.py

Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.

User domain model and data transfer objects.

Separates DB row representation from business logic.
All password and TOTP fields are handled as encrypted/hashed
values — plaintext never persists beyond the request lifecycle.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class UserRole(str, Enum):
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_2FA = "pending_2fa" # Registered but hasn't completed 2FA setup


@dataclass
class User:
    """
    Core user domain model.

    Security notes:
      - password_hash: bcrypt hash only — never store plaintext
      - totp_secret_enc: Fernet-encrypted TOTP secret
      - backup_code_hashes: SHA-256 hashes of backup codes — never plaintext
      - All datetimes are UTC-aware
    """
    id: str # UUID4
    username: str
    email: str
    password_hash: str # bcrypt
    role: UserRole
    status: UserStatus
    totp_secret_enc: Optional[str] # Fernet-encrypted
    totp_enabled: bool
    backup_code_hashes: List[str] # SHA-256 hashes
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]
    failed_login_count: int
    locked_until: Optional[datetime]

    @classmethod
    def new(
        cls,
        username: str,
        email: str,
        password_hash: str,
        role: UserRole = UserRole.TRADER,
    ) -> "User":
        """Factory method for new user creation."""
        now = datetime.now(timezone.utc)
        return cls(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=password_hash,
            role=role,
            status=UserStatus.PENDING_2FA,
            totp_secret_enc=None,
            totp_enabled=False,
            backup_code_hashes=[],
            created_at=now,
            updated_at=now,
            last_login_at=None,
            failed_login_count=0,
            locked_until=None,
        )

    def is_locked(self) -> bool:
        """Returns True if account is under a lockout period."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and not self.is_locked()


@dataclass
class UserPublic:
    """Safe public representation — never includes secrets."""
    id: str
    username: str
    email: str
    role: UserRole
    status: UserStatus
    totp_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    @classmethod
    def from_user(cls, user: "User") -> "UserPublic":
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=user.status,
            totp_enabled=user.totp_enabled,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
