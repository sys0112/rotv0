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
