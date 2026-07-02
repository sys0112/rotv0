import pytest
from pension_analyzer import pension_frequency_analysis, pick_pension_numbers

SMALL_DRAWS = [
    {"round": 1, "date": "2024-01-05", "jo": 3, "number": "415207"},
    {"round": 2, "date": "2024-01-12", "jo": 1, "number": "832915"},
    {"round": 3, "date": "2024-01-19", "jo": 3, "number": "415890"},
]


def test_frequency_analysis_positions_count():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    assert len(stats["positions"]) == 6


def test_frequency_analysis_each_position_has_10_digits():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    for pos_stats in stats["positions"]:
        assert len(pos_stats) == 10
        assert all(0 <= s["digit"] <= 9 for s in pos_stats)


def test_frequency_analysis_jo_counts():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    jo_by_num = {s["jo"]: s for s in stats["jo"]}
    assert jo_by_num[3]["count"] == 2
    assert jo_by_num[1]["count"] == 1
    assert jo_by_num[2]["count"] == 0


def test_frequency_analysis_digit_count():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    # Position 0: digits are 4, 8, 4 → 4 appears twice
    pos0 = {s["digit"]: s["count"] for s in stats["positions"][0]}
    assert pos0[4] == 2
    assert pos0[8] == 1


def test_frequency_analysis_pct():
    stats = pension_frequency_analysis(SMALL_DRAWS)
    pos0 = {s["digit"]: s for s in stats["positions"][0]}
    assert pos0[4]["pct"] == round(2 / 3 * 100, 1)


def test_frequency_analysis_empty_draws():
    stats = pension_frequency_analysis([])
    assert len(stats["positions"]) == 6
    for pos_stats in stats["positions"]:
        assert all(s["count"] == 0 for s in pos_stats)
    assert all(s["count"] == 0 for s in stats["jo"])


def test_pick_pension_numbers_returns_5():
    results = pick_pension_numbers(SMALL_DRAWS, strategy="mixed", count=5)
    assert len(results) == 5


def test_pick_pension_numbers_format():
    results = pick_pension_numbers(SMALL_DRAWS, strategy="mixed", count=5)
    for r in results:
        assert 1 <= r["jo"] <= 5
        assert len(r["number"]) == 6
        assert r["number"].isdigit()


def test_pick_pension_numbers_all_strategies():
    for strategy in ["hot", "cold", "mixed"]:
        results = pick_pension_numbers(SMALL_DRAWS, strategy=strategy, count=5)
        assert len(results) == 5
        for r in results:
            assert 1 <= r["jo"] <= 5
            assert len(r["number"]) == 6
            assert r["number"].isdigit()


def test_pick_pension_numbers_is_deterministic():
    r1 = pick_pension_numbers(SMALL_DRAWS, strategy="mixed", count=5)
    r2 = pick_pension_numbers(SMALL_DRAWS, strategy="mixed", count=5)
    assert r1 == r2
