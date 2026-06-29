def normalize_input(s: str):
    s = s.strip().lower()
    if s in ("y", "예", "ㅇ", "네"):
        return "yes"
    if s in ("n", "아니오", "ㄴ", "아니"):
        return "no"
    return None
