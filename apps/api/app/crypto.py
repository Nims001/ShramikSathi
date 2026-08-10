"""Asymmetric-cryptosystem digital signatures for the dual-consensus work log.

Nepal's Electronic Transactions Act, 2063 (2008) §2 defines a *digital
signature* as authentication of an electronic record using an **asymmetric
cryptosystem** and the signer's **private key**, verifiable with the
corresponding **public key**. This module implements exactly that:

* RSA-2048 key pairs (the scheme recognised by Nepal's e-governance /
  digital-signature ecosystem), SHA-256, PKCS#1 v1.5.
* Private keys are never stored as plaintext: they are encrypted at rest with
  AES-256-GCM keyed from the server `SIGNING_SECRET`, so a leaked database is
  not enough to forge a signature.
* A deterministic canonical serialisation + SHA-256 hash of the log record,
  so any later tampering breaks the stored signatures.

`canonical_json` / `content_hash` operate on plain dicts so callers decide
which fields constitute the signed record.
"""

import base64
import hashlib
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import settings

_KEY_SIZE = 2048
_PBKDF2_ITERATIONS = 240_000
_SALT = b"shramiksathi-signing-v1"


# ---- Canonical serialisation + content hash -------------------------------


def canonical_json(data: dict) -> str:
    """Deterministic JSON: sorted keys, compact separators, UTF-8-safe.

    Two records that differ only in key order or whitespace hash identically;
    any real change in value changes the hash.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_hash(data: dict) -> str:
    """SHA-256 hex digest of the canonical serialisation of `data`."""
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


# ---- Key pair generation + at-rest encryption ------------------------------


def _encryption_key() -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(), length=32, salt=_SALT, iterations=_PBKDF2_ITERATIONS
    )
    return kdf.derive(settings.signing_secret.encode("utf-8"))


def generate_keypair() -> tuple[str, str, str]:
    """Return (public_pem, private_pem_encrypted, fingerprint_hex)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=_KEY_SIZE)
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("ascii")
    return public_pem, encrypt_private_key(private_pem), fingerprint(public_pem)


def encrypt_private_key(private_pem: str) -> str:
    """AES-256-GCM encrypt a PEM private key; returns base64(nonce + ciphertext)."""
    key = _encryption_key()
    aesgcm = AESGCM(key)
    nonce = hashlib.sha256(private_pem.encode("utf-8")).digest()[:12]
    ciphertext = aesgcm.encrypt(nonce, private_pem.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext).decode("ascii")


def decrypt_private_key(private_pem_encrypted: str) -> str:
    """Decrypt a private key produced by :func:`encrypt_private_key`."""
    raw = base64.b64decode(private_pem_encrypted.encode("ascii"))
    nonce, ciphertext = raw[:12], raw[12:]
    plaintext = AESGCM(_encryption_key()).decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def fingerprint(public_pem: str) -> str:
    """Stable fingerprint (SHA-256 hex) of a public key, for display/audit."""
    return hashlib.sha256(public_pem.encode("ascii")).hexdigest()


def _load_private_key(private_pem: str) -> RSAPrivateKey:
    return serialization.load_pem_private_key(private_pem.encode("utf-8"), password=None)


def _load_public_key(public_pem: str) -> RSAPublicKey:
    return serialization.load_pem_public_key(public_pem.encode("ascii"))


# ---- Signing / verification ------------------------------------------------


def sign(content: str, private_pem_encrypted: str) -> str:
    """Sign `content` (e.g. a content hash hex) with the encrypted private key.

    Returns base64 PKCS#1 v1.5 / SHA-256 signature.
    """
    private_key = _load_private_key(decrypt_private_key(private_pem_encrypted))
    signature = private_key.sign(
        content.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256()
    )
    return base64.b64encode(signature).decode("ascii")


def verify(content: str, signature: str, public_pem: str) -> bool:
    """Verify a base64 signature against `content` and the signer's public key."""
    try:
        public_key = _load_public_key(public_pem)
        public_key.verify(
            base64.b64decode(signature.encode("ascii")),
            content.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False
