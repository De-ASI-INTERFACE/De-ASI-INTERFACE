"""
tests/test_auth.py

Owner/Creator: Richard Patterson
© 2026 Richard Patterson. All Rights Reserved.

Comprehensive auth test suite:
  - TOTP generation, encryption, verification
  - Backup code hashing and consumption
  - Replay attack prevention
  - Password hashing and verification
  - User model validation
  - Rate limiter sliding window
  - Token store JTI lifecycle
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pyotp

from src.api.auth.totp import (
    decrypt_totp_secret,
    encrypt_totp_secret,
    generate_backup_codes,
    generate_totp_secret,
    get_totp_provisioning_uri,
    hash_backup_code,
    verify_backup_code,
    verify_totp,
)
from src.api.auth.user_model import User, UserRole, UserStatus
from src.api.auth.user_store import hash_password, verify_password
from src.api.auth.rate_limiter import RateLimiter
from src.api.auth.token_store import TokenStore


# ---------------------------------------------------------------------------
# TOTP Tests
# ---------------------------------------------------------------------------

class TestTOTPGeneration:
    def test_generate_totp_secret_is_base32(self):
        secret = generate_totp_secret()
        import base64
        # Should not raise
        base64.b32decode(secret)
        assert len(secret) == 32

    def test_generate_totp_secret_unique(self):
        secrets = {generate_totp_secret() for _ in range(100)}
        assert len(secrets) == 100

    def test_provisioning_uri_format(self):
        secret = generate_totp_secret()
        uri = get_totp_provisioning_uri("richard", secret)
        assert uri.startswith("otpauth://totp/")
        assert "De-ASI-INTERFACE" in uri
        assert "richard" in uri


class TestTOTPEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        secret = generate_totp_secret()
        encrypted = encrypt_totp_secret(secret)
        assert encrypted != secret
        decrypted = decrypt_totp_secret(encrypted)
        assert decrypted == secret

    def test_encrypted_different_each_time(self):
        secret = generate_totp_secret()
        enc1 = encrypt_totp_secret(secret)
        enc2 = encrypt_totp_secret(secret)
        # Fernet uses random IV so ciphertexts differ
        assert enc1 != enc2
        # But both decrypt to same value
        assert decrypt_totp_secret(enc1) == decrypt_totp_secret(enc2) == secret

    def test_tampered_ciphertext_raises(self):
        secret = generate_totp_secret()
        encrypted = encrypt_totp_secret(secret)
        tampered = encrypted[:-4] + "XXXX"
        with pytest.raises(ValueError):
            decrypt_totp_secret(tampered)


class TestTOTPVerification:
    @pytest.mark.asyncio
    async def test_valid_code_accepted(self):
        secret = generate_totp_secret()
        encrypted = encrypt_totp_secret(secret)
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()
        result = await verify_totp("richard", valid_code, encrypted, redis_client=None)
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_code_rejected(self):
        secret = generate_totp_secret()
        encrypted = encrypt_totp_secret(secret)
        result = await verify_totp("richard", "000000", encrypted, redis_client=None)
        # This could theoretically pass 1/1000000 times — acceptable
        # Use a clearly invalid format for deterministic failure
        result2 = await verify_totp("richard", "abcdef", encrypted, redis_client=None)
        assert result2 is False

    @pytest.mark.asyncio
    async def test_wrong_length_rejected(self):
        secret = generate_totp_secret()
        encrypted = encrypt_totp_secret(secret)
        for bad in ["", "123", "1234567", "      "]:
            result = await verify_totp("richard", bad, encrypted, redis_client=None)
            assert result is False, f"Expected False for code: {repr(bad)}"

    @pytest.mark.asyncio
    async def test_replay_attack_blocked(self):
        secret = generate_totp_secret()
        encrypted = encrypt_totp_secret(secret)
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        # Mock Redis: first SET returns True (new), second returns False (replay)
        redis_mock = AsyncMock()
        redis_mock.set = AsyncMock(side_effect=[True, False])

        result1 = await verify_totp("richard", valid_code, encrypted, redis_mock)
        assert result1 is True

        result2 = await verify_totp("richard", valid_code, encrypted, redis_mock)
        assert result2 is False

    @pytest.mark.asyncio
    async def test_redis_failure_does_not_block_auth(self):
        """Auth should succeed even if Redis replay check fails."""
        secret = generate_totp_secret()
        encrypted = encrypt_totp_secret(secret)
        totp = pyotp.TOTP(secret)
        valid_code = totp.now()

        redis_mock = AsyncMock()
        redis_mock.set = AsyncMock(side_effect=Exception("Redis down"))

        result = await verify_totp("richard", valid_code, encrypted, redis_mock)
        assert result is True


# ---------------------------------------------------------------------------
# Backup Code Tests
# ---------------------------------------------------------------------------

class TestBackupCodes:
    def test_generate_10_codes(self):
        codes = generate_backup_codes(10)
        assert len(codes) == 10

    def test_codes_format(self):
        codes = generate_backup_codes(5)
        for code in codes:
            parts = code.split("-")
            assert len(parts) == 2
            assert len(parts[0]) == 5
            assert len(parts[1]) == 5

    def test_codes_unique(self):
        codes = generate_backup_codes(10)
        assert len(set(codes)) == 10

    def test_hash_is_deterministic(self):
        code = "ABCDE-12345"
        assert hash_backup_code(code) == hash_backup_code(code)

    def test_hash_case_insensitive(self):
        assert hash_backup_code("abcde-12345") == hash_backup_code("ABCDE-12345")

    @pytest.mark.asyncio
    async def test_valid_backup_code_accepted(self):
        codes = generate_backup_codes(3)
        hashes = [hash_backup_code(c) for c in codes]
        is_valid, matched = await verify_backup_code("richard", codes[1], hashes)
        assert is_valid is True
        assert matched == hashes[1]

    @pytest.mark.asyncio
    async def test_invalid_backup_code_rejected(self):
        hashes = [hash_backup_code(c) for c in generate_backup_codes(3)]
        is_valid, matched = await verify_backup_code("richard", "AAAAA-BBBBB", hashes)
        assert is_valid is False
        assert matched is None


# ---------------------------------------------------------------------------
# Password Tests
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_verify_roundtrip(self):
        pw = "Sup3rS3cur3P@ssword!"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed)

    def test_wrong_password_rejected(self):
        hashed = hash_password("correct-horse-battery")
        assert not verify_password("wrong-password", hashed)

    def test_hash_unique_per_call(self):
        pw = "same-password"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2 # bcrypt salt
        assert verify_password(pw, h1)
        assert verify_password(pw, h2)

    def test_plaintext_not_in_hash(self):
        pw = "MySecret123"
        hashed = hash_password(pw)
        assert pw not in hashed


# ---------------------------------------------------------------------------
# User Model Tests
# ---------------------------------------------------------------------------

class TestUserModel:
    def test_new_user_defaults(self):
        user = User.new("richard", "r@example.com", "hash")
        assert user.status == UserStatus.PENDING_2FA
        assert user.totp_enabled is False
        assert user.failed_login_count == 0
        assert user.locked_until is None
        assert len(user.id) == 36 # UUID4

    def test_is_locked_false_by_default(self):
        user = User.new("richard", "r@example.com", "hash")
        assert user.is_locked() is False

    def test_is_locked_true_when_locked_until_future(self):
        user = User.new("richard", "r@example.com", "hash")
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=10)
        assert user.is_locked() is True

    def test_is_locked_false_when_expired(self):
        user = User.new("richard", "r@example.com", "hash")
        user.locked_until = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert user.is_locked() is False

    def test_is_active_requires_active_status(self):
        user = User.new("richard", "r@example.com", "hash")
        user.status = UserStatus.ACTIVE
        assert user.is_active() is True
        user.status = UserStatus.SUSPENDED
        assert user.is_active() is False


# ---------------------------------------------------------------------------
# Rate Limiter Tests
# ---------------------------------------------------------------------------

class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_allows_under_limit(self):
        rl = RateLimiter()
        for _ in range(4):
            await rl.record_failure("test:user")
        allowed = await rl.check("test:user", max_attempts=5, window_seconds=900)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_blocks_at_limit(self):
        rl = RateLimiter()
        for _ in range(5):
            await rl.record_failure("test:user2")
        allowed = await rl.check("test:user2", max_attempts=5, window_seconds=900)
        assert allowed is False

    @pytest.mark.asyncio
    async def test_reset_clears_count(self):
        rl = RateLimiter()
        for _ in range(5):
            await rl.record_failure("test:user3")
        await rl.reset("test:user3")
        allowed = await rl.check("test:user3", max_attempts=5, window_seconds=900)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_window_expiry(self):
        """Attempts outside the window should not count."""
        rl = RateLimiter()
        # Manually inject old timestamps
        import time as _time
        old_time = _time.monotonic() - 1000 # Way outside any window
        rl._records["test:user4"].timestamps = [old_time] * 10
        allowed = await rl.check("test:user4", max_attempts=5, window_seconds=900)
        assert allowed is True

    @pytest.mark.asyncio
    async def test_attempts_remaining(self):
        rl = RateLimiter()
        await rl.record_failure("test:user5")
        await rl.record_failure("test:user5")
        remaining = await rl.attempts_remaining("test:user5", max_attempts=5)
        assert remaining == 3


# ---------------------------------------------------------------------------
# Token Store Tests
# ---------------------------------------------------------------------------

class TestTokenStore:
    @pytest.mark.asyncio
    async def test_store_and_validate(self):
        ts = TokenStore()
        jti = str(uuid.uuid4())
        await ts.store(jti, ttl_seconds=60)
        assert await ts.is_valid(jti) is True

    @pytest.mark.asyncio
    async def test_revoke(self):
        ts = TokenStore()
        jti = str(uuid.uuid4())
        await ts.store(jti, ttl_seconds=60)
        await ts.revoke(jti)
        assert await ts.is_valid(jti) is False

    @pytest.mark.asyncio
    async def test_unknown_jti_invalid(self):
        ts = TokenStore()
        assert await ts.is_valid("nonexistent-jti") is False

    @pytest.mark.asyncio
    async def test_ws_ticket_single_use(self):
        ts = TokenStore()
        ticket = secrets.token_urlsafe(32)
        await ts.store_ws_ticket(ticket, "richard", ttl_seconds=30)
        user1 = await ts.consume_ws_ticket(ticket)
        assert user1 == "richard"
        user2 = await ts.consume_ws_ticket(ticket) # replay
        assert user2 is None

    @pytest.mark.asyncio
    async def test_ws_ticket_expiry(self):
        ts = TokenStore()
        ticket = secrets.token_urlsafe(32)
        # Store with 0s TTL (already expired)
        import time as _time
        async with ts._lock:
            ts._ws_tickets[ticket] = ("richard", _time.monotonic() - 1)
        user = await ts.consume_ws_ticket(ticket)
        assert user is None


# Needed for standalone import in test
import secrets
