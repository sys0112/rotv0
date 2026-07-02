import contextlib
import os
import sqlite3
from pathlib import Path

DB_PATH = os.environ.get("ROTTO_DB_PATH", str(Path(__file__).parent / "lotto.db"))


def init_db():
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS draws (
                round  INTEGER PRIMARY KEY,
                date   TEXT NOT NULL,
                n1     INTEGER NOT NULL,
                n2     INTEGER NOT NULL,
                n3     INTEGER NOT NULL,
                n4     INTEGER NOT NULL,
                n5     INTEGER NOT NULL,
                n6     INTEGER NOT NULL,
                bonus  INTEGER NOT NULL
            )
        """)
        conn.commit()


def save_draw(round_no: int, date: str, numbers: list, bonus: int):
    if len(numbers) != 6:
        raise ValueError(f"expected 6 numbers, got {len(numbers)}")
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO draws VALUES (?,?,?,?,?,?,?,?,?)",
            (round_no, date, *numbers, bonus),
        )
        conn.commit()


def get_latest_round() -> int:
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute("SELECT MAX(round) FROM draws").fetchone()
    return row[0] or 0


def get_all_draws() -> list:
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM draws ORDER BY round").fetchall()
    return [
        {
            "round": r["round"],
            "date": r["date"],
            "numbers": [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]],
            "bonus": r["bonus"],
        }
        for r in rows
    ]


def init_pension_db():
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pension_draws (
                round   INTEGER PRIMARY KEY,
                date    TEXT NOT NULL,
                jo      INTEGER NOT NULL,
                number  TEXT NOT NULL
            )
        """)
        conn.commit()


def save_pension_draw(round_no: int, date: str, jo: int, number: str):
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO pension_draws VALUES (?,?,?,?)",
            (round_no, date, jo, number),
        )
        conn.commit()


def get_latest_pension_round() -> int:
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute("SELECT MAX(round) FROM pension_draws").fetchone()
    return row[0] or 0


def get_all_pension_draws() -> list:
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM pension_draws ORDER BY round"
        ).fetchall()
    return [
        {"round": r["round"], "date": r["date"], "jo": r["jo"], "number": r["number"]}
        for r in rows
    ]


import secrets as _secrets


def init_license_db():
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS license_keys (
                key        TEXT PRIMARY KEY,
                order_id   TEXT NOT NULL,
                issued_at  TEXT NOT NULL,
                note       TEXT NOT NULL DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_config (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.commit()


def save_license_key(key: str, order_id: str, note: str = "") -> None:
    from datetime import datetime, timezone
    issued_at = datetime.now(timezone.utc).isoformat()
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO license_keys VALUES (?,?,?,?)",
            (key, order_id, issued_at, note),
        )
        conn.commit()


def get_license_key(key: str) -> dict | None:
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM license_keys WHERE key=?", (key,)
        ).fetchone()
    if row is None:
        return None
    return {"key": row["key"], "order_id": row["order_id"],
            "issued_at": row["issued_at"], "note": row["note"]}


def get_all_license_keys() -> list:
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM license_keys ORDER BY issued_at DESC"
        ).fetchall()
    return [{"key": r["key"], "order_id": r["order_id"],
             "issued_at": r["issued_at"], "note": r["note"]} for r in rows]


def get_admin_password_hash() -> str | None:
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT value FROM admin_config WHERE key='admin_password_hash'"
        ).fetchone()
    return row[0] if row else None


def set_admin_password_hash(hash_value: str) -> None:
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO admin_config VALUES ('admin_password_hash', ?)",
            (hash_value,),
        )
        conn.commit()


def get_or_create_flask_secret() -> str:
    with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT value FROM admin_config WHERE key='flask_secret'"
        ).fetchone()
        if row:
            return row[0]
        secret = _secrets.token_hex(32)
        conn.execute(
            "INSERT INTO admin_config VALUES ('flask_secret', ?)", (secret,)
        )
        conn.commit()
        return secret
