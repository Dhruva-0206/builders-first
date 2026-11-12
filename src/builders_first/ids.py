"""Pseudonymous developer ids. Raw GitHub logins never leave data/raw/."""
import hashlib


def dev_hash(login: str) -> str:
    """Stable id for a GitHub login: first 12 hex chars of SHA-256 of the lower-cased login."""
    return hashlib.sha256(login.strip().lower().encode("utf-8")).hexdigest()[:12]
