"""Tests for asymmetric-cryptosystem signatures and canonical log hashing.

Covers the Electronic Transactions Act, 2063 "asymmetric cryptosystem"
primitives in app.crypto and the log-record binding in app.services.signing.
"""

from datetime import date, datetime, time, timezone

from app import crypto
from app.models.worklog import WorkLog
from app.models.user import User
from app.services import signing


# ---- Key generation + sign/verify round trip -------------------------------

def test_generate_keypair_returns_pem_and_fingerprint():
    public_pem, private_enc, fp = crypto.generate_keypair()
    assert "PUBLIC KEY" in public_pem
    assert "PRIVATE KEY" not in private_enc
    assert len(fp) == 64
    assert crypto.fingerprint(public_pem) == fp


def test_sign_and_verify_round_trip():
    public_pem, private_enc, _ = crypto.generate_keypair()
    content = "9f86d081884c7d659a2feaa0c55ad015"
    sig = crypto.sign(content, private_enc)
    assert crypto.verify(content, sig, public_pem)


def test_signature_fails_on_tampered_content():
    public_pem, private_enc, _ = crypto.generate_keypair()
    sig = crypto.sign("original-hash", private_enc)
    assert not crypto.verify("tampered-hash", sig, public_pem)


def test_signature_fails_with_wrong_public_key():
    public_pem, private_enc, _ = crypto.generate_keypair()
    other_pem, _, _ = crypto.generate_keypair()
    sig = crypto.sign("content", private_enc)
    assert not crypto.verify("content", sig, other_pem)


def test_signature_deterministic_given_same_key_and_content():
    _, private_enc, _ = crypto.generate_keypair()
    assert crypto.sign("same", private_enc) == crypto.sign("same", private_enc)


# ---- Private key at rest ----------------------------------------------------

def test_encrypted_private_key_does_not_leak_plaintext():
    _, private_enc, _ = crypto.generate_keypair()
    plain = crypto.decrypt_private_key(private_enc)
    assert "PRIVATE KEY" in plain
    assert "PRIVATE KEY" not in private_enc
    assert private_enc.isascii()


# ---- Canonical serialisation + content hash ---------------------------------

def test_canonical_json_is_deterministic_across_key_order():
    a = crypto.canonical_json({"b": 1, "a": {"x": 1, "y": [3, 2]}})
    b = crypto.canonical_json({"a": {"y": [3, 2], "x": 1}, "b": 1})
    assert a == b


def test_content_hash_changes_when_value_changes():
    h1 = crypto.content_hash({"hours": 8, "paid": 500})
    h2 = crypto.content_hash({"hours": 8, "paid": 500.01})
    assert h1 != h2
    assert len(h1) == 64


# ---- Work log canonical record ----------------------------------------------

def _log(**overrides) -> WorkLog:
    base = dict(
        id="11111111-1111-1111-1111-111111111111",
        employer_id="22222222-2222-2222-2222-222222222222",
        log_date=date(2026, 8, 5),
        report_time=time(9, 0),
        scheduled_end_time=time(17, 0),
        work_started_at=datetime(2026, 8, 5, 9, 0, tzinfo=timezone.utc),
        work_ended_at=datetime(2026, 8, 5, 17, 0, tzinfo=timezone.utc),
        breaks=[{"start": "2026-08-05T13:00:00Z", "end": "2026-08-05T13:30:00Z"}],
        overtime_minutes=0,
        paid_amount=None,
        promised_amount=800.0,
        piece_count=None,
        piece_rate=None,
        deductions=None,
        note="busy day",
    )
    base.update(overrides)
    return WorkLog(**base)


def test_worklog_content_hash_ignores_floating_point_drift():
    h1 = signing.log_content_hash(_log(paid_amount=500))
    h2 = signing.log_content_hash(_log(paid_amount=500.001))
    assert h1 == h2


def test_worklog_content_hash_changes_when_any_fact_changes():
    base = signing.log_content_hash(_log())
    assert signing.log_content_hash(_log(breaks=[])) != base
    assert signing.log_content_hash(_log(note=None)) != base
    assert signing.log_content_hash(_log(promised_amount=801)) != base


def test_verify_log_signature_validates_current_content():
    log = _log()
    user = User(username="w1", password_hash="x")
    content_hash = signing.log_content_hash(log)
    # Simulate the router path: keygen, sign the hash, store both.
    public_pem, private_enc, _ = crypto.generate_keypair()
    user.signing_public_key_pem = public_pem
    log.content_hash = content_hash
    log.employee_signature = crypto.sign(content_hash, private_enc)

    assert signing.verify_log_signature(log, user)


def test_verify_log_signature_detects_edited_record():
    log = _log()
    user = User(username="w1", password_hash="x")
    public_pem, private_enc, _ = crypto.generate_keypair()
    user.signing_public_key_pem = public_pem
    log.content_hash = signing.log_content_hash(log)
    log.employee_signature = crypto.sign(log.content_hash, private_enc)

    log.promised_amount = 9999  # edited after signing
    assert not signing.verify_log_signature(log, user)
