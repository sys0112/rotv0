# License Key System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 오프라인 HMAC 라이선스 키 시스템을 추가하여 EXE 실행 시 유효한 키가 있어야만 앱을 사용할 수 있게 하고, 관리자 패널에서 키를 생성·관리한다.

**Architecture:** `license.py`가 HMAC-SHA256 키 생성·검증·파일 I/O를 담당한다. DB에 `license_keys` (발급 이력)와 `admin_config` (관리자 비밀번호 해시, Flask 세션 키) 테이블을 추가한다. Flask `before_request` 미들웨어가 매 요청마다 라이선스 파일을 확인하고 미인증 시 `/license`로 리다이렉트한다.

**Tech Stack:** Python 3.12, Flask (session, redirect), werkzeug.security (PBKDF2 비밀번호 해싱), hmac + hashlib (키 생성), sqlite3, PyInstaller

---

## 파일 구조

| 파일 | 역할 |
|------|------|
| `license.py` (신규) | 키 생성, 검증, license.key 파일 읽기/쓰기, `is_licensed()` |
| `db.py` (수정) | `license_keys`, `admin_config` 테이블 + CRUD 6개 함수 |
| `app.py` (수정) | `before_request` 미들웨어, `/license`, `/api/license/activate`, `/admin/*`, `/api/admin/*` 라우트 |
| `launcher.py` (수정) | `ROTTO_LICENSE_PATH` 환경변수 추가 |
| `templates/license.html` (신규) | 터미널 스타일 키 입력 화면 |
| `templates/admin_login.html` (신규) | 관리자 로그인/최초설정 화면 |
| `templates/admin.html` (신규) | 관리자 패널 (키 생성 + 발급 이력) |
| `tests/test_license_db.py` (신규) | DB 함수 테스트 |
| `tests/test_license.py` (신규) | license.py 함수 테스트 |

---

## Task 1: DB — license_keys, admin_config 테이블 + CRUD

**Files:**
- Modify: `db.py`
- Create: `tests/test_license_db.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_license_db.py` 생성:

```python
import os, sys, tempfile, pytest
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
```

- [ ] **Step 2: 테스트 실패 확인**

```
python -m pytest tests/test_license_db.py -v
```
Expected: `ERROR` (함수 미정의)

- [ ] **Step 3: db.py에 6개 함수 추가**

`db.py` 파일 끝에 다음 코드를 추가한다:

```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

```
python -m pytest tests/test_license_db.py -v
```
Expected: 7 passed

- [ ] **Step 5: 커밋**

```
git add db.py tests/test_license_db.py
git commit -m "feat: add license_keys and admin_config DB tables"
```

---

## Task 2: license.py — 키 생성, 검증, 파일 I/O

**Files:**
- Create: `license.py`
- Create: `tests/test_license.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_license.py` 생성:

```python
import os, sys, tempfile, pytest
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
```

- [ ] **Step 2: 테스트 실패 확인**

```
python -m pytest tests/test_license.py -v
```
Expected: `ERROR` (license 모듈 없음)

- [ ] **Step 3: license.py 작성**

`license.py` 생성:

```python
import hmac
import hashlib
import os
from pathlib import Path

import db

_SECRET = b"L0tt0-An4lyz3r-x9Km2024-zPqR7vT"

LICENSE_PATH = os.environ.get(
    "ROTTO_LICENSE_PATH", str(Path(__file__).parent / "license.key")
)


def _get_license_path() -> str:
    return os.environ.get("ROTTO_LICENSE_PATH", LICENSE_PATH)


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
```

- [ ] **Step 4: 테스트 통과 확인**

```
python -m pytest tests/test_license.py -v
```
Expected: 11 passed

- [ ] **Step 5: 커밋**

```
git add license.py tests/test_license.py
git commit -m "feat: add license key generation and validation"
```

---

## Task 3: license.html + /license 라우트 + before_request 미들웨어

**Files:**
- Create: `templates/license.html`
- Modify: `app.py`
- Modify: `launcher.py`

- [ ] **Step 1: launcher.py에 ROTTO_LICENSE_PATH 추가**

`launcher.py` 33번째 줄 다음에 추가:

```python
os.environ["ROTTO_LICENSE_PATH"] = os.path.join(_data_dir(), "license.key")
```

전체 해당 블록:
```python
os.environ["ROTTO_TEMPLATE_PATH"] = _resource_path("templates")
os.environ["ROTTO_DB_PATH"] = os.path.join(_data_dir(), "lotto.db")
os.environ["ROTTO_LICENSE_PATH"] = os.path.join(_data_dir(), "license.key")
```

- [ ] **Step 2: templates/license.html 생성**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LOTTO ANALYZER — 라이선스 인증</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #000;
            color: #00ff41;
            font-family: 'JetBrains Mono', 'Courier New', monospace;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        .scanline {
            position: fixed; inset: 0;
            background: repeating-linear-gradient(
                0deg, transparent, transparent 2px,
                rgba(0,255,65,0.02) 2px, rgba(0,255,65,0.02) 4px
            );
            pointer-events: none;
        }
        .terminal {
            border: 1px solid #00ff41;
            padding: 40px 48px;
            width: 500px;
            box-shadow: 0 0 32px rgba(0,255,65,0.2), inset 0 0 32px rgba(0,0,0,0.8);
            position: relative;
            z-index: 1;
        }
        .header { margin-bottom: 32px; }
        .title { font-size: 1rem; letter-spacing: 2px; margin-bottom: 4px; }
        .subtitle { font-size: 0.75rem; color: #008f24; letter-spacing: 1px; }
        .blink { animation: blink 1s step-end infinite; }
        @keyframes blink { 50% { opacity: 0; } }
        .prompt { font-size: 0.8rem; color: #008f24; margin-bottom: 10px; letter-spacing: 1px; }
        .input-wrap { position: relative; margin-bottom: 28px; }
        input[type="text"] {
            background: transparent;
            border: none;
            border-bottom: 1px solid #00ff41;
            color: #00ff41;
            font-family: inherit;
            font-size: 1.05rem;
            letter-spacing: 4px;
            width: 100%;
            outline: none;
            padding: 8px 0;
            text-transform: uppercase;
        }
        input[type="text"]::placeholder { color: #004d14; letter-spacing: 2px; }
        button {
            background: transparent;
            border: 1px solid #00ff41;
            color: #00ff41;
            font-family: inherit;
            font-size: 0.9rem;
            letter-spacing: 3px;
            padding: 12px;
            cursor: pointer;
            width: 100%;
            transition: all 0.15s;
        }
        button:hover { background: #00ff41; color: #000; }
        .msg { margin-top: 20px; font-size: 0.8rem; min-height: 1.2em; }
        .msg.error { color: #ff4444; }
        .msg.success { color: #00ff41; }
        .shake { animation: shake 0.4s; }
        @keyframes shake {
            0%,100% { transform: translateX(0); }
            20%,60%  { transform: translateX(-10px); }
            40%,80%  { transform: translateX(10px); }
        }
    </style>
</head>
<body>
    <div class="scanline"></div>
    <div class="terminal" id="terminal">
        <div class="header">
            <div class="title">&gt; LOTTO ANALYZER v1.0<span class="blink">_</span></div>
            <div class="subtitle">&gt; LICENSE VERIFICATION REQUIRED</div>
        </div>
        <div class="prompt">&gt; 라이선스 키를 입력하세요</div>
        <div class="input-wrap">
            <input type="text" id="keyInput"
                   placeholder="LOTO-XXXX-XXXX-XXXX-XXXX"
                   maxlength="24"
                   autocomplete="off"
                   spellcheck="false">
        </div>
        <button onclick="activate()">[ ACTIVATE ]</button>
        <div class="msg" id="msg"></div>
    </div>

    <script>
        const input = document.getElementById('keyInput');

        input.addEventListener('input', e => {
            let raw = e.target.value.replace(/[^A-Za-z0-9]/g, '').toUpperCase();
            // 접두사 LOTO 고정
            let body = raw.startsWith('LOTO') ? raw.slice(4) : raw;
            body = body.replace(/[^A-F0-9]/g, '');
            let groups = [];
            for (let i = 0; i < 16 && i < body.length; i += 4) {
                groups.push(body.slice(i, i + 4));
            }
            e.target.value = groups.length ? 'LOTO-' + groups.join('-') : '';
        });

        async function activate() {
            const key = input.value.trim();
            const msgEl = document.getElementById('msg');
            const terminal = document.getElementById('terminal');
            msgEl.textContent = '> 인증 중...';
            msgEl.className = 'msg';

            let r, d;
            try {
                r = await fetch('/api/license/activate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key })
                });
                d = await r.json();
            } catch {
                msgEl.textContent = '> 오류가 발생했습니다.';
                msgEl.className = 'msg error';
                return;
            }

            if (r.ok && d.success) {
                msgEl.textContent = '> LICENSED ✓ 잠시 후 이동합니다...';
                msgEl.className = 'msg success';
                setTimeout(() => window.location.href = '/', 1200);
            } else {
                msgEl.textContent = '> 유효하지 않은 키입니다. 다시 확인해주세요.';
                msgEl.className = 'msg error';
                terminal.classList.add('shake');
                setTimeout(() => terminal.classList.remove('shake'), 400);
            }
        }

        input.addEventListener('keydown', e => { if (e.key === 'Enter') activate(); });
        input.focus();
    </script>
</body>
</html>
```

- [ ] **Step 3: app.py — import 추가, 초기화, 미들웨어, 라이선스 라우트 추가**

`app.py` 상단 import 블록을 아래로 교체:

```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, jsonify, request, redirect, session, url_for
import db
import crawler
import analyzer
import pension_crawler
import pension_analyzer
import license as lic
```

Flask 앱 생성 직후 (`app = Flask(...)` 다음 줄) 아래 코드 삽입:

```python
db.init_license_db()
app.secret_key = db.get_or_create_flask_secret()
```

`app.py`에 `before_request` 훅 추가 (앱 생성 직후, 첫 번째 `@app.route` 이전):

```python
_LICENSE_EXEMPT = {
    "/license",
    "/api/license/activate",
    "/admin",
    "/admin/login",
    "/admin/logout",
    "/api/admin/generate",
}

@app.before_request
def check_license():
    if request.path in _LICENSE_EXEMPT:
        return
    if not lic.is_licensed():
        return redirect("/license")
```

`app.py`에 라이선스 라우트 추가 (기존 라우트 중 어디든 괜찮음):

```python
@app.route("/license")
def license_page():
    if lic.is_licensed():
        return redirect("/")
    return render_template("license.html")


@app.route("/api/license/activate", methods=["POST"])
def api_license_activate():
    data = request.get_json(silent=True) or {}
    key = str(data.get("key", "")).strip().upper()
    if not key:
        return jsonify({"success": False, "error": "키를 입력해주세요"}), 400
    if not lic.validate_key(key):
        return jsonify({"success": False, "error": "유효하지 않은 키"}), 401
    lic.write_license_file(key)
    return jsonify({"success": True})
```

- [ ] **Step 4: 수동 테스트 — 미인증 상태에서 / 접근 시 /license로 이동하는지 확인**

```
python app.py
```
브라우저에서 `http://localhost:5000` 접속 → `/license`로 리다이렉트되어야 함.  
터미널 UI가 보이고 잘못된 키 입력 시 에러 메시지 + 흔들림 효과 확인.

- [ ] **Step 5: 커밋**

```
git add templates/license.html app.py launcher.py
git commit -m "feat: add license gate and terminal-style activation UI"
```

---

## Task 4: 관리자 로그인 — /admin/login, /admin/logout

**Files:**
- Create: `templates/admin_login.html`
- Modify: `app.py`

- [ ] **Step 1: templates/admin_login.html 생성**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>관리자 로그인</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0f;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Inter', sans-serif;
            color: #e2e8f0;
        }
        .card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 48px 40px;
            width: 380px;
            backdrop-filter: blur(12px);
        }
        .icon { font-size: 2.5rem; text-align: center; margin-bottom: 12px; }
        h1 { text-align: center; font-size: 1.2rem; font-weight: 600; margin-bottom: 8px; }
        .sub { text-align: center; font-size: 0.8rem; color: #64748b; margin-bottom: 32px; }
        label { display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px; }
        input[type="password"], input[type="text"] {
            width: 100%;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            color: #e2e8f0;
            font-size: 0.95rem;
            padding: 10px 14px;
            outline: none;
            margin-bottom: 20px;
        }
        input:focus { border-color: rgba(99,102,241,0.6); }
        button {
            width: 100%;
            background: #6366f1;
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 0.95rem;
            font-weight: 600;
            padding: 12px;
            cursor: pointer;
        }
        button:hover { background: #4f46e5; }
        .error {
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: 8px;
            color: #f87171;
            font-size: 0.82rem;
            padding: 10px 14px;
            margin-bottom: 16px;
        }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🔐</div>
        {% if is_setup %}
        <h1>관리자 비밀번호 설정</h1>
        <p class="sub">처음 실행 시 비밀번호를 설정하세요</p>
        {% else %}
        <h1>관리자 로그인</h1>
        <p class="sub">판매자 전용 관리 패널</p>
        {% endif %}

        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}

        <form method="POST" action="/admin/login">
            {% if is_setup %}
            <label>새 비밀번호</label>
            <input type="password" name="password" placeholder="비밀번호 입력" required autofocus>
            <label>비밀번호 확인</label>
            <input type="password" name="password_confirm" placeholder="비밀번호 재입력" required>
            <input type="hidden" name="action" value="setup">
            <button type="submit">비밀번호 설정</button>
            {% else %}
            <label>비밀번호</label>
            <input type="password" name="password" placeholder="비밀번호 입력" required autofocus>
            <input type="hidden" name="action" value="login">
            <button type="submit">로그인</button>
            {% endif %}
        </form>
    </div>
</body>
</html>
```

- [ ] **Step 2: app.py에 관리자 로그인/로그아웃 라우트 추가**

```python
from werkzeug.security import generate_password_hash, check_password_hash


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    db.init_license_db()
    has_password = db.get_admin_password_hash() is not None

    if request.method == "GET":
        return render_template("admin_login.html", is_setup=not has_password, error=None)

    action = request.form.get("action")

    if action == "setup":
        if has_password:
            return render_template("admin_login.html", is_setup=False, error="이미 설정되어 있습니다")
        pw = request.form.get("password", "")
        pw_confirm = request.form.get("password_confirm", "")
        if len(pw) < 6:
            return render_template("admin_login.html", is_setup=True, error="비밀번호는 6자 이상이어야 합니다")
        if pw != pw_confirm:
            return render_template("admin_login.html", is_setup=True, error="비밀번호가 일치하지 않습니다")
        db.set_admin_password_hash(generate_password_hash(pw))
        session["is_admin"] = True
        return redirect("/admin")

    if action == "login":
        if not has_password:
            return redirect("/admin/login")
        pw = request.form.get("password", "")
        stored_hash = db.get_admin_password_hash()
        if not check_password_hash(stored_hash, pw):
            return render_template("admin_login.html", is_setup=False, error="비밀번호가 틀렸습니다")
        session["is_admin"] = True
        return redirect("/admin")

    return redirect("/admin/login")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect("/admin/login")
```

- [ ] **Step 3: 수동 테스트**

```
python app.py
```
1. `http://localhost:5000/admin/login` 접속 → 비밀번호 설정 화면 표시
2. 비밀번호 설정 완료 → `/admin`으로 이동 (아직 admin.html 없으니 404)
3. `/admin/logout` → 로그인 화면으로 이동
4. 로그인 화면에서 틀린 비밀번호 → 에러 메시지 표시
5. 맞는 비밀번호 → `/admin` 이동

- [ ] **Step 4: 커밋**

```
git add templates/admin_login.html app.py
git commit -m "feat: add admin login/logout with password setup flow"
```

---

## Task 5: 관리자 패널 — admin.html + 키 생성 라우트

**Files:**
- Create: `templates/admin.html`
- Modify: `app.py`

- [ ] **Step 1: templates/admin.html 생성**

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>관리자 패널 — LOTTO ANALYZER</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #0a0a0f;
            font-family: 'Inter', sans-serif;
            color: #e2e8f0;
            min-height: 100vh;
            padding: 32px;
        }
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 32px;
            padding-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .header-left h1 { font-size: 1.4rem; font-weight: 700; }
        .header-left p { font-size: 0.82rem; color: #64748b; margin-top: 4px; }
        .btn-logout {
            background: rgba(239,68,68,0.1);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: 8px;
            color: #f87171;
            font-size: 0.82rem;
            padding: 8px 16px;
            cursor: pointer;
            text-decoration: none;
        }
        .stat-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 20px 24px;
            display: inline-block;
            margin-bottom: 28px;
        }
        .stat-card .num { font-size: 2rem; font-weight: 700; color: #818cf8; }
        .stat-card .label { font-size: 0.8rem; color: #64748b; margin-top: 2px; }
        .grid { display: grid; grid-template-columns: 360px 1fr; gap: 24px; }
        .card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 24px;
        }
        .card h2 { font-size: 1rem; font-weight: 600; margin-bottom: 20px; color: #c7d2fe; }
        label { display: block; font-size: 0.8rem; color: #94a3b8; margin-bottom: 6px; }
        input[type="text"] {
            width: 100%;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            color: #e2e8f0;
            font-size: 0.9rem;
            padding: 9px 12px;
            outline: none;
            margin-bottom: 14px;
        }
        input:focus { border-color: rgba(99,102,241,0.5); }
        .btn-generate {
            width: 100%;
            background: #6366f1;
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 0.9rem;
            font-weight: 600;
            padding: 11px;
            cursor: pointer;
        }
        .btn-generate:hover { background: #4f46e5; }
        .result-box {
            background: rgba(99,102,241,0.1);
            border: 1px solid rgba(99,102,241,0.3);
            border-radius: 8px;
            padding: 14px;
            margin-top: 16px;
            display: none;
        }
        .result-key {
            font-family: 'Courier New', monospace;
            font-size: 1.1rem;
            letter-spacing: 2px;
            color: #a5b4fc;
            word-break: break-all;
        }
        .copy-btn {
            background: transparent;
            border: 1px solid rgba(99,102,241,0.4);
            border-radius: 6px;
            color: #818cf8;
            font-size: 0.78rem;
            padding: 4px 10px;
            cursor: pointer;
            margin-top: 8px;
        }
        table { width: 100%; border-collapse: collapse; font-size: 0.83rem; }
        th {
            text-align: left;
            color: #64748b;
            font-weight: 500;
            padding: 8px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            color: #cbd5e1;
        }
        td:first-child {
            font-family: 'Courier New', monospace;
            font-size: 0.78rem;
            color: #a5b4fc;
            letter-spacing: 1px;
        }
        tr:hover td { background: rgba(255,255,255,0.02); }
        .empty { color: #475569; text-align: center; padding: 32px; font-size: 0.85rem; }
    </style>
</head>
<body>
    <header>
        <div class="header-left">
            <h1>🔐 관리자 패널</h1>
            <p>LOTTO ANALYZER 라이선스 관리</p>
        </div>
        <a href="/admin/logout" class="btn-logout">로그아웃</a>
    </header>

    <div class="stat-card">
        <div class="num">{{ total }}</div>
        <div class="label">발급된 라이선스</div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>🔑 새 라이선스 키 생성</h2>
            <label>주문번호 (크몽 주문번호 등)</label>
            <input type="text" id="orderId" placeholder="ORDER-001" autocomplete="off">
            <label>메모 (선택 — 구매자명 등)</label>
            <input type="text" id="note" placeholder="홍길동" autocomplete="off">
            <button class="btn-generate" onclick="generate()">키 생성</button>

            <div class="result-box" id="resultBox">
                <div style="font-size:0.78rem;color:#64748b;margin-bottom:6px;">생성된 키</div>
                <div class="result-key" id="resultKey"></div>
                <button class="copy-btn" onclick="copyKey()">📋 복사</button>
            </div>
        </div>

        <div class="card">
            <h2>📋 발급 이력</h2>
            {% if keys %}
            <table>
                <thead>
                    <tr>
                        <th>라이선스 키</th>
                        <th>주문번호</th>
                        <th>메모</th>
                        <th>발급일</th>
                    </tr>
                </thead>
                <tbody>
                {% for k in keys %}
                <tr>
                    <td>{{ k.key }}</td>
                    <td>{{ k.order_id }}</td>
                    <td>{{ k.note }}</td>
                    <td>{{ k.issued_at[:10] }}</td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty">발급된 라이선스가 없습니다</div>
            {% endif %}
        </div>
    </div>

    <script>
        async function generate() {
            const orderId = document.getElementById('orderId').value.trim();
            const note = document.getElementById('note').value.trim();
            if (!orderId) { alert('주문번호를 입력하세요'); return; }

            const r = await fetch('/api/admin/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_id: orderId, note })
            });
            const d = await r.json();
            if (r.ok) {
                document.getElementById('resultKey').textContent = d.key;
                document.getElementById('resultBox').style.display = 'block';
                setTimeout(() => location.reload(), 1500);
            } else {
                alert(d.error || '오류가 발생했습니다');
            }
        }

        function copyKey() {
            const key = document.getElementById('resultKey').textContent;
            navigator.clipboard.writeText(key);
        }
    </script>
</body>
</html>
```

- [ ] **Step 2: app.py에 /admin, /api/admin/generate 라우트 추가**

```python
@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return redirect("/admin/login")
    db.init_license_db()
    keys = db.get_all_license_keys()
    return render_template("admin.html", keys=keys, total=len(keys))


@app.route("/api/admin/generate", methods=["POST"])
def api_admin_generate():
    if not session.get("is_admin"):
        return jsonify({"error": "인증 필요"}), 401
    data = request.get_json(silent=True) or {}
    order_id = str(data.get("order_id", "")).strip()
    note = str(data.get("note", "")).strip()
    if not order_id:
        return jsonify({"error": "주문번호를 입력해주세요"}), 400
    db.init_license_db()
    key = lic.generate_key(order_id)
    db.save_license_key(key, order_id, note)
    return jsonify({"key": key, "order_id": order_id})
```

- [ ] **Step 3: 수동 테스트**

```
python app.py
```

1. `http://localhost:5000/admin/login` 접속 → 비밀번호 설정 후 로그인
2. 관리자 패널에서 주문번호 `ORDER-001`, 메모 `테스트` 입력 → 키 생성
3. 생성된 키 복사
4. 로그아웃 → `/license` 페이지에서 복사한 키 입력 → 앱 진입 성공 확인
5. 재실행 시 라이선스 파일이 있으므로 바로 앱 진입 확인

- [ ] **Step 4: 전체 테스트 통과 확인**

```
python -m pytest tests/ -v
```
Expected: 기존 50개 + 신규 18개 = 68 passed

- [ ] **Step 5: 커밋**

```
git add templates/admin.html app.py
git commit -m "feat: add admin panel with license key generation and history"
```

---

## Task 6: EXE 재빌드

**Files:**
- `dist/lotto.exe` (재생성)

- [ ] **Step 1: 기존 프로세스 종료 후 빌드**

```
python -m PyInstaller --onefile --console --name "lotto" --add-data "templates;templates" --hidden-import "flask" --hidden-import "jinja2" --hidden-import "werkzeug" --hidden-import "werkzeug.security" --hidden-import "requests" --hidden-import "sqlite3" launcher.py
```

- [ ] **Step 2: 빌드 결과 확인**

```
dir dist\lotto.exe
```
Expected: 파일 존재, 14MB 내외

- [ ] **Step 3: EXE 실행 테스트**

`dist\lotto.exe` 실행:
1. `dist/license.key` 없는 상태 → `/license` 터미널 화면 표시
2. 관리자 패널에서 생성한 키 입력 → 앱 진입
3. 재실행 → 바로 앱 진입 (키 재입력 없음)

- [ ] **Step 4: 커밋**

```
git add build.bat
git commit -m "feat: rebuild EXE with license system"
```
