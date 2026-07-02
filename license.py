import hmac
import hashlib
import os
from pathlib import Path

import db

_SECRET = b"L0tt0-An4lyz3r-x9Km2024-zPqR7vT"

_DEFAULT_LICENSE_PATH = str(Path(__file__).parent / "license.key")


def _get_license_path() -> str:
    return os.environ.get("ROTTO_LICENSE_PATH", _DEFAULT_LICENSE_PATH)


def generate_key(order_id: str) -> str:
    raw = hmac.new(_SECRET, order_id.strip().encode(), digestmod=hashlib.sha256).hexdigest()
    h = raw[:16].upper()
    return f"LOTO-{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"


def validate_key(key: str) -> bool:
    normalized = key.strip().upper()
    return db.get_license_key(normalized) is not None


def read_license_file() -> str | None:
    path = _get_license_path()
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None


def write_license_file(key: str) -> None:
    path = _get_license_path()
    Path(path).write_text(key.strip().upper(), encoding="utf-8")


def is_licensed() -> bool:
    key = read_license_file()
    if not key:
        return False
    return validate_key(key)
