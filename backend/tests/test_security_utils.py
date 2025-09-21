"""Tests for security helper functions."""

from app.utils.security import get_password_hash, verify_password


def test_verify_password_with_valid_hash() -> None:
    """A valid bcrypt hash should validate successfully."""
    hashed = get_password_hash("s3cret-pass")
    assert verify_password("s3cret-pass", hashed)


def test_verify_password_with_invalid_hash_returns_false() -> None:
    """Malformed stored hashes should not raise errors during verification."""
    # When legacy data contains plaintext values, passlib raises ``ValueError``.
    # The helper should gracefully treat this as a failed verification.
    assert not verify_password("irrelevant", "plaintext-password")


def test_verify_password_with_none_hash_returns_false() -> None:
    """Missing hashes should be treated as a failed verification."""
    assert not verify_password("irrelevant", None)  # type: ignore[arg-type]
