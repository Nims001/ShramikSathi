"""Password hashing and session-token utilities.

No external crypto dependency: PBKDF2-HMAC-SHA256 via stdlib hashlib with a
per-password random salt, formatted as `pbkdf2_sha256$<iterations>$<salt>$<hash>`.
Session tokens are 32 random bytes from `secrets`.
"""

import hashlib
import hmac
import secrets

_ITERATIONS = 240_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${_ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iterations, salt, expected = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        ).hex()
        return hmac.compare_digest(digest, expected)
    except (ValueError, TypeError):
        return False


def generate_token() -> str:
    return secrets.token_urlsafe(32)


# ---- Share codes (employer portal) ------------------------------------------
# Codes use an unambiguous alphabet (no 0/O/1/I) and are stored only as a
# SHA-256 hash, so a leaked database cannot be used to impersonate a worker.

_CODE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def generate_share_code() -> str:
    """Return a code like ``SRM-KX9F-7Q2C`` (12 chars, 3×4 groups)."""
    raw = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(12))
    return f"{raw[0:4]}-{raw[4:8]}-{raw[8:12]}"


def normalize_share_code(code: str) -> str:
    clean = "".join(ch for ch in code.upper() if ch.isalnum())
    return "-".join(clean[i : i + 4] for i in range(0, len(clean), 4))


def hash_share_code(code: str) -> str:
    return hashlib.sha256(normalize_share_code(code).encode("utf-8")).hexdigest()


def verify_share_code(code: str, stored: str) -> bool:
    return hmac.compare_digest(hash_share_code(code), stored)
