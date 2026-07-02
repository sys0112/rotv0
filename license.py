import hmac
import hashlib
import os
import secrets as _secrets
from pathlib import Path

_SECRET = b"L0tt0-An4lyz3r-x9Km2024-zPqR7vT"
_DEFAULT_LICENSE_PATH = str(Path(__file__).parent / "license.key")


def _get_license_path() -> str:
    return os.environ.get("ROTTO_LICENSE_PATH", _DEFAULT_LICENSE_PATH)


def generate_key(order_id: str = "") -> str:
    nonce = _secrets.token_hex(4).upper()
    mac = hmac.new(_SECRET, nonce.encode(), hashlib.sha256).hexdigest()[:8].upper()
    h = nonce + mac
    return f"LOTO-{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"


def validate_key(key: str) -> bool:
    key = key.strip().upper()
    if not key.startswith("LOTO-"):
        return False
    body = key[5:].replace("-", "")
    if len(body) != 16:
        return False
    nonce = body[:8]
    expected_mac = hmac.new(_SECRET, nonce.encode(), hashlib.sha256).hexdigest()[:8].upper()
    return body[8:] == expected_mac


def read_license_file() -> str | None:
    try:
        return Path(_get_license_path()).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None


def write_license_file(key: str) -> None:
    Path(_get_license_path()).write_text(key.strip().upper(), encoding="utf-8")


def is_licensed() -> bool:
    key = read_license_file()
    if not key:
        return False
    return validate_key(key)
