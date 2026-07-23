import bcrypt as _bcrypt


def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using bcrypt.

    Uses the bcrypt library directly (compatible with bcrypt>=4.0) to avoid
    the passlib 1.7.4 + bcrypt>=4.0 incompatibility where passlib calls the
    removed encode_password() helper.

    Args:
        password: The plain-text password to hash.

    Returns:
        The hashed password string (UTF-8 decoded bcrypt hash).
    """
    salt = _bcrypt.gensalt()
    hashed = _bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies a plain-text password against a hashed password.

    Args:
        password: The plain-text password to verify.
        hashed: The hashed password string to compare against.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return _bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
