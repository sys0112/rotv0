# 연금복권 분석기 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 동행복권 연금복권720+ 과거 당첨 데이터를 스크래핑하고, 자릿수별 빈도 분석으로 5세트를 추천하는 `/pension` 페이지를 추가한다.

**Architecture:** 기존 Flask 앱에 pension_crawler.py + pension_analyzer.py를 추가하고, app.py에 4개 라우트를 붙인다. DB는 기존 lotto.db에 `pension_draws` 테이블을 추가한다. UI는 index.html과 동일한 Stellar Web 스타일이지만 파란색 테마로 구성한다.

**Tech Stack:** Python 3.12, Flask, requests, SQLite, Chart.js 4.4, PyInstaller

---

## File Map

| 파일 | 변경 |
|------|------|
| `db.py` | 수정 — pension_draws 테이블 + 4개 함수 추가 |
| `pension_crawler.py` | 신규 — 동행복권 스크래핑 |
| `pension_analyzer.py` | 신규 — 자릿수별 빈도 분석 + 번호 추천 |
| `app.py` | 수정 — 4개 라우트 추가 |
| `templates/pension.html` | 신규 — UI |
| `templates/index.html` | 수정 — nav 탭 추가 |
| `tests/test_pension_db.py` | 신규 |
| `tests/test_pension_crawler.py` | 신규 |
| `tests/test_pension_analyzer.py` | 신규 |

---

## Task 1: DB — pension_draws 테이블 추가

**Files:**
- Modify: `db.py`
- Test: `tests/test_pension_db.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_pension_db.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_pension_db.py -v
```

Expected: 6 FAILED with `AttributeError: module 'db' has no attribute 'init_pension_db'`

- [ ] **Step 3: Add pension DB functions to db.py**

Append to the end of `db.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_pension_db.py -v
```

Expected: 6 PASSED

- [ ] **Step 5: Commit**

```
git add db.py tests/test_pension_db.py
git commit -m "feat: add pension_draws DB table and functions"
```

---

## Task 2: Crawler — pension_crawler.py

**Files:**
- Create: `pension_crawler.py`
- Test: `tests/test_pension_crawler.py`

**Context:** 동행복권 연금복권 결과 페이지 URL은 `https://dhlottery.co.kr/gameResult.do?method=win720&Round={round_no}`. HTML에서 `X조 YYYYYY번` 패턴을 regex로 파싱한다. 실제 사이트 HTML 구조가 다르면 Step 8에서 regex 조정이 필요할 수 있다.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_pension_crawler.py`:

```python
import pytest
from pension_crawler import _parse_pension_draw


FIXTURE_BASIC = """
<html><body>
<select id="Round" name="Round">
  <option value="195" selected>제195회(2026.06.28)</option>
  <option value="194">제194회(2026.06.21)</option>
</select>
<div class="result_area">
  <p>1등 당첨번호</p>
  <strong>3조 415207번</strong>
</div>
</body></html>
"""

FIXTURE_YEAR_FORMAT = """
<html><body>
<select name="Round">
  <option value="100">제100회(2024.03.02)</option>
</select>
<div>2024년 3월 2일 추첨</div>
<p>1등: 2조 091834번</p>
</body></html>
"""

FIXTURE_NO_DATA = "<html><body><p>결과 없음</p></body></html>"


def test_parse_basic():
    result = _parse_pension_draw(195, FIXTURE_BASIC)
    assert result is not None
    assert result["round"] == 195
    assert result["jo"] == 3
    assert result["number"] == "415207"
    assert result["date"] == "2026-06-28"


def test_parse_year_format_fallback():
    result = _parse_pension_draw(100, FIXTURE_YEAR_FORMAT)
    assert result is not None
    assert result["jo"] == 2
    assert result["number"] == "091834"
    assert result["date"] == "2024-03-02"


def test_parse_returns_none_on_missing_data():
    result = _parse_pension_draw(195, FIXTURE_NO_DATA)
    assert result is None


def test_parse_round_number_preserved():
    result = _parse_pension_draw(195, FIXTURE_BASIC)
    assert result["round"] == 195
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_pension_crawler.py -v
```

Expected: ImportError — `pension_crawler` does not exist yet

- [ ] **Step 3: Create pension_crawler.py**

Create `pension_crawler.py`:

```python
import re
import requests

BASE_URL = "https://dhlottery.co.kr"
_RESULT_URL = f"{BASE_URL}/gameResult.do?method=win720"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    session.get(_RESULT_URL, timeout=10)
    return session


def fetch_latest_pension_round() -> int:
    resp = requests.get(_RESULT_URL, timeout=10, headers={"User-Agent": _USER_AGENT})
    resp.raise_for_status()
    options = re.findall(r'<option[^>]+value=["\'](\d+)["\']', resp.text)
    if not options:
        raise RuntimeError("최신 회차를 페이지에서 찾을 수 없습니다")
    return max(int(x) for x in options)


def fetch_pension_draw(round_no: int, _session=None) -> dict | None:
    session = _session or requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    url = f"{_RESULT_URL}&Round={round_no}"
    resp = session.get(url, timeout=10)
    resp.raise_for_status()
    return _parse_pension_draw(round_no, resp.text)


def _parse_pension_draw(round_no: int, html: str) -> dict | None:
    # Try to extract date from option element: (YYYY.MM.DD) pattern
    date_match = re.search(
        r'value=["\']' + str(round_no) + r'["\'][^>]*>[^<]*\((\d{4})\.(\d{2})\.(\d{2})\)',
        html,
    )
    if date_match:
        date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
    else:
        # Fallback: YYYY년 MM월 DD일 pattern anywhere on page
        m = re.search(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', html)
        if not m:
            return None
        date = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    # Extract jo number (1-5): "X조" pattern
    jo_match = re.search(r'([1-5])조', html)
    if not jo_match:
        return None
    jo = int(jo_match.group(1))

    # Extract 6-digit number in 300 chars after the jo match
    search_area = html[jo_match.end(): jo_match.end() + 300]
    num_match = re.search(r'\b(\d{6})\b', search_area)
    if not num_match:
        return None

    return {"round": round_no, "date": date, "jo": jo, "number": num_match.group(1)}
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_pension_crawler.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```
git add pension_crawler.py tests/test_pension_crawler.py
git commit -m "feat: add pension_crawler.py with HTML parser"
```

---

## Task 3: Analyzer — pension_analyzer.py

**Files:**
- Create: `pension_analyzer.py`
- Test: `tests/test_pension_analyzer.py`

**Context:** 연금복권은 6자리 번호를 자릿수별로 분석한다. 각 자릿수(0~5번째)에서 0~9 중 어느 숫자가 많이 나왔는지 분석 후 hot/cold/mixed 전략으로 5세트 추천.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_pension_analyzer.py`:

```python
import pytest
from pension_analyzer import pension_frequency_analysis, pick_pension_numbers

SMALL_DRAWS = [
    {"round": 1, "date": "2024-01-05", "jo": 3, "number": "415207"},
    {"round": 2, "date": "2024-01-12", "jo": 1, "number": "832915"},
    {"round": 3, "date": "2024-01-19", "jo": 3, "number": "415890"},
]


def test_frequency_analysis_positions_count():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    assert len(stats["positions"]) == 6


def test_frequency_analysis_each_position_has_10_digits():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    for pos_stats in stats["positions"]:
        assert len(pos_stats) == 10
        assert all(0 <= s["digit"] <= 9 for s in pos_stats)


def test_frequency_analysis_jo_counts():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    jo_by_num = {s["jo"]: s for s in stats["jo"]}
    assert jo_by_num[3]["count"] == 2
    assert jo_by_num[1]["count"] == 1
    assert jo_by_num[2]["count"] == 0


def test_frequency_analysis_digit_count():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    # Position 0: digits are 4, 8, 4 → 4 appears twice
    pos0 = {s["digit"]: s["count"] for s in stats["positions"][0]}
    assert pos0[4] == 2
    assert pos0[8] == 1


def test_frequency_analysis_pct():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    pos0 = {s["digit"]: s for s in stats["positions"][0]}
    assert pos0[4]["pct"] == round(2 / 3 * 100, 1)


def test_frequency_analysis_empty_draws():
    stats = pension_frequency_analysis([])
    assert len(stats["positions"]) == 6
    for pos_stats in stats["positions"]:
        assert all(s["count"] == 0 for s in pos_stats)
    assert all(s["count"] == 0 for s in stats["jo"])


def test_pick_pension_numbers_returns_5():
    results = pick_pension_numbers(SMALL_DRAWS, strategy="mixed", count=5)
    assert len(results) == 5


def test_pick_pension_numbers_format():
    results = pick_pension_numbers(SMALL_DRAWS, strategy="mixed", count=5)
    for r in results:
        assert 1 <= r["jo"] <= 5
        assert len(r["number"]) == 6
        assert r["number"].isdigit()


def test_pick_pension_numbers_all_strategies():
    for strategy in ["hot", "cold", "mixed"]:
        results = pick_pension_numbers(SMALL_DRAWS, strategy=strategy, count=5)
        assert len(results) == 5
        for r in results:
            assert 1 <= r["jo"] <= 5
            assert len(r["number"]) == 6
            assert r["number"].isdigit()


def test_pick_pension_numbers_is_deterministic():
    r1 = pick_pension_numbers(SMALL_DRAWS, strategy="mixed", count=5)
    r2 = pick_pension_numbers(SMALL_DRAWS, strategy="mixed", count=5)
    assert r1 == r2
```

- [ ] **Step 2: Run tests to verify they fail**

```
pytest tests/test_pension_analyzer.py -v
```

Expected: ImportError — `pension_analyzer` does not exist yet

- [ ] **Step 3: Create pension_analyzer.py**

Create `pension_analyzer.py`:

```python
from collections import Counter


def pension_frequency_analysis(draws: list) -> dict:
    total = len(draws)
    position_counters = [Counter() for _ in range(6)]
    jo_counter = Counter()

    for draw in draws:
        jo_counter[draw["jo"]] += 1
        for pos, digit_char in enumerate(draw["number"]):
            position_counters[pos][int(digit_char)] += 1

    positions = []
    for counter in position_counters:
        pos_stats = [
            {
                "digit": d,
                "count": counter.get(d, 0),
                "pct": round(counter.get(d, 0) / total * 100, 1) if total > 0 else 0.0,
            }
            for d in range(10)
        ]
        positions.append(pos_stats)

    jo_stats = [
        {
            "jo": j,
            "count": jo_counter.get(j, 0),
            "pct": round(jo_counter.get(j, 0) / total * 100, 1) if total > 0 else 0.0,
        }
        for j in range(1, 6)
    ]

    return {"positions": positions, "jo": jo_stats}


def pick_pension_numbers(draws: list, strategy: str = "mixed", count: int = 5) -> list:
    stats = pension_frequency_analysis(draws)

    # Per-position digit rankings (hot = most frequent first)
    hot_per_pos = [
        [s["digit"] for s in sorted(pos_stats, key=lambda x: x["count"], reverse=True)]
        for pos_stats in stats["positions"]
    ]
    cold_per_pos = [list(reversed(ranked)) for ranked in hot_per_pos]

    # Jo rankings
    hot_jo = [s["jo"] for s in sorted(stats["jo"], key=lambda x: x["count"], reverse=True)]
    cold_jo = list(reversed(hot_jo))

    results = []
    for i in range(count):
        digits = []
        for pos in range(6):
            if strategy == "hot":
                digits.append(hot_per_pos[pos][i % 10])
            elif strategy == "cold":
                digits.append(cold_per_pos[pos][i % 10])
            else:  # mixed: even positions hot, odd positions cold
                if pos % 2 == 0:
                    digits.append(hot_per_pos[pos][i % 10])
                else:
                    digits.append(cold_per_pos[pos][i % 10])

        if strategy == "hot":
            jo = hot_jo[i % 5]
        elif strategy == "cold":
            jo = cold_jo[i % 5]
        else:
            jo = hot_jo[i % 5] if i % 2 == 0 else cold_jo[i % 5]

        results.append({"jo": jo, "number": "".join(str(d) for d in digits)})

    return results
```

- [ ] **Step 4: Run tests to verify they pass**

```
pytest tests/test_pension_analyzer.py -v
```

Expected: 11 PASSED

- [ ] **Step 5: Run all tests to check nothing broke**

```
pytest -v
```

Expected: all existing tests still PASS

- [ ] **Step 6: Commit**

```
git add pension_analyzer.py tests/test_pension_analyzer.py
git commit -m "feat: add pension_analyzer with positional frequency analysis"
```

---

## Task 4: API Routes — app.py

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add imports and routes to app.py**

Add after the existing `import analyzer` line:

```python
import pension_crawler
import pension_analyzer
```

Add the following 4 routes after the existing `/api/pick` route (before `if __name__ == "__main__":`):

```python
@app.route("/pension")
def pension():
    db.init_pension_db()
    draws = db.get_all_pension_draws()
    return render_template(
        "pension.html",
        total=len(draws),
        first_round=draws[0]["round"] if draws else 0,
        latest_round=draws[-1]["round"] if draws else 0,
    )


@app.route("/api/pension/update", methods=["POST"])
def api_pension_update():
    db.init_pension_db()
    latest_local = db.get_latest_pension_round()
    try:
        latest_remote = pension_crawler.fetch_latest_pension_round()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if latest_local >= latest_remote:
        draws = db.get_all_pension_draws()
        first = draws[0]["round"] if draws else 0
        return jsonify({"saved": 0, "latest": latest_local, "total": len(draws), "first_round": first})

    session = pension_crawler.build_session()
    saved = 0
    failed = 0
    for round_no in range(latest_local + 1, latest_remote + 1):
        try:
            draw = pension_crawler.fetch_pension_draw(round_no, _session=session)
            if draw:
                db.save_pension_draw(draw["round"], draw["date"], draw["jo"], draw["number"])
                saved += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    draws = db.get_all_pension_draws()
    first = draws[0]["round"] if draws else 0
    return jsonify({"saved": saved, "failed": failed, "latest": latest_remote, "total": len(draws), "first_round": first})


@app.route("/api/pension/stats")
def api_pension_stats():
    db.init_pension_db()
    draws = db.get_all_pension_draws()
    if not draws:
        return jsonify({"total": 0, "latest": 0, "first": 0, "positions": [], "jo": []})
    stats = pension_analyzer.pension_frequency_analysis(draws)
    stats["total"] = len(draws)
    stats["latest"] = draws[-1]["round"]
    stats["first"] = draws[0]["round"]
    return jsonify(stats)


@app.route("/api/pension/pick")
def api_pension_pick():
    strategy = request.args.get("strategy", "mixed")
    count = int(request.args.get("count", 5))
    db.init_pension_db()
    draws = db.get_all_pension_draws()
    if not draws:
        return jsonify({"error": "데이터가 없습니다"}), 400
    sets = pension_analyzer.pick_pension_numbers(draws, strategy=strategy, count=count)
    return jsonify({"sets": sets})
```

- [ ] **Step 2: Verify the app starts without error**

```
python app.py
```

Expected: `Running on http://127.0.0.1:5000` with no ImportError. Stop with Ctrl+C.

- [ ] **Step 3: Commit**

```
git add app.py
git commit -m "feat: add pension lottery API routes to app.py"
```

---

## Task 5: UI — pension.html + index.html nav

**Files:**
- Create: `templates/pension.html`
- Modify: `templates/index.html`

- [ ] **Step 1: Create templates/pension.html**

Create `templates/pension.html`:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>연금복권 번호 분석기</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    *, *::before, *::after { box-sizing: border-box; }
    body {
      font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
      background-color: #020508;
      background-image:
        radial-gradient(ellipse 80% 50% at 10% 0%, rgba(59,130,246,0.06) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 90% 100%, rgba(37,99,235,0.05) 0%, transparent 60%),
        radial-gradient(ellipse 40% 30% at 50% 50%, rgba(96,165,250,0.03) 0%, transparent 70%);
      min-height: 100vh;
      color: #e2e8f0;
    }
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image: radial-gradient(circle, rgba(255,255,255,0.025) 1px, transparent 1px);
      background-size: 28px 28px;
      pointer-events: none;
      z-index: 0;
    }
    #app { position: relative; z-index: 1; }
    .card {
      background: rgba(255,255,255,0.035);
      border: 1px solid rgba(255,255,255,0.08);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-radius: 16px;
    }
    .card-header {
      padding: 16px 24px;
      border-bottom: 1px solid rgba(255,255,255,0.07);
      display: flex; align-items: center; justify-content: space-between; gap: 12px;
    }
    .card-title { font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; }
    .btn-primary {
      display: flex; align-items: center; gap: 8px;
      background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(37,99,235,0.1));
      border: 1px solid rgba(59,130,246,0.3);
      color: #93c5fd; padding: 10px 20px; border-radius: 10px;
      font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.15s;
    }
    .btn-primary:hover { background: linear-gradient(135deg, rgba(59,130,246,0.3), rgba(37,99,235,0.2)); }
    .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
    #bgCanvas { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
    .kpi-card { transition: transform 0.15s; }
    .kpi-card:hover { transform: translateY(-1px); }
    .pos-tab {
      padding: 5px 10px; border-radius: 7px; font-size: 12px; font-weight: 600;
      cursor: pointer; transition: all 0.15s; color: #64748b;
      background: transparent; border: 1px solid transparent;
    }
    .pos-tab.active { background: rgba(59,130,246,0.18); color: #93c5fd; border-color: rgba(59,130,246,0.25); }
    .strategy-btn {
      padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 600;
      cursor: pointer; transition: all 0.15s; color: #64748b;
      background: transparent; border: 1px solid rgba(255,255,255,0.08);
    }
    .strategy-btn.active { background: rgba(59,130,246,0.18); color: #93c5fd; border-color: rgba(59,130,246,0.3); }
    .jo-badge {
      display: inline-flex; align-items: center; justify-content: center;
      background: rgba(59,130,246,0.15); border: 1px solid rgba(59,130,246,0.3);
      color: #93c5fd; font-size: 12px; font-weight: 700;
      padding: 4px 10px; border-radius: 8px; min-width: 44px;
    }
    .digit-box {
      width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;
      background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
      border-radius: 8px; font-size: 15px; font-weight: 700; color: #e2e8f0;
    }
  </style>
</head>
<body>
<canvas id="bgCanvas"></canvas>
<div id="app">

  <header style="background:rgba(2,5,8,0.88);border-bottom:1px solid rgba(255,255,255,0.07);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);position:sticky;top:0;z-index:50;">
    <div style="max-width:1280px;margin:0 auto;padding:14px 32px;display:flex;align-items:center;justify-content:space-between;gap:16px;">
      <div style="display:flex;align-items:center;gap:20px;">
        <div style="display:flex;align-items:center;gap:12px;">
          <div style="width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,rgba(59,130,246,0.25),rgba(37,99,235,0.1));border:1px solid rgba(59,130,246,0.3);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;">🎰</div>
          <div>
            <h1 style="font-size:16px;font-weight:700;color:#f1f5f9;letter-spacing:-0.01em;line-height:1.2;">연금복권 번호 분석기</h1>
            <p id="headerSub" style="font-size:11px;color:#64748b;margin-top:2px;">{% if total %}{{ first_round }}회 ~ {{ latest_round }}회차 수집 (총 {{ total }}회){% else %}데이터를 업데이트하세요{% endif %}</p>
          </div>
        </div>
        <nav style="display:flex;gap:4px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:4px;">
          <a href="/" style="display:flex;align-items:center;gap:6px;padding:6px 14px;border-radius:7px;font-size:13px;font-weight:500;color:#64748b;text-decoration:none;transition:color 0.15s;" onmouseover="this.style.color='#94a3b8'" onmouseout="this.style.color='#64748b'">🎱 로또</a>
          <a href="/pension" style="display:flex;align-items:center;gap:6px;padding:6px 14px;border-radius:7px;font-size:13px;font-weight:600;background:rgba(59,130,246,0.18);color:#93c5fd;border:1px solid rgba(59,130,246,0.25);text-decoration:none;">🎰 연금복권</a>
        </nav>
      </div>
      <button id="updateBtn" onclick="doUpdate()" class="btn-primary">
        <span id="updateIcon">🔄</span>
        <span id="updateText">최신 데이터 받기</span>
      </button>
    </div>
  </header>

  <main style="max-width:1280px;margin:0 auto;padding:28px 32px;display:flex;flex-direction:column;gap:20px;">

    <!-- KPI row -->
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;max-width:500px;">
      <div class="card kpi-card" style="padding:20px 22px;overflow:hidden;position:relative;">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#3b82f6,#60a5fa);border-radius:16px 16px 0 0;"></div>
        <p style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;margin-bottom:10px;">수집된 회차</p>
        <p id="kpiTotal" style="font-size:28px;font-weight:800;color:#f1f5f9;line-height:1;">{{ total or '-' }}<span style="font-size:13px;font-weight:500;color:#64748b;margin-left:4px;">회</span></p>
      </div>
      <div class="card kpi-card" style="padding:20px 22px;overflow:hidden;position:relative;">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,#6366f1,#818cf8);border-radius:16px 16px 0 0;"></div>
        <p style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;font-weight:600;margin-bottom:10px;">최신 회차</p>
        <p id="kpiLatest" style="font-size:28px;font-weight:800;color:#f1f5f9;line-height:1;">{{ latest_round or '-' }}<span style="font-size:13px;font-weight:500;color:#64748b;margin-left:4px;">회</span></p>
      </div>
    </div>

    <!-- Main grid -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start;">

      <!-- Left: Digit frequency -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">자릿수별 빈도</span>
          <div style="display:flex;gap:3px;" id="posTabs">
            <button class="pos-tab active" onclick="selectPos(0)" id="posTab0">1번째</button>
            <button class="pos-tab" onclick="selectPos(1)" id="posTab1">2번째</button>
            <button class="pos-tab" onclick="selectPos(2)" id="posTab2">3번째</button>
            <button class="pos-tab" onclick="selectPos(3)" id="posTab3">4번째</button>
            <button class="pos-tab" onclick="selectPos(4)" id="posTab4">5번째</button>
            <button class="pos-tab" onclick="selectPos(5)" id="posTab5">6번째</button>
          </div>
        </div>
        <div style="padding:20px;">
          <canvas id="freqChart" height="220"></canvas>
          <p id="noDataMsg" style="text-align:center;color:#64748b;font-size:13px;padding:40px 0;">데이터를 업데이트하세요</p>
        </div>
      </div>

      <!-- Right: Recommendations -->
      <div class="card">
        <div class="card-header">
          <span class="card-title">번호 추천</span>
          <div style="display:flex;gap:6px;">
            <button class="strategy-btn active" id="stratMixed" onclick="setStrategy('mixed')">Mixed</button>
            <button class="strategy-btn" id="stratHot" onclick="setStrategy('hot')">🔥 Hot</button>
            <button class="strategy-btn" id="stratCold" onclick="setStrategy('cold')">❄️ Cold</button>
          </div>
        </div>
        <div style="padding:20px;display:flex;flex-direction:column;gap:12px;">
          <div id="setsContainer" style="display:flex;flex-direction:column;gap:8px;min-height:220px;">
            <p style="color:#64748b;font-size:13px;text-align:center;margin-top:40px;">번호 추천받기 버튼을 눌러주세요</p>
          </div>
          <button onclick="doPick()" class="btn-primary" style="width:100%;justify-content:center;margin-top:4px;">
            🎰 번호 추천받기
          </button>
        </div>
      </div>

    </div>
  </main>
</div>

<script>
// ── Stellar Web background (blue) ──
(function() {
  const canvas = document.getElementById('bgCanvas');
  const ctx = canvas.getContext('2d');
  function resize() { canvas.width = innerWidth; canvas.height = innerHeight; }
  resize();
  window.addEventListener('resize', resize);
  const N = 80;
  const nodes = Array.from({ length: N }, () => ({
    x: Math.random() * innerWidth, y: Math.random() * innerHeight,
    vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
    r: 1 + Math.random() * 1.5,
  }));
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = 0; i < N; i++) {
      const a = nodes[i];
      a.x += a.vx; a.y += a.vy;
      if (a.x < 0 || a.x > canvas.width) a.vx *= -1;
      if (a.y < 0 || a.y > canvas.height) a.vy *= -1;
      for (let j = i + 1; j < N; j++) {
        const b = nodes[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 150) {
          ctx.strokeStyle = `rgba(59,130,246,${(1 - dist/150) * 0.15})`;
          ctx.lineWidth = 0.8;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
      ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, Math.PI*2);
      ctx.fillStyle = 'rgba(59,130,246,0.25)'; ctx.fill();
    }
    requestAnimationFrame(draw);
  }
  draw();
})();

// ── State ──
let currentStrategy = 'mixed';
let currentPos = 0;
let statsData = null;
let freqChart = null;

// ── Update ──
async function doUpdate() {
  const btn = document.getElementById('updateBtn');
  const icon = document.getElementById('updateIcon');
  const text = document.getElementById('updateText');
  btn.disabled = true; icon.textContent = '⏳'; text.textContent = '업데이트 중...';
  try {
    const r = await fetch('/api/pension/update', { method: 'POST' });
    const d = await r.json();
    if (d.error) throw new Error(d.error);
    document.getElementById('kpiTotal').innerHTML = `${d.total}<span style="font-size:13px;font-weight:500;color:#64748b;margin-left:4px;">회</span>`;
    document.getElementById('kpiLatest').innerHTML = `${d.latest}<span style="font-size:13px;font-weight:500;color:#64748b;margin-left:4px;">회</span>`;
    document.getElementById('headerSub').textContent = `1회 ~ ${d.latest}회차 수집 (총 ${d.total}회)`;
    icon.textContent = '✅'; text.textContent = `${d.saved}건 저장됨`;
    await loadStats();
  } catch(e) {
    icon.textContent = '❌'; text.textContent = '오류: ' + e.message;
  } finally {
    btn.disabled = false;
    setTimeout(() => { icon.textContent = '🔄'; text.textContent = '최신 데이터 받기'; }, 3000);
  }
}

// ── Stats & Chart ──
async function loadStats() {
  const r = await fetch('/api/pension/stats');
  statsData = await r.json();
  if (statsData.positions && statsData.positions.length > 0) {
    document.getElementById('noDataMsg').style.display = 'none';
    renderChart(currentPos);
  }
}

function selectPos(idx) {
  currentPos = idx;
  for (let i = 0; i < 6; i++) {
    document.getElementById(`posTab${i}`).classList.toggle('active', i === idx);
  }
  if (statsData && statsData.positions) renderChart(idx);
}

function renderChart(posIdx) {
  if (!statsData || !statsData.positions || statsData.positions.length === 0) return;
  const posData = statsData.positions[posIdx];
  const labels = posData.map(s => s.digit.toString());
  const data = posData.map(s => s.count);
  const ctx = document.getElementById('freqChart').getContext('2d');
  if (freqChart) freqChart.destroy();
  freqChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: `${posIdx+1}번째 자리 빈도`,
        data,
        backgroundColor: 'rgba(59,130,246,0.45)',
        borderColor: 'rgba(59,130,246,0.8)',
        borderWidth: 1,
        borderRadius: 4,
      }]
    },
    options: {
      responsive: true,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', font: { weight: '600' } } },
      }
    }
  });
}

// ── Strategy ──
function setStrategy(s) {
  currentStrategy = s;
  document.getElementById('stratMixed').classList.toggle('active', s === 'mixed');
  document.getElementById('stratHot').classList.toggle('active', s === 'hot');
  document.getElementById('stratCold').classList.toggle('active', s === 'cold');
}

// ── Pick ──
async function doPick() {
  const r = await fetch(`/api/pension/pick?strategy=${currentStrategy}&count=5`);
  const d = await r.json();
  if (d.error) { alert(d.error); return; }
  renderSets(d.sets);
}

function renderSets(sets) {
  document.getElementById('setsContainer').innerHTML = sets.map((s, i) => `
    <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:10px;">
      <span style="font-size:11px;color:#64748b;font-weight:600;min-width:16px;">${i+1}</span>
      <span class="jo-badge">${s.jo}조</span>
      <div style="display:flex;gap:5px;">
        ${s.number.split('').map(d => `<span class="digit-box">${d}</span>`).join('')}
      </div>
    </div>
  `).join('');
}

// ── Init: load existing stats if data already in DB ──
window.addEventListener('load', () => { loadStats(); });
</script>
</body>
</html>
```

- [ ] **Step 2: Add nav tabs to index.html**

In `templates/index.html`, find the header section that ends with:
```html
          </div>
        </div>
      </div>
      <button id="updateBtn" onclick="doUpdate()" class="btn-primary">
```

Insert the nav between the closing `</div>` of the logo section and the `<button>`:

```html
        <nav style="display:flex;gap:4px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:4px;">
          <a href="/" style="display:flex;align-items:center;gap:6px;padding:6px 14px;border-radius:7px;font-size:13px;font-weight:600;background:rgba(16,185,129,0.18);color:#34d399;border:1px solid rgba(16,185,129,0.25);text-decoration:none;">🎱 로또</a>
          <a href="/pension" style="display:flex;align-items:center;gap:6px;padding:6px 14px;border-radius:7px;font-size:13px;font-weight:500;color:#64748b;text-decoration:none;transition:color 0.15s;" onmouseover="this.style.color='#94a3b8'" onmouseout="this.style.color='#64748b'">🎰 연금복권</a>
        </nav>
```

The exact insertion point in index.html (after line 183, before line 184):
- Find: `      <button id="updateBtn" onclick="doUpdate()" class="btn-primary">`
- Insert the nav block above it

- [ ] **Step 3: Start the Flask app and verify both pages load**

```
python app.py
```

Open `http://localhost:5000` — verify 로또 page loads with nav tabs (🎱 로또 active, 🎰 연금복권 link).
Open `http://localhost:5000/pension` — verify 연금복권 page loads with blue theme and nav tabs (🎰 연금복권 active).

Stop with Ctrl+C.

- [ ] **Step 4: Commit**

```
git add templates/pension.html templates/index.html
git commit -m "feat: add pension.html UI and nav tabs to index.html"
```

---

## Task 6: EXE 빌드

**Files:**
- Rebuild: `dist/lotto.exe`

- [ ] **Step 1: Ensure lotto.exe is not running**

Close any running instance of `dist/lotto.exe`.

- [ ] **Step 2: Rebuild EXE**

```
python -m PyInstaller lotto.spec
```

Expected: `Building EXE from EXE-00.toc completed successfully.`

- [ ] **Step 3: Smoke-test the EXE**

Double-click `dist/lotto.exe`. Verify:
- 로또 page opens at `http://localhost:5000`
- Nav shows 🎱 로또 and 🎰 연금복권 tabs
- Clicking 🎰 연금복권 navigates to pension page with blue theme

- [ ] **Step 4: Commit**

```
git add dist/lotto.exe
git commit -m "build: rebuild EXE with pension lottery feature"
```
