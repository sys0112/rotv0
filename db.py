import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).parent / "lotto.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()


def save_draw(round_no: int, date: str, numbers: list, bonus: int):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO draws VALUES (?,?,?,?,?,?,?,?,?)",
        (round_no, date, numbers[0], numbers[1], numbers[2],
         numbers[3], numbers[4], numbers[5], bonus),
    )
    conn.commit()
    conn.close()


def get_latest_round() -> int:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT MAX(round) FROM draws").fetchone()
    conn.close()
    return row[0] or 0


def get_all_draws() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM draws ORDER BY round").fetchall()
    conn.close()
    return [
        {
            "round": r["round"],
            "date": r["date"],
            "numbers": [r["n1"], r["n2"], r["n3"], r["n4"], r["n5"], r["n6"]],
            "bonus": r["bonus"],
        }
        for r in rows
    ]
