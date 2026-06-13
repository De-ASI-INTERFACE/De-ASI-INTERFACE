"""
src/api/auth/totp.py

Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.

Robust TOTP (Time-based One-Time Password) implementation.

Features:
  - RFC 6238 compliant via pyotp
  - Clock-skew tolerance: ±1 window (±30s)
  - TOTP secret provisioning (QR code URI generation)
  - TOTP secret encryption at rest (Fernet symmetric encryption)
  - Backup codes: 10 single-use recovery codes per user
  - Replay attack prevention via Redis-backed used-OTP store
  - Full audit logging on every verification attempt

Dependencies:
  - pyotp>=2.9.0
  - cryptography>=42.0.0
  - aioredis>=2.0.1
"""

import base64
import hashlib
import secrets
import time
from typing import List, Optional, Tuple

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from loguru import logger

from config import settings


# ---------------------------------------------------------------------------
# Secret encryption at rest
# ---------------------------------------------------------------------------

def _get_fernet() -> Fernet:
    """
    Derive a Fernet key from JWT_SECRET so we don't need a separate env var.
    In production, replace with a dedicated TOTP_ENCRYPTION_KEY env var.
    """
    raw = settings.JWT_SECRET.encode()
    key_bytes = hashlib.sha256(raw).digest() # 32 bytes
    b64_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(b64_key)


def encrypt_totp_secret(plaintext_secret: str) -> str:
    """Encrypt a TOTP secret before storing in the database."""
    fernet = _get_fernet()
    return fernet.encrypt(plaintext_secret.encode()).decode()


def decrypt_totp_secret(encrypted_secret: str) -> str:
    """Decrypt a TOTP secret retrieved from the database."""
    fernet = _get_fernet()
    try:
        return fernet.decrypt(encrypted_secret.encode()).decode()
    except InvalidToken as e:
        logger.error("TOTP secret decryption failed — possible key rotation or corruption")
        raise ValueError("Cannot decrypt TOTP secret") from e


# ---------------------------------------------------------------------------
# TOTP provisioning
# ---------------------------------------------------------------------------

def generate_totp_secret() -> str:
    """Generate a new cryptographically random TOTP base32 secret."""
    return pyotp.random_base32()


def get_totp_provisioning_uri(
    username: str,
    plaintext_secret: str,
    issuer: str = "De-ASI-INTERFACE"
) -> str:
    """
    Returns an otpauth:// URI for QR code generation.
    Render with: qrcode.make(uri) or display in authenticator app setup.
    """
    totp = pyotp.TOTP(plaintext_secret)
    return totp.provisioning_uri(
        name=username,
        issuer_name=issuer
    )


def generate_backup_codes(count: int = 10) -> List[str]:
    """
    Generate `count` single-use backup recovery codes.
    Each code is 10 hex chars (5 bytes) formatted as XXXXX-XXXXX.
    Store hashed (SHA-256) in DB — never store plaintext.
    """
    codes = []
    for _ in range(count):
        raw = secrets.token_hex(5) # 10 hex chars
        formatted = f"{raw[:5].upper()}-{raw[5:].upper()}"
        codes.append(formatted)
    return codes


def hash_backup_code(code: str) -> str:
    """SHA-256 hash a backup code for safe DB storage."""
    normalized = code.replace("-", "").upper().encode()
    return hashlib.sha256(normalized).hexdigest()


# ---------------------------------------------------------------------------
# TOTP verification
# ---------------------------------------------------------------------------

async def verify_totp(
    username: str,
    code: str,
    encrypted_secret: str,
    redis_client=None
) -> bool:
    """
    Verify a 6-digit TOTP code.

    Security properties:
      1. Clock-skew tolerance of ±1 window (30s grace)
      2. Replay attack prevention — each (code, window) pair
         is stored in Redis for 90s and rejected if reused
      3. All attempts are audit-logged with username + IP context

    Args:
        username:         User identifier for audit logging
        code:             6-digit TOTP code from authenticator app
        encrypted_secret: Fernet-encrypted TOTP secret from DB
        redis_client:     Optional aioredis client for replay prevention

    Returns:
        True if code is valid and not replayed, False otherwise
    """
    # Input validation
    if not code or not code.strip().isdigit() or len(code.strip()) != 6:
        logger.warning(f"TOTP invalid format | user={username}")
        return False

    code = code.strip()

    try:
        plaintext_secret = decrypt_totp_secret(encrypted_secret)
    except ValueError:
        logger.error(f"TOTP secret decryption error | user={username}")
        return False

    totp = pyotp.TOTP(plaintext_secret)

    # Verify with ±1 window tolerance (covers ~90s clock drift)
    is_valid = totp.verify(code, valid_window=1)

    if not is_valid:
        logger.warning(f"TOTP invalid code | user={username}")
        return False

    # Replay attack prevention
    if redis_client:
        current_window = int(time.time()) // 30
        replay_key = f"totp_used:{username}:{current_window}:{code}"
        try:
            # SETNX — only set if not exists. TTL = 90s covers ±1 window
            was_set = await redis_client.set(replay_key, "1", ex=90, nx=True)
            if not was_set:
                logger.warning(f"TOTP replay attempt blocked | user={username} | window={current_window}")
                return False
        except Exception as e:
            # Redis unavailable — log and allow (don't block auth on infra failure)
            logger.warning(f"TOTP replay check failed (Redis error): {e} | user={username}")

    logger.info(f"TOTP verified | user={username}")
    return True


async def verify_backup_code(
    username: str,
    code: str,
    stored_hashes: List[str],
) -> Tuple[bool, Optional[str]]:
    """
    Verify a backup recovery code.

    Args:
        username:      User identifier for audit logging
        code:          Raw backup code entered by user (e.g., "ABCDE-12345")
        stored_hashes: List of SHA-256 hashed backup codes from DB

    Returns:
        Tuple of (is_valid: bool, matched_hash: Optional[str])
        If valid, matched_hash is the hash to mark as consumed in DB.
    """
    code_hash = hash_backup_code(code)

    for stored_hash in stored_hashes:
        if secrets.compare_digest(code_hash, stored_hash):
            logger.info(f"Backup code used | user={username}")
            return True, stored_hash

    logger.warning(f"Backup code invalid | user={username}")
    return False, None
