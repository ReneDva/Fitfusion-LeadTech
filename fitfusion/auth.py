"""Local email/username + password auth (salted hash, no external identity provider).

'Continue with Google / Apple' are shown as UI affordances per the product spec, but
real OAuth needs a registered app + redirect URI, which isn't meaningful for a
localhost-only app — see README roadmap. They're wired to a clear "not available
in local mode" message instead of silently doing nothing.
"""
import hashlib
import hmac
import os
import re

from fitfusion.db import create_user, find_user_by_login

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str, salt: bytes = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return salt.hex() + ":" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(expected.hex(), digest_hex)


def signup(email: str, username: str, name: str, password: str):
    """Returns (user_id, error_key_or_None)."""
    if not (email and username and name and password):
        return None, "fill_all_fields"
    if not EMAIL_RE.match(email):
        return None, "fill_all_fields"
    if find_user_by_login(email) or find_user_by_login(username):
        return None, "user_exists"
    user_id = create_user(email, username, name, hash_password(password))
    return user_id, None


def login(identifier: str, password: str):
    """Returns (user_row, error_key_or_None)."""
    if not (identifier and password):
        return None, "fill_all_fields"
    user = find_user_by_login(identifier)
    if not user or not verify_password(password, user["password_hash"]):
        return None, "invalid_credentials"
    return user, None
