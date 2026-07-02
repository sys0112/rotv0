import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(autouse=True)
def setup(tmp_path, monkeypatch):
    db_file = str(tmp_path / "test.db")
    license_file = str(tmp_path / "license.key")
    monkeypatch.setenv("ROTTO_DB_PATH", db_file)
    monkeypatch.setenv("ROTTO_LICENSE_PATH", license_file)
    import importlib, db as db_mod, license as lic_mod
    importlib.reload(db_mod)
    importlib.reload(lic_mod)
    db_mod.init_license_db()
    yield lic_mod, db_mod

def test_generate_key_format(setup):
    lic, _ = setup
    key = lic.generate_key("ORDER-001")
    parts = key.split("-")
    assert parts[0] == "LOTO"
    assert len(parts) == 5
    assert all(len(p) == 4 for p in parts[1:])

def test_generate_key_deterministic(setup):
    lic, _ = setup
    assert lic.generate_key("ORDER-001") == lic.generate_key("ORDER-001")

def test_generate_key_unique_per_order(setup):
    lic, _ = setup
    assert lic.generate_key("ORDER-001") != lic.generate_key("ORDER-002")

def test_validate_key_valid(setup):
    lic, db = setup
    key = lic.generate_key("ORDER-001")
    db.save_license_key(key, "ORDER-001")
    assert lic.validate_key(key) is True

def test_validate_key_invalid(setup):
    lic, _ = setup
    assert lic.validate_key("LOTO-0000-0000-0000-0000") is False

def test_validate_key_case_insensitive(setup):
    lic, db = setup
    key = lic.generate_key("ORDER-001")
    db.save_license_key(key, "ORDER-001")
    assert lic.validate_key(key.lower()) is True

def test_read_license_file_missing(setup):
    lic, _ = setup
    assert lic.read_license_file() is None

def test_write_and_read_license_file(setup):
    lic, _ = setup
    lic.write_license_file("LOTO-AAAA-BBBB-CCCC-DDDD")
    assert lic.read_license_file() == "LOTO-AAAA-BBBB-CCCC-DDDD"

def test_is_licensed_true(setup):
    lic, db = setup
    key = lic.generate_key("ORDER-001")
    db.save_license_key(key, "ORDER-001")
    lic.write_license_file(key)
    assert lic.is_licensed() is True

def test_is_licensed_false_no_file(setup):
    lic, _ = setup
    assert lic.is_licensed() is False

def test_is_licensed_false_key_not_in_db(setup):
    lic, _ = setup
    lic.write_license_file("LOTO-0000-0000-0000-0000")
    assert lic.is_licensed() is False
