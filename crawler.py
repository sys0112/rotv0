import requests

API_URL = "https://www.dhlottery.co.kr/gameResult.do"


def fetch_draw(round_no: int) -> dict | None:
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
    data = resp.json()
    if data.get("returnValue") != "success":
        raise RuntimeError(f"Unexpected API response: {data.get('returnValue')}")
    return data["drwNo"]
