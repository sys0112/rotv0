import requests

_API_URL = "https://www.dhlottery.co.kr/pt720/selectPstPt720WnList.do"
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
_HEADERS = {
    "User-Agent": _USER_AGENT,
    "Referer": "https://www.dhlottery.co.kr/pt720/result",
    "AJAX": "true",
    "requestMenuUri": "/pt720/result",
}


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(_HEADERS)
    return session


def fetch_all_pension_draws() -> list[dict]:
    """Fetch all rounds at once from the JSON API."""
    resp = requests.get(_API_URL, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    results = payload.get("data", {}).get("result", [])
    draws = []
    for item in results:
        ymd = str(item["psltRflYmd"])
        date = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
        draws.append({
            "round": int(item["psltEpsd"]),
            "date": date,
            "jo": int(item["wnBndNo"]),
            "number": str(item["wnRnkVl"]).zfill(6),
        })
    return draws


def fetch_latest_pension_round() -> int:
    draws = fetch_all_pension_draws()
    if not draws:
        raise RuntimeError("연금복권 데이터를 가져올 수 없습니다")
    return max(d["round"] for d in draws)


def fetch_pension_draw(round_no: int, _session=None) -> dict | None:
    draws = fetch_all_pension_draws()
    for d in draws:
        if d["round"] == round_no:
            return d
    return None
