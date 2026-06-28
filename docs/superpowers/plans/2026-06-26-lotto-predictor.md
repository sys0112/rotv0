# 로또 예측 프로그램 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 동행복권 사이트에서 역대 당첨 번호를 자동 크롤링하고 통계 분석 기반으로 번호를 추천하는 Python CLI 프로그램을 만든다.

**Architecture:** `crawler.py`가 동행복권 JSON API를 호출해 회차 데이터를 수집하고, `db.py`가 SQLite에 저장하며, `analyzer.py`가 통계를 계산하고, `main.py`가 argparse CLI로 이를 묶는다.

**Tech Stack:** Python 3.10+, requests, pytest, SQLite (stdlib)

---

## File Map

| 파일 | 역할 |
|------|------|
| `requirements.txt` | 의존성 선언 |
| `db.py` | SQLite 초기화, 저장, 조회 |
| `crawler.py` | 동행복권 API 크롤링 |
| `analyzer.py` | 빈도/미출현 분석, 번호 추천 |
| `main.py` | CLI 진입점 (update / stats / pick) |
| `tests/__init__.py` | 테스트 패키지 마커 |
| `tests/test_db.py` | db.py 유닛 테스트 |
| `tests/test_crawler.py` | crawler.py 유닛 테스트 (requests mocking) |
| `tests/test_analyzer.py` | analyzer.py 유닛 테스트 |
| `tests/test_main.py` | main.py 통합 테스트 |

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/__init__.py`

- [ ] **Step 1: requirements.txt 작성**

```
requests
pytest
```

파일 경로: `C:\rotto\requirements.txt`

- [ ] **Step 2: tests 패키지 마커 생성**

`C:\rotto\tests\__init__.py` — 빈 파일 생성

- [ ] **Step 3: 의존성 설치**

```
pip install -r requirements.txt
```

Expected: `Successfully installed requests-... pytest-...`

- [ ] **Step 4: pytest 동작 확인**

```
pytest --collect-only
```

Expected: `no tests ran` (에러 없이 종료)

- [ ] **Step 5: git 초기화 및 커밋**

```
git init
git add requirements.txt tests/__init__.py
git commit -m "chore: project setup"
```

---

## Task 2: DB Module

**Files:**
- Create: `db.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`C:\rotto\tests\test_db.py`:

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

```
pytest tests/test_db.py -v
```

Expected: `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 3: db.py 구현**

`C:\rotto\db.py`:

```python
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
```

- [ ] **Step 4: 테스트 통과 확인**

```
pytest tests/test_db.py -v
```

Expected: `6 passed`

- [ ] **Step 5: 커밋**

```
git add db.py tests/test_db.py
git commit -m "feat: add SQLite db module"
```

---

## Task 3: Crawler Module

**Files:**
- Create: `crawler.py`
- Create: `tests/test_crawler.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`C:\rotto\tests\test_crawler.py`:

```python
from unittest.mock import patch, Mock
import crawler

MOCK_SUCCESS = {
    "returnValue": "success",
    "drwNo": 1,
    "drwNoDate": "2002-12-07",
    "drwtNo1": 10,
    "drwtNo2": 23,
    "drwtNo3": 29,
    "drwtNo4": 33,
    "drwtNo5": 37,
    "drwtNo6": 40,
    "bnusNo": 16,
}


def test_fetch_draw_parses_response():
    mock_resp = Mock()
    mock_resp.json.return_value = MOCK_SUCCESS

    with patch("crawler.requests.get", return_value=mock_resp):
        result = crawler.fetch_draw(1)

    assert result["round"] == 1
    assert result["date"] == "2002-12-07"
    assert result["numbers"] == [10, 23, 29, 33, 37, 40]
    assert result["bonus"] == 16


def test_fetch_draw_returns_none_when_fail():
    mock_resp = Mock()
    mock_resp.json.return_value = {"returnValue": "fail"}

    with patch("crawler.requests.get", return_value=mock_resp):
        result = crawler.fetch_draw(9999)

    assert result is None


def test_fetch_latest_round():
    mock_resp = Mock()
    mock_resp.json.return_value = {**MOCK_SUCCESS, "drwNo": 1150}

    with patch("crawler.requests.get", return_value=mock_resp):
        result = crawler.fetch_latest_round()

    assert result == 1150


def test_fetch_draw_passes_correct_params():
    mock_resp = Mock()
    mock_resp.json.return_value = MOCK_SUCCESS

    with patch("crawler.requests.get", return_value=mock_resp) as mock_get:
        crawler.fetch_draw(42)

    call_kwargs = mock_get.call_args
    assert call_kwargs[1]["params"]["drwNo"] == 42
    assert call_kwargs[1]["params"]["method"] == "byWin"
```

- [ ] **Step 2: 테스트 실패 확인**

```
pytest tests/test_crawler.py -v
```

Expected: `ModuleNotFoundError: No module named 'crawler'`

- [ ] **Step 3: crawler.py 구현**

`C:\rotto\crawler.py`:

```python
import requests

API_URL = "https://www.dhlottery.co.kr/gameResult.do"


def fetch_draw(round_no: int) -> dict:
    resp = requests.get(
        API_URL,
        params={"method": "byWin", "drwNo": round_no},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("returnValue") != "success":
        return None
    return {
        "round": data["drwNo"],
        "date": data["drwNoDate"],
        "numbers": [data[f"drwtNo{i}"] for i in range(1, 7)],
        "bonus": data["bnusNo"],
    }


def fetch_latest_round() -> int:
    resp = requests.get(API_URL, params={"method": "byWin"}, timeout=10)
    resp.raise_for_status()
    return resp.json()["drwNo"]
```

- [ ] **Step 4: 테스트 통과 확인**

```
pytest tests/test_crawler.py -v
```

Expected: `4 passed`

- [ ] **Step 5: 커밋**

```
git add crawler.py tests/test_crawler.py
git commit -m "feat: add lottery crawler"
```

---

## Task 4: Analyzer Module

**Files:**
- Create: `analyzer.py`
- Create: `tests/test_analyzer.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`C:\rotto\tests\test_analyzer.py`:

```python
import random
import pytest
from analyzer import frequency_analysis, pick_numbers

SMALL_DRAWS = [
    {"round": 1, "date": "2002-12-07", "numbers": [1, 2, 3, 4, 5, 6], "bonus": 7},
    {"round": 2, "date": "2002-12-14", "numbers": [1, 2, 3, 10, 11, 12], "bonus": 13},
    {"round": 3, "date": "2002-12-21", "numbers": [1, 10, 20, 30, 40, 45], "bonus": 7},
]


@pytest.fixture
def large_draws():
    random.seed(42)
    return [
        {
            "round": i + 1,
            "date": "2000-01-01",
            "numbers": sorted(random.sample(range(1, 46), 6)),
            "bonus": random.randint(1, 45),
        }
        for i in range(60)
    ]


def test_frequency_analysis_returns_all_45_numbers():
    stats = frequency_analysis(SMALL_DRAWS)
    assert len(stats) == 45
    assert all(1 <= s["number"] <= 45 for s in stats)


def test_frequency_analysis_counts_correctly():
    stats = frequency_analysis(SMALL_DRAWS)
    by_num = {s["number"]: s for s in stats}
    assert by_num[1]["count"] == 3
    assert by_num[2]["count"] == 2
    assert by_num[45]["count"] == 1
    assert by_num[7]["count"] == 0  # 7은 보너스 번호라 카운트 안 됨


def test_frequency_analysis_sorted_descending():
    stats = frequency_analysis(SMALL_DRAWS)
    counts = [s["count"] for s in stats]
    assert counts == sorted(counts, reverse=True)


def test_frequency_analysis_pct():
    stats = frequency_analysis(SMALL_DRAWS)
    by_num = {s["number"]: s for s in stats}
    assert by_num[1]["pct"] == 100.0  # 3회 중 3회 출현


def test_frequency_analysis_last_seen_ago():
    stats = frequency_analysis(SMALL_DRAWS)
    by_num = {s["number"]: s for s in stats}
    # 6번은 1회차에만 출현, 최신 회차 3 - 마지막 출현 1 = 2회차 미출현
    assert by_num[6]["last_seen_ago"] == 2
    # 1번은 3회차에도 출현, ago = 0
    assert by_num[1]["last_seen_ago"] == 0


def test_pick_numbers_returns_requested_count(large_draws):
    results = pick_numbers(large_draws, strategy="mixed", count=3)
    assert len(results) == 3


def test_pick_numbers_each_set_has_6_unique(large_draws):
    results = pick_numbers(large_draws, strategy="mixed", count=5)
    for nums in results:
        assert len(nums) == 6
        assert len(set(nums)) == 6
        assert all(1 <= n <= 45 for n in nums)
        assert nums == sorted(nums)


def test_pick_numbers_all_strategies(large_draws):
    for strategy in ["hot", "cold", "mixed"]:
        results = pick_numbers(large_draws, strategy=strategy, count=2)
        assert len(results) == 2
        for nums in results:
            assert len(nums) == 6
```

- [ ] **Step 2: 테스트 실패 확인**

```
pytest tests/test_analyzer.py -v
```

Expected: `ModuleNotFoundError: No module named 'analyzer'`

- [ ] **Step 3: analyzer.py 구현**

`C:\rotto\analyzer.py`:

```python
import random
from collections import Counter


def frequency_analysis(draws: list) -> list:
    total = len(draws)
    counter = Counter()
    last_seen = {}

    for draw in draws:
        for n in draw["numbers"]:
            counter[n] += 1
            if draw["round"] > last_seen.get(n, 0):
                last_seen[n] = draw["round"]

    latest_round = draws[-1]["round"] if draws else 0

    result = []
    for num in range(1, 46):
        count = counter.get(num, 0)
        pct = round(count / total * 100, 1) if total > 0 else 0.0
        last = last_seen.get(num, 0)
        result.append({
            "number": num,
            "count": count,
            "pct": pct,
            "last_seen_ago": latest_round - last,
        })

    return sorted(result, key=lambda x: x["count"], reverse=True)


def pick_numbers(draws: list, strategy: str = "mixed", count: int = 5) -> list:
    stats = frequency_analysis(draws)
    recent = draws[-50:] if len(draws) >= 50 else draws
    recent_counter = Counter(n for d in recent for n in d["numbers"])

    hot_pool = [
        s["number"]
        for s in sorted(stats, key=lambda x: recent_counter.get(x["number"], 0), reverse=True)[:20]
    ]
    cold_pool = [
        s["number"]
        for s in sorted(stats, key=lambda x: x["last_seen_ago"], reverse=True)[:20]
    ]

    results = []
    for _ in range(count):
        if strategy == "hot":
            nums = sorted(random.sample(hot_pool, 6))
        elif strategy == "cold":
            nums = sorted(random.sample(cold_pool, 6))
        else:
            hot3 = random.sample(hot_pool, 3)
            cold_remaining = [n for n in cold_pool if n not in hot3]
            cold3 = random.sample(cold_remaining, 3)
            nums = sorted(hot3 + cold3)
        results.append(nums)

    return results
```

- [ ] **Step 4: 테스트 통과 확인**

```
pytest tests/test_analyzer.py -v
```

Expected: `9 passed`

- [ ] **Step 5: 커밋**

```
git add analyzer.py tests/test_analyzer.py
git commit -m "feat: add statistical analyzer"
```

---

## Task 5: CLI Main

**Files:**
- Create: `main.py`
- Create: `tests/test_main.py`

- [ ] **Step 1: 실패하는 테스트 작성**

`C:\rotto\tests\test_main.py`:

```python
import random
import pytest
from argparse import Namespace
from unittest.mock import patch
import main

@pytest.fixture
def sample_draws():
    random.seed(42)
    return [
        {
            "round": i + 1,
            "date": "2000-01-01",
            "numbers": sorted(random.sample(range(1, 46), 6)),
            "bonus": random.randint(1, 45),
        }
        for i in range(60)
    ]


def test_cmd_update_already_latest(capsys):
    with patch("main.db.init_db"), \
         patch("main.db.get_latest_round", return_value=1150), \
         patch("main.crawler.fetch_latest_round", return_value=1150):
        main.cmd_update(Namespace())
    out = capsys.readouterr().out
    assert "최신 상태" in out


def test_cmd_stats_no_data_shows_message(capsys):
    with patch("main.db.init_db"), \
         patch("main.db.get_all_draws", return_value=[]):
        main.cmd_stats(Namespace())
    out = capsys.readouterr().out
    assert "데이터가 없습니다" in out


def test_cmd_stats_shows_table(capsys, sample_draws):
    with patch("main.db.init_db"), \
         patch("main.db.get_all_draws", return_value=sample_draws):
        main.cmd_stats(Namespace())
    out = capsys.readouterr().out
    assert "출현 빈도" in out
    assert "60회차" in out


def test_cmd_pick_outputs_correct_set_count(capsys, sample_draws):
    with patch("main.db.init_db"), \
         patch("main.db.get_all_draws", return_value=sample_draws):
        main.cmd_pick(Namespace(count=3, strategy="mixed"))
    out = capsys.readouterr().out
    lines = [l for l in out.strip().split("\n") if l.startswith("세트")]
    assert len(lines) == 3


def test_cmd_pick_no_data_shows_message(capsys):
    with patch("main.db.init_db"), \
         patch("main.db.get_all_draws", return_value=[]):
        main.cmd_pick(Namespace(count=5, strategy="mixed"))
    out = capsys.readouterr().out
    assert "데이터가 없습니다" in out
```

- [ ] **Step 2: 테스트 실패 확인**

```
pytest tests/test_main.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: main.py 구현**

`C:\rotto\main.py`:

```python
import argparse
import db
import crawler
import analyzer


def cmd_update(args):
    db.init_db()
    latest_local = db.get_latest_round()
    latest_remote = crawler.fetch_latest_round()

    if latest_local >= latest_remote:
        print(f"이미 최신 상태입니다. (회차: {latest_local})")
        return

    total = latest_remote - latest_local
    print(f"크롤링 시작: {latest_local + 1}회차 ~ {latest_remote}회차 (총 {total}개)")

    for round_no in range(latest_local + 1, latest_remote + 1):
        draw = crawler.fetch_draw(round_no)
        if draw:
            db.save_draw(draw["round"], draw["date"], draw["numbers"], draw["bonus"])
        print(f"  진행 중: {round_no}/{latest_remote}회차", end="\r")

    print(f"\n완료! {total}개 회차 업데이트됨")


def cmd_stats(args):
    db.init_db()
    draws = db.get_all_draws()
    if not draws:
        print("데이터가 없습니다. 먼저 'python main.py update'를 실행하세요.")
        return

    stats = analyzer.frequency_analysis(draws)
    total = len(draws)

    print(f"\n[번호별 출현 빈도 - 전체 {total}회차 기준]")
    print(f"{'순위':>4}  {'번호':>4}  {'출현횟수':>8}  {'출현률':>7}  {'미출현(회차)':>12}")
    print("-" * 55)
    for i, s in enumerate(stats, 1):
        print(f"{i:>4}  {s['number']:>4}  {s['count']:>8}  {s['pct']:>6.1f}%  {s['last_seen_ago']:>12}회차")


def cmd_pick(args):
    db.init_db()
    draws = db.get_all_draws()
    if not draws:
        print("데이터가 없습니다. 먼저 'python main.py update'를 실행하세요.")
        return

    strategy_names = {"hot": "핫넘버", "cold": "콜드넘버", "mixed": "혼합"}
    print(f"\n[추천 번호 - {strategy_names[args.strategy]} 전략]")
    sets = analyzer.pick_numbers(draws, strategy=args.strategy, count=args.count)
    for i, nums in enumerate(sets, 1):
        formatted = "  ".join(f"{n:02d}" for n in nums)
        print(f"세트 {i}: {formatted}")


def main():
    parser = argparse.ArgumentParser(description="로또 번호 통계 분석 및 추천")
    subs = parser.add_subparsers(dest="command")

    subs.add_parser("update", help="최신 당첨 번호 크롤링")
    subs.add_parser("stats", help="번호별 출현 빈도 통계")

    pick_parser = subs.add_parser("pick", help="번호 추천")
    pick_parser.add_argument("--count", type=int, default=5, help="추천 세트 수 (기본: 5)")
    pick_parser.add_argument(
        "--strategy",
        choices=["hot", "cold", "mixed"],
        default="mixed",
        help="추천 전략 (기본: mixed)",
    )

    args = parser.parse_args()

    if args.command == "update":
        cmd_update(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "pick":
        cmd_pick(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 전체 테스트 통과 확인**

```
pytest -v
```

Expected: 모든 테스트 통과 (총 24개)

- [ ] **Step 5: 최종 커밋**

```
git add main.py tests/test_main.py
git commit -m "feat: add CLI entry point"
```

---

## 완료 후 동작 확인

```bash
# 최신 데이터 크롤링 (최초 실행은 수 분 소요)
python main.py update

# 통계 확인
python main.py stats

# 혼합 전략으로 5세트 추천 (기본)
python main.py pick

# 핫넘버 전략으로 3세트
python main.py pick --count 3 --strategy hot

# 콜드넘버 전략으로 10세트
python main.py pick --count 10 --strategy cold
```
