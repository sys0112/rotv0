# 라이선스 시스템 Design Spec

## Overview

로또 번호 분석기 EXE를 크몽 등에서 판매할 때 구매자별 라이선스 키로 인증하는 시스템.
오프라인 HMAC 검증 방식으로 서버 없이 동작하며, 관리자 패널에서 키를 생성하고 발급 이력을 관리한다.

---

## Architecture

### 흐름

```
[구매자 최초 실행]
    ↓
license.key 파일 존재 + 유효? ──No──→ /license 페이지 (키 입력)
    ↓ Yes                                    ↓ 유효한 키 입력
모든 라우트 정상 접근 허용             license.key 저장 → / 로 리다이렉트

[판매자 관리]
/admin/login → bcrypt 비밀번호 검증 → /admin
    → 주문번호 입력 → 키 생성 → 발급 이력 저장
```

---

## License Key

### 생성 알고리즘

```python
import hmac, hashlib

SECRET = "판매자만 아는 비밀값"  # EXE에 하드코딩 (obfuscate 처리)

def generate_key(order_id: str) -> str:
    raw = hmac.new(SECRET.encode(), order_id.encode(), hashlib.sha256).hexdigest()
    hex16 = raw[:16].upper()
    return f"LOTO-{hex16[0:4]}-{hex16[4:8]}-{hex16[8:12]}-{hex16[12:16]}"
    # 예: LOTO-A3F2-9B1E-4C7D-88FA

def validate_key(key: str) -> bool:
    # 발급된 키 목록과 대조 (DB에서 조회)
    # 또는 역산 불가능하므로 DB에 저장된 키 목록 대조
    pass
```

### 키 형식

- 형식: `LOTO-XXXX-XXXX-XXXX-XXXX` (25자)
- 대소문자 구분 없음 (입력 시 자동 대문자 변환)
- 하이픈 자동 삽입 지원

### 검증 방식

- 앱 시작 시 `license.key` 파일에서 저장된 키를 읽음
- DB의 `license_keys` 테이블에 해당 키가 존재하는지 확인
- 파일 없거나 키가 DB에 없으면 `/license`로 리다이렉트

> **중요**: 키 유효성은 DB 조회로 판단한다. HMAC 알고리즘은 생성에만 사용하고,
> 검증은 "발급된 키 목록에 있는가"로 한다. 이렇게 하면 특정 키를 취소(revoke)할 수 있다.

### license.key 파일

- 위치: EXE와 같은 디렉토리 (`_data_dir()/license.key`)
- 내용: 평문 키 문자열 (예: `LOTO-A3F2-9B1E-4C7D-88FA`)

---

## Data Model

### DB 테이블: `license_keys`

```sql
CREATE TABLE IF NOT EXISTS license_keys (
    key         TEXT PRIMARY KEY,
    order_id    TEXT NOT NULL,
    issued_at   TEXT NOT NULL,   -- ISO8601
    note        TEXT             -- 선택적 메모 (구매자명 등)
);
```

### DB 테이블: `admin_config`

```sql
CREATE TABLE IF NOT EXISTS admin_config (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);
-- admin_config에 ('admin_password_hash', '$2b$12$...') 저장
```

---

## API Routes

| Route | Method | 설명 |
|-------|--------|------|
| `/license` | GET | 키 입력 화면 |
| `/api/license/activate` | POST | 키 검증 + license.key 저장 |
| `/admin/login` | GET | 관리자 로그인 화면 |
| `/admin/login` | POST | 비밀번호 검증 + 세션 발급 |
| `/admin` | GET | 관리자 패널 (키 생성 + 이력) |
| `/api/admin/generate` | POST | 주문번호 → 키 생성 + DB 저장 |
| `/admin/logout` | GET | 세션 제거 |

### 미들웨어

`app.py`에 `@app.before_request`로 라이선스 체크:

```python
EXEMPT_ROUTES = {"/license", "/api/license/activate", "/admin", "/admin/login", "/admin/logout", "/api/admin/generate"}

@app.before_request
def check_license():
    if request.path in EXEMPT_ROUTES:
        return
    if not is_licensed():
        return redirect("/license")
```

---

## Files

### 새로 추가

| 파일 | 역할 |
|------|------|
| `license.py` | 키 생성(`generate_key`), 검증(`is_licensed`), 파일 저장/읽기 |
| `templates/license.html` | 키 입력 UI (터미널 스타일) |
| `templates/admin.html` | 관리자 패널 UI |
| `templates/admin_login.html` | 관리자 로그인 UI |

### 기존 수정

| 파일 | 변경 내용 |
|------|-----------|
| `db.py` | `init_license_db()`, `save_license_key()`, `get_license_key()`, `get_all_license_keys()`, `get_admin_password_hash()`, `set_admin_password_hash()` |
| `app.py` | `before_request` 미들웨어, `/license`, `/admin/*`, `/api/license/*`, `/api/admin/*` 라우트 추가, `SECRET_KEY` 설정 |

---

## UI

### /license (키 입력 화면)

- 배경: 순수 검정 (`#000`)
- 폰트: `monospace` (JetBrains Mono 또는 폴백)
- 초록 글씨 (`#00ff41`)
- 중앙에 입력 카드:
  ```
  ┌─────────────────────────────┐
  │  > LOTTO ANALYZER v1.0      │
  │  > 라이선스 키를 입력하세요   │
  │                              │
  │  [LOTO-____-____-____-____] │
  │                              │
  │  [  ACTIVATE  ]              │
  └─────────────────────────────┘
  ```
- 깜빡이는 커서 애니메이션
- 잘못된 키: 빨간 에러 메시지 + 화면 쉐이크 애니메이션
- 성공: 초록 "LICENSED" 메시지 + 페이드아웃 후 앱으로 이동

### /admin (관리자 패널)

- 현재 앱 다크 테마와 통일 (glass card 스타일)
- 상단: 발급된 키 수 카운트
- 좌측: 키 생성 폼 (주문번호 + 메모 입력 → 생성 버튼)
- 우측: 발급 이력 테이블 (키, 주문번호, 발급일, 메모)

---

## Security

- `SECRET` 문자열은 소스에 직접 하드코딩 (PyInstaller로 패킹 시 노출 어려움)
- 관리자 비밀번호는 bcrypt 해싱 후 DB 저장
- Flask `session`은 `app.secret_key`로 서명 (랜덤 생성 후 DB에 저장)
- 관리자 첫 실행 시 `/admin`에 접근하면 비밀번호 설정 화면으로 안내

---

## Out of Scope

- 라이선스 만료일 (기간제 키)
- 온라인 활성화 서버
- 하드웨어 ID 바인딩
- 이메일 자동 발송
