from collections import Counter


def pension_frequency_analysis(draws: list) -> dict:
    total = len(draws)
    position_counters = [Counter() for _ in range(6)]
    jo_counter = Counter()

    for draw in draws:
        jo_counter[draw["jo"]] += 1
        for pos, digit_char in enumerate(draw["number"]):
            position_counters[pos][int(digit_char)] += 1

    positions = []
    for counter in position_counters:
        pos_stats = [
            {
                "digit": d,
                "count": counter.get(d, 0),
                "pct": round(counter.get(d, 0) / total * 100, 1) if total > 0 else 0.0,
            }
            for d in range(10)
        ]
        positions.append(pos_stats)

    jo_stats = [
        {
            "jo": j,
            "count": jo_counter.get(j, 0),
            "pct": round(jo_counter.get(j, 0) / total * 100, 1) if total > 0 else 0.0,
        }
        for j in range(1, 6)
    ]

    return {"positions": positions, "jo": jo_stats}


def pick_pension_numbers(draws: list, strategy: str = "mixed", count: int = 5) -> list:
    stats = pension_frequency_analysis(draws)

    # Per-position digit rankings (hot = most frequent first)
    hot_per_pos = [
        [s["digit"] for s in sorted(pos_stats, key=lambda x: x["count"], reverse=True)]
        for pos_stats in stats["positions"]
    ]
    cold_per_pos = [list(reversed(ranked)) for ranked in hot_per_pos]

    # Jo rankings
    hot_jo = [s["jo"] for s in sorted(stats["jo"], key=lambda x: x["count"], reverse=True)]
    cold_jo = list(reversed(hot_jo))

    results = []
    for i in range(count):
        digits = []
        for pos in range(6):
            if strategy == "hot":
                digits.append(hot_per_pos[pos][i % 10])
            elif strategy == "cold":
                digits.append(cold_per_pos[pos][i % 10])
            else:  # mixed: even positions hot, odd positions cold
                if pos % 2 == 0:
                    digits.append(hot_per_pos[pos][i % 10])
                else:
                    digits.append(cold_per_pos[pos][i % 10])

        if strategy == "hot":
            jo = hot_jo[i % 5]
        elif strategy == "cold":
            jo = cold_jo[i % 5]
        else:
            jo = hot_jo[i % 5] if i % 2 == 0 else cold_jo[i % 5]

        results.append({"jo": jo, "number": "".join(str(d) for d in digits)})

    return results
