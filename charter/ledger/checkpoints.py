from __future__ import annotations

import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def generate_keypair() -> tuple[bytes, bytes]:
    key = Ed25519PrivateKey.generate()
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def sign(private_pem: bytes, data: bytes) -> bytes:
    key = serialization.load_pem_private_key(private_pem, password=None)
    assert isinstance(key, Ed25519PrivateKey)
    return key.sign(data)


def verify_signature(public_pem: bytes, signature: bytes, data: bytes) -> bool:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    pub = serialization.load_pem_public_key(public_pem)
    assert isinstance(pub, Ed25519PublicKey)
    try:
        pub.verify(signature, data)
        return True
    except InvalidSignature:
        return False


def compute_merkle_root(hashes: list[str]) -> str:
    combined = "|".join(sorted(hashes))
    return hashlib.sha256(combined.encode()).hexdigest()
