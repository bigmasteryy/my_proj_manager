from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta


PASSWORD_ITERATIONS = 120_000
SESSION_DURATION_DAYS = 30


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return f"{PASSWORD_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        iterations_text, salt_hex, digest_hex = password_hash.split("$", 2)
        iterations = int(iterations_text)
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        iterations,
    )
    return secrets.compare_digest(digest.hex(), digest_hex)


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_expiry_from_now() -> datetime:
    return datetime.now() + timedelta(days=SESSION_DURATION_DAYS)
