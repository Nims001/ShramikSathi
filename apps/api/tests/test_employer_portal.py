"""Tests for the employer portal's share-code helpers and role guard."""

import pytest

from app.routers.employer_portal import _require_employer
from app.models.user import User
from fastapi import HTTPException
from app.security import generate_share_code, hash_share_code, normalize_share_code, verify_share_code


# ---- Share code generation & hashing --------------------------------------

def test_generate_share_code_format():
    code = generate_share_code()
    parts = code.split("-")
    assert len(parts) == 3
    assert all(len(p) == 4 for p in parts)
    assert code == code.upper()


def test_generate_share_code_avoids_ambiguous_characters():
    for _ in range(50):
        assert not any(c in code for code in [generate_share_code() for _ in range(1)] for c in "0O1I")


def test_normalize_share_code():
    assert normalize_share_code("a8b9-c7d6-e5f4") == "A8B9-C7D6-E5F4"
    assert normalize_share_code(" a8b9 c7d6 e5f4 ") == "A8B9-C7D6-E5F4"
    assert normalize_share_code("a8b9c7d6e5f4") == "A8B9-C7D6-E5F4"


def test_hash_and_verify_share_code():
    code = generate_share_code()
    digest = hash_share_code(code)
    assert digest != code
    assert len(digest) == 64
    assert verify_share_code(code, digest)
    assert not verify_share_code(generate_share_code(), digest)


def test_hash_is_unique_per_code():
    codes = {generate_share_code() for _ in range(20)}
    digests = {hash_share_code(c) for c in codes}
    assert len(codes) == len(digests)


def test_hash_never_contains_plaintext_code():
    for _ in range(10):
        code = generate_share_code()
        assert code not in hash_share_code(code)


# ---- Role guard ------------------------------------------------------------

def test_require_employer_accepts_employer():
    user = User(role="employer")
    _require_employer(user)  # should not raise


def test_require_employer_rejects_worker():
    user = User(role="worker")
    with pytest.raises(HTTPException) as exc:
        _require_employer(user)
    assert exc.value.status_code == 403
