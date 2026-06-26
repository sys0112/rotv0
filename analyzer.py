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
