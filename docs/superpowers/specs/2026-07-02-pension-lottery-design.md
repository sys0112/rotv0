# 연금복권 분석기 Design Spec

## Overview

기존 로또 분석기(`index.html`)와 동일한 패턴으로 연금복권720+ 과거 당첨 데이터를 스크래핑하고, 자릿수별 빈도 분석을 통해 번호 5세트를 추천하는 별도 웹 페이지를 추가한다.

---

## Architecture

### 새로 추가할 파일

| 파일 | 역할 |
|------|------|
| `pension_crawler.py` | 동행복권 사이트에서 연금복권 당첨 데이터 스크래핑 |
| `pension_analyzer.py` | 자릿수별 빈도 분석 + hot/cold/mixed 전략 번호 추천 |
| `templates/pension.html` | 연금복권 분석 페이지 UI |

### 기존 파일 수정

| 파일 | 변경 내용 |
|------|-----------|
| `app.py` | `/pension`, `/api/pension/update`, `/api/pension/stats`, `/api/pension/pick` 라우트 추가 |
| `db.py` | `pension_draws` 테이블 추가 |

### 데이터 흐름

```
동행복권 웹사이트
  → pension_crawler.py (스크래핑)
  → DB: pension_draws 테이블 (round, date, jo, number)
  → pension_analyzer.py (빈도 분석 + 추천)
  → /api/pension/pick
  → pension.html (UI 표시)
```

---

## Data Model

### DB 테이블: `pension_draws`

```sql
CREATE TABLE IF NOT EXISTS pension_draws (
    round   INTEGER PRIMARY KEY,
    date    TEXT NOT NULL,
    jo      INTEGER NOT NULL,  -- 1~5
    number  TEXT NOT NULL      -- 6자리 문자열 (예: "415207")
);
```

### 연금복권 구조

- **조(組)**: 1~5 중 하나
- **번호**: 000000~999999 (6자리, 각 자릿수 0~9)
- 매주 1회 추첨

---

## Crawler (`pension_crawler.py`)

**스크래핑 URL:**
```
https://dhlottery.co.kr/gameResult.do?method=win720&Round={round_no}
```

**구현 함수:**
- `fetch_latest_pension_round()` → 현재 최신 회차 번호 반환
- `fetch_pension_draw(round_no)` → `{"round": int, "date": str, "jo": int, "number": str}` 반환
- `build_session()` → requests Session (기존 crawler.py의 build_session과 동일 패턴)

**파싱 대상:** HTML에서 조와 6자리 번호 추출 (BeautifulSoup)

---

## Analyzer (`pension_analyzer.py`)

### 빈도 분석: `pension_frequency_analysis(draws)`

- 반환값: 자릿수별(1~6) × 숫자(0~9) 빈도 딕셔너리
- 조(1~5) 빈도 포함

```python
{
  "positions": [
    # position 0 (첫 번째 자리)
    [{"digit": 0, "count": 12, "pct": 10.5}, ...],  # 0~9
    ...  # position 1~5
  ],
  "jo": [{"jo": 1, "count": 20, "pct": 18.5}, ...]  # 1~5
}
```

### 번호 추천: `pick_pension_numbers(draws, strategy, count=5)`

각 자릿수마다 독립적으로 hot/cold digit 선택:

| 전략 | 설명 |
|------|------|
| `hot` | 각 자릿수에서 가장 많이 나온 숫자 선택 |
| `cold` | 각 자릿수에서 가장 적게 나온 숫자 선택 |
| `mixed` | 자릿수 홀짝 기준으로 hot/cold 교대 선택 |

조(Jo) 선택: 전략과 동일하게 hot/cold/mixed 적용

반환값: `[{"jo": 3, "number": "415207"}, ...]` (5세트)

---

## API Routes (`app.py`)

| Route | Method | 설명 |
|-------|--------|------|
| `/pension` | GET | `pension.html` 렌더링 |
| `/api/pension/update` | POST | 최신 데이터 스크래핑 후 DB 저장 |
| `/api/pension/stats` | GET | 자릿수별 빈도 분석 결과 반환 |
| `/api/pension/pick` | GET | `?strategy=mixed&count=5` 번호 추천 |

`/api/pension/update` 응답:
```json
{"saved": 10, "failed": 0, "latest": 195, "total": 195}
```

`/api/pension/pick` 응답:
```json
{"sets": [{"jo": 3, "number": "415207"}, ...]}
```

---

## UI (`templates/pension.html`)

### 레이아웃

```
┌─────────────────────────────────────┐
│  연금복권 번호 분석기                    │
│  [🎱 로또]  [🎰 연금복권 ←active]       │
├─────────────────────────────────────┤
│  [데이터 업데이트]  195회차 수집완료       │
├──────────────┬──────────────────────┤
│              │  번호 추천 (5세트)        │
│  자릿수별     │  ┌────────────────┐   │
│  빈도 차트    │  │ 3조 | 4 1 5 2 0 7│   │
│  (막대그래프) │  │ 1조 | 8 3 2 9 1 5│   │
│              │  └────────────────┘   │
│  자릿수 탭:   │                        │
│  [1][2][3]   │  전략: [hot][cold][mixed]│
│  [4][5][6]   │  [번호 추천받기]          │
└─────────────┴──────────────────────┘
```

### 스타일

- Stellar Web 배경 + **파란색** 노드 (`rgba(59,130,246,0.25)`) — 로또(초록)와 구분
- 기존 `.card`, 글래스 카드, Inter 폰트 동일 적용

### 자릿수별 빈도 차트

- 자릿수 탭 1~6 클릭 시 해당 자릿수의 0~9 빈도 막대그래프 표시
- Chart.js 수평 막대 차트

### 추천 번호 표시

```
3조  |  4  1  5  2  0  7
1조  |  8  3  2  9  1  5
```

- 조는 뱃지 형태로 강조
- 각 숫자는 개별 박스로 표시

### nav 탭

`index.html`과 `pension.html` 양쪽에 탭 추가:
- 로또 페이지: `[🎱 로또 ←active]  [🎰 연금복권]`
- 연금복권 페이지: `[🎱 로또]  [🎰 연금복권 ←active]`

---

## DB (`db.py`)

기존 `init_db()` 함수에 `pension_draws` 테이블 생성 추가:

```python
def init_pension_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pension_draws (
            round   INTEGER PRIMARY KEY,
            date    TEXT NOT NULL,
            jo      INTEGER NOT NULL,
            number  TEXT NOT NULL
        )
    """)
    conn.commit()
```

추가 함수:
- `get_all_pension_draws()` → 전체 목록 반환
- `get_latest_pension_round()` → 최신 회차 번호 반환
- `save_pension_draw(round, date, jo, number)` → 저장

---

## Testing

- `tests/test_pension_analyzer.py` — 빈도 분석 + 추천 함수 단위 테스트
- `tests/test_pension_crawler.py` — 파싱 함수 단위 테스트 (HTML fixture 기반)

---

## Out of Scope

- 당첨 확인 기능 (번호 입력 후 대조)
- 2등 이하 보조번호 분석
- 연금복권 구매 기능
