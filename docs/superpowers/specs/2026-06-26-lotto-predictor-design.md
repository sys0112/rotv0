# 로또 예측 프로그램 설계 문서

**날짜:** 2026-06-26  
**언어:** Python 3  
**형태:** CLI 툴  

---

## 개요

동행복권 사이트에서 역대 당첨 번호를 자동 크롤링하고, 통계 분석을 통해 번호별 출현 빈도 및 미출현 현황을 보여주며, 전략별 번호 조합을 추천하는 CLI 프로그램.

---

## 프로젝트 구조

```
C:\rotto\
├── main.py              # CLI 진입점 (argparse)
├── crawler.py           # 동행복권 크롤링 (requests + BeautifulSoup)
├── db.py                # SQLite 저장/조회
├── analyzer.py          # 통계 분석 로직
├── requirements.txt
└── lotto.db             # 런타임 자동 생성
```

---

## 데이터 흐름

```
동행복권 사이트 → crawler.py → db.py (SQLite) → analyzer.py → main.py (CLI 출력)
```

---

## DB 스키마

```sql
CREATE TABLE draws (
    round   INTEGER PRIMARY KEY,
    date    TEXT NOT NULL,
    n1      INTEGER NOT NULL,
    n2      INTEGER NOT NULL,
    n3      INTEGER NOT NULL,
    n4      INTEGER NOT NULL,
    n5      INTEGER NOT NULL,
    n6      INTEGER NOT NULL,
    bonus   INTEGER NOT NULL
);
```

---

## CLI 명령

### `python main.py update`
- 동행복권 사이트에서 최신 회차까지 크롤링
- 이미 DB에 있는 회차는 스킵 (증분 업데이트)
- 첫 실행 시 전체 회차 수집

### `python main.py stats`
- 1~45번 각 번호의 전체 출현 횟수 및 출현률(%) 출력
- 출현 횟수 기준 내림차순 정렬
- 마지막으로 나온 회차 기준 미출현 회차 수 표시

### `python main.py pick [--count N] [--strategy hot|cold|mixed]`
- `--count N`: 추천 조합 수 (기본값: 5)
- `--strategy`: 추천 전략 선택 (기본값: mixed)
  - `hot`: 최근 50회차 기준 고빈도 번호 풀에서 6개 선택
  - `cold`: 미출현 기간이 긴 번호 풀에서 6개 선택
  - `mixed`: 핫넘버 3개 + 콜드넘버 3개 조합

---

## 모듈 상세

### crawler.py
- 동행복권 API (`https://www.dhlottery.co.kr/gameResult.do?method=byWin&drwNo=<회차>`) 호출
- 최신 회차 번호 자동 감지
- `requests` + `BeautifulSoup` 또는 JSON 응답 파싱

### db.py
- SQLite 연결 및 테이블 초기화
- `save_draw(round, date, numbers, bonus)` — 단건 저장
- `get_all_draws()` — 전체 회차 조회
- `get_latest_round()` — 가장 최근 저장된 회차 번호 반환

### analyzer.py
- `frequency_analysis(draws)` — 번호별 출현 횟수/출현률 반환
- `last_seen_analysis(draws)` — 번호별 마지막 출현 회차 및 미출현 기간 반환
- `pick_numbers(draws, strategy, count)` — 전략별 번호 추천, count 세트 반환

### main.py
- `argparse` 기반 서브커맨드 라우팅
- 각 명령 결과를 포맷팅해서 터미널 출력

---

## 의존성 (requirements.txt)

```
requests
beautifulsoup4
```

---

## 출력 예시

```
$ python main.py stats

[번호별 출현 빈도 - 전체 1150회차 기준]
순위  번호  출현횟수  출현률   미출현(회차)
 1    34    190     16.5%    3회차
 2    27    185     16.1%    1회차
...

$ python main.py pick --count 3 --strategy mixed

[추천 번호 - 혼합 전략]
세트 1: 07 12 23 34 38 41
세트 2: 03 11 19 27 35 44
세트 3: 06 14 22 30 37 42
```

---

## 제약사항

- 동행복권 사이트 구조 변경 시 크롤러 수정 필요
- 로또는 순수 랜덤이므로 통계 기반 예측은 엔터테인먼트 목적
