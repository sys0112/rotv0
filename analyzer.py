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

    hot_ranked = [
        s["number"]
        for s in sorted(stats, key=lambda x: recent_counter.get(x["number"], 0), reverse=True)
    ]
    cold_ranked = [
        s["number"]
        for s in sorted(stats, key=lambda x: x["last_seen_ago"], reverse=True)
    ]

    results = []
    if strategy == "hot":
        for i in range(count):
            start = (i * 6) % len(hot_ranked)
            nums = [hot_ranked[(start + k) % len(hot_ranked)] for k in range(6)]
            results.append(sorted(nums))
    elif strategy == "cold":
        for i in range(count):
            start = (i * 6) % len(cold_ranked)
            nums = [cold_ranked[(start + k) % len(cold_ranked)] for k in range(6)]
            results.append(sorted(nums))
    else:
        # Fixed pools: top 22 hot, remaining 23 cold.
        # Circular indexing ensures all counts (1–10) yield 6 numbers per set.
        hot_pool = hot_ranked[:22]
        cold_pool = [n for n in cold_ranked if n not in set(hot_pool)]
        for i in range(count):
            h = i * 3 % len(hot_pool)
            c = i * 3 % len(cold_pool)
            hot3 = [hot_pool[(h + k) % len(hot_pool)] for k in range(3)]
            cold3 = [cold_pool[(c + k) % len(cold_pool)] for k in range(3)]
            nums = sorted(set(hot3) | set(cold3))
            if len(nums) < 6:
                fill = [n for n in hot_ranked if n not in set(nums)]
                nums = sorted(nums + fill[:6 - len(nums)])
            results.append(nums)

    return results
