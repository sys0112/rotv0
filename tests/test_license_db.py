import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("ROTTO_DB_PATH", db_file)
    import importlib, db as db_mod
    importlib.reload(db_mod)
    yield db_mod

def test_init_license_db_creates_tables(tmp_db):
    tmp_db.init_license_db()
    import sqlite3
    conn = sqlite3.connect(os.environ["ROTTO_DB_PATH"])
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert "license_keys" in tables
    assert "admin_config" in tables

def test_save_and_get_license_key(tmp_db):
    tmp_db.init_license_db()
    tmp_db.save_license_key("LOTO-A3F2-9B1E-4C7D-88FA", "ORDER-001", "홍길동")
    row = tmp_db.get_license_key("LOTO-A3F2-9B1E-4C7D-88FA")
    assert row is not None
    assert row["order_id"] == "ORDER-001"
    assert row["note"] == "홍길동"

def test_get_license_key_not_found(tmp_db):
    tmp_db.init_license_db()
    assert tmp_db.get_license_key("LOTO-0000-0000-0000-0000") is None

def test_get_all_license_keys(tmp_db):
    tmp_db.init_license_db()
    tmp_db.save_license_key("LOTO-AAAA-BBBB-CCCC-DDDD", "ORDER-001", "")
    tmp_db.save_license_key("LOTO-1111-2222-3333-4444", "ORDER-002", "테스트")
    rows = tmp_db.get_all_license_keys()
    assert len(rows) == 2

def test_admin_password_hash_none_initially(tmp_db):
    tmp_db.init_license_db()
    assert tmp_db.get_admin_password_hash() is None

def test_set_and_get_admin_password_hash(tmp_db):
    tmp_db.init_license_db()
    tmp_db.set_admin_password_hash("$2b$12$fakehash")
    assert tmp_db.get_admin_password_hash() == "$2b$12$fakehash"

def test_get_or_create_flask_secret_stable(tmp_db):
    tmp_db.init_license_db()
    s1 = tmp_db.get_or_create_flask_secret()
    s2 = tmp_db.get_or_create_flask_secret()
    assert s1 == s2
    assert len(s1) == 64
