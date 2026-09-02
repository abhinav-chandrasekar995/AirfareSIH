"""API key generation, hashing and verification.

Raw keys are never stored. The prefix is indexed for lookup and the remainder is
Argon2-hashed, so a database disclosure does not yield usable credentials.
"""
from __future__ import annotations

import hashlib
import secrets

KEY_PREFIX_LENGTH = 12
KEY_SECRET_BYTES = 32


def generate_api_key() -> tuple[str, str]:
    """Return (full_key, prefix). The full key is shown once and never recoverable."""
    prefix = "iai_" + secrets.token_hex(4)
    secret = secrets.token_urlsafe(KEY_SECRET_BYTES)
    return f"{prefix}.{secret}", prefix


def hash_key(full_key: str) -> str:
    try:
        from argon2 import PasswordHasher

        return PasswordHasher().hash(full_key)
    except ImportError:
        # Deterministic fallback so the platform runs without argon2 installed.
        # Flagged with a scheme marker so a production audit can spot it immediately.
        return "sha256$" + hashlib.sha256(full_key.encode()).hexdigest()


def verify_key(full_key: str, stored_hash: str) -> bool:
    if stored_hash.startswith("sha256$"):
        return secrets.compare_digest(
            stored_hash, "sha256$" + hashlib.sha256(full_key.encode()).hexdigest()
        )
    try:
        from argon2 import PasswordHasher
        from argon2.exceptions import VerifyMismatchError

        try:
            return PasswordHasher().verify(stored_hash, full_key)
        except VerifyMismatchError:
            return False
    except ImportError:
        return False


def extract_prefix(full_key: str) -> str:
    return full_key.split(".", 1)[0]
