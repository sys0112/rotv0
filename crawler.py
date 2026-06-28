import re
import requests

BASE_URL = "https://www.dhlottery.co.kr"
_RESULT_URL = f"{BASE_URL}/lt645/result"
_API_URL = f"{BASE_URL}/lt645/selectPstLt645InfoNew.do"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": _USER_AGENT})
    session.get(_RESULT_URL, timeout=10)
    return session


def fetch_draw(round_no: int, _session=None) -> dict | None:
    session = _session or build_session()
    resp = session.get(
        _API_URL,
        params={"srchDir": "center", "srchLtEpsd": round_no},
        headers={
            "Accept": "application/json, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": _RESULT_URL,
        },
        timeout=10,
    )
    resp.raise_for_status()
    payload = resp.json()
    for item in (payload.get("data") or {}).get("list") or []:
        if item.get("ltEpsd") == round_no:
            raw = item["ltRflYmd"]  # "YYYYMMDD"
            return {
                "round": item["ltEpsd"],
                "date": f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}",
                "numbers": [item[f"tm{i}WnNo"] for i in range(1, 7)],
                "bonus": item["bnsWnNo"],
            }
    return None


def fetch_latest_round() -> int:
    resp = requests.get(
        _RESULT_URL, timeout=10, headers={"User-Agent": _USER_AGENT}
    )
    resp.raise_for_status()
    options = re.findall(r'data-value=["\'](\d+)["\']', resp.text)
    if not options:
        raise RuntimeError("최신 회차를 페이지에서 찾을 수 없습니다")
    return max(int(x) for x in options)
