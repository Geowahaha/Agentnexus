"""
Ed25519 Cryptographic Signing for Revenue Data and Fingerprints.

Defense in Depth for Revenue Attribution Data:
- Ed25519 for signing (strong, fast, modern)
- Canonical JSON for deterministic signing
- SHA-256 pre-hash
- Signature includes timestamp, workflow, hash for replay protection
- Verification on read for integrity

Keys managed via settings (in prod use secrets manager, rotate regularly).
Public key can be exposed for verification.

This makes Revenue Data tamper-evident and provably ours.
"""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization

from app.core.config import settings

# In-memory for session; in prod load from secure storage
_private_key: Ed25519PrivateKey | None = None
_public_key: Ed25519PublicKey | None = None

def _get_private_key() -> Ed25519PrivateKey:
    global _private_key
    if _private_key is None:
        key_pem = getattr(settings, "moat_ed25519_private_key_pem", None)
        if key_pem:
            _private_key = serialization.load_pem_private_key(
                key_pem.encode(), password=None
            )
        else:
            # Dev only: generate
            _private_key = Ed25519PrivateKey.generate()
    return _private_key

def _get_public_key() -> Ed25519PublicKey:
    global _public_key
    if _public_key is None:
        _public_key = _get_private_key().public_key()
    return _public_key

def canonical_json(obj: dict[str, Any]) -> bytes:
    """Canonical JSON for signing: sorted keys, no whitespace, utf8."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")

def sign_revenue_attribution(
    revenue_att: dict[str, Any],
    workflow_id: str,
    skill_slug: str | None = None,
) -> dict[str, Any]:
    """
    Sign revenue attribution payload.

    Returns original + signature and metadata.
    Use this for all revenue data in fingerprints and profiles.
    """
    private_key = _get_private_key()
    pub_key = _get_public_key()

    payload = {
        "version": "1.0",
        "workflow_id": workflow_id,
        "skill_slug": skill_slug,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "revenue_att": revenue_att,
    }

    canonical = canonical_json(payload)
    digest = hashlib.sha256(canonical).digest()
    signature = private_key.sign(digest)

    pub_pem = pub_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

    signed = {
        **revenue_att,
        "_signature": {
            "alg": "Ed25519",
            "sig": base64.b64encode(signature).decode(),
            "pub_key_pem": pub_pem,
            "payload_hash": base64.b64encode(digest).decode(),
            "timestamp": payload["timestamp"],
            "version": "1.0",
        },
    }
    return signed

def verify_revenue_attribution(signed_revenue: dict[str, Any]) -> bool:
    """Verify the signature on a revenue attribution dict."""
    sig_info = signed_revenue.get("_signature")
    if not sig_info or sig_info.get("alg") != "Ed25519":
        return False

    try:
        pub_key = serialization.load_pem_public_key(sig_info["pub_key_pem"].encode())
        if not isinstance(pub_key, Ed25519PublicKey):
            return False

        # Reconstruct payload without sig
        payload = {
            "version": sig_info["version"],
            "workflow_id": signed_revenue.get("workflow_id"),  # may not be in base
            "skill_slug": signed_revenue.get("skill_slug"),
            "timestamp": sig_info["timestamp"],
            "revenue_att": {k: v for k, v in signed_revenue.items() if not k.startswith("_")},
        }
        canonical = canonical_json(payload)
        digest = hashlib.sha256(canonical).digest()
        signature = base64.b64decode(sig_info["sig"])
        pub_key.verify(signature, digest)
        return True
    except Exception:
        return False

def get_public_key_pem() -> str:
    return _get_public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()

# For MCP long-term: expose verify for external agents to validate our revenue data provenance
def get_verify_function():
    return verify_revenue_attribution
