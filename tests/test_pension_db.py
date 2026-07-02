import contextlib
import sqlite3
import pytest
import db


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    yield


def test_init_pension_db_creates_table():
    db.init_pension_db()
    with contextlib.closing(sqlite3.connect(db.DB_PATH)) as conn:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()]
    assert "pension_draws" in tables


def test_save_and_get_pension_draws():
    db.init_pension_db()
    db.save_pension_draw(1, "2024-01-05", 3, "415207")
    draws = db.get_all_pension_draws()
    assert len(draws) == 1
    assert draws[0] == {"round": 1, "date": "2024-01-05", "jo": 3, "number": "415207"}


def test_get_latest_pension_round_empty():
    db.init_pension_db()
    assert db.get_latest_pension_round() == 0


def test_get_latest_pension_round():
    db.init_pension_db()
    db.save_pension_draw(1, "2024-01-05", 3, "415207")
    db.save_pension_draw(5, "2024-02-02", 2, "123456")
    assert db.get_latest_pension_round() == 5


def test_save_pension_draw_duplicate_ignored():
    db.init_pension_db()
    db.save_pension_draw(1, "2024-01-05", 3, "415207")
    db.save_pension_draw(1, "2024-01-05", 3, "999999")
    assert len(db.get_all_pension_draws()) == 1


def test_get_all_pension_draws_ordered():
    db.init_pension_db()
    db.save_pension_draw(3, "2024-01-19", 1, "111111")
    db.save_pension_draw(1, "2024-01-05", 3, "415207")
    draws = db.get_all_pension_draws()
    assert [d["round"] for d in draws] == [1, 3]
