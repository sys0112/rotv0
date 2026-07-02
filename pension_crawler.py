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
    num_match = re.search(r'(\d{6})', search_area)
    if not num_match:
        return None

    return {"round": round_no, "date": date, "jo": jo, "number": num_match.group(1)}
