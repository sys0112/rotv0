import pytest
import db


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))


def test_init_creates_table():
    import sqlite3
    db.init_db()
    conn = sqlite3.connect(db.DB_PATH)
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='draws'"
    ).fetchone()
    conn.close()
    assert row is not None


def test_save_and_retrieve_draw():
    db.init_db()
    db.save_draw(1, "2002-12-07", [10, 23, 29, 33, 37, 40], 16)
    draws = db.get_all_draws()
    assert len(draws) == 1
    assert draws[0]["round"] == 1
    assert draws[0]["numbers"] == [10, 23, 29, 33, 37, 40]
    assert draws[0]["bonus"] == 16


def test_get_latest_round_empty():
    db.init_db()
    assert db.get_latest_round() == 0


def test_get_latest_round_with_data():
    db.init_db()
    db.save_draw(1, "2002-12-07", [10, 23, 29, 33, 37, 40], 16)
    db.save_draw(5, "2003-01-11", [1, 2, 3, 4, 5, 6], 7)
    assert db.get_latest_round() == 5


def test_save_draw_ignores_duplicate():
    db.init_db()
    db.save_draw(1, "2002-12-07", [10, 23, 29, 33, 37, 40], 16)
    db.save_draw(1, "2002-12-07", [10, 23, 29, 33, 37, 40], 16)
    assert len(db.get_all_draws()) == 1


def test_draws_ordered_by_round():
    db.init_db()
    db.save_draw(3, "2003-01-01", [1, 2, 3, 4, 5, 6], 7)
    db.save_draw(1, "2002-12-07", [10, 23, 29, 33, 37, 40], 16)
    draws = db.get_all_draws()
    assert draws[0]["round"] == 1
    assert draws[1]["round"] == 3
