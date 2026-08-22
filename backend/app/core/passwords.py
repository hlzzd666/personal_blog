import hashlib
import hmac
import secrets

PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
DEFAULT_PASSWORD_HASH_ITERATIONS = 600_000
SALT_BYTES = 16


def hash_password(password: str, iterations: int = DEFAULT_PASSWORD_HASH_ITERATIONS) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"{PASSWORD_HASH_ALGORITHM}${iterations}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, raw_iterations, salt, expected_digest = password_hash.split("$", maxsplit=3)
        iterations = int(raw_iterations)
    except ValueError:
        return False

    if algorithm != PASSWORD_HASH_ALGORITHM or iterations <= 0:
        return False

    actual_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return hmac.compare_digest(actual_digest, expected_digest)
