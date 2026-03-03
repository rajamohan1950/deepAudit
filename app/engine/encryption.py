"""AES-256-GCM encryption helpers for data at rest.

Encryption standards
--------------------
* **Algorithm**: AES-256-GCM (authenticated encryption with associated data).
* **Key management**: In production, keys are sourced from AWS KMS via envelope
  encryption.  The helpers below accept raw 32-byte keys for local /
  integration-test use.
* **Transport security**: TLS 1.3 is enforced at the infrastructure layer
  (Render / AWS ALB) — this module only covers data-at-rest.
"""

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE_BYTES = 12  # 96-bit nonce recommended for AES-GCM
_KEY_BYTES = 32    # AES-256


def generate_key() -> bytes:
    """Return a cryptographically random 256-bit key."""
    return AESGCM.generate_key(bit_length=_KEY_BYTES * 8)


def encrypt_content(content: str | bytes, key: bytes) -> bytes:
    """Encrypt *content* with AES-256-GCM.

    Returns ``nonce || ciphertext`` (the first 12 bytes are the nonce).
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    nonce = os.urandom(_NONCE_BYTES)
    ciphertext = AESGCM(key).encrypt(nonce, content, None)
    return nonce + ciphertext


def decrypt_content(encrypted_bytes: bytes, key: bytes) -> bytes:
    """Decrypt data produced by :func:`encrypt_content`.

    Returns the original plaintext as ``bytes``.
    """
    nonce = encrypted_bytes[:_NONCE_BYTES]
    ciphertext = encrypted_bytes[_NONCE_BYTES:]
    return AESGCM(key).decrypt(nonce, ciphertext, None)
