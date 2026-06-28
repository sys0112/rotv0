import random
import pytest
from analyzer import frequency_analysis, pick_numbers

SMALL_DRAWS = [
    {"round": 1, "date": "2002-12-07", "numbers": [1, 2, 3, 4, 5, 6], "bonus": 7},
    {"round": 2, "date": "2002-12-14", "numbers": [1, 2, 3, 10, 11, 12], "bonus": 13},
    {"round": 3, "date": "2002-12-21", "numbers": [1, 10, 20, 30, 40, 45], "bonus": 7},
]


@pytest.fixture
def large_draws():
    rng = random.Random(42)
    return [
        {
            "round": i + 1,
            "date": "2000-01-01",
            "numbers": sorted(rng.sample(range(1, 46), 6)),
            "bonus": rng.randint(1, 45),
        }
        for i in range(60)
    ]


def test_frequency_analysis_returns_all_45_numbers():
    stats = frequency_analysis(SMALL_DRAWS)
    assert len(stats) == 45
    assert all(1 <= s["number"] <= 45 for s in stats)


def test_frequency_analysis_counts_correctly():
    stats = frequency_analysis(SMALL_DRAWS)
    by_num = {s["number"]: s for s in stats}
    assert by_num[1]["count"] == 3
    assert by_num[2]["count"] == 2
    assert by_num[45]["count"] == 1
    assert by_num[7]["count"] == 0  # 7은 보너스 번호라 카운트 안 됨


def test_frequency_analysis_sorted_descending():
    stats = frequency_analysis(SMALL_DRAWS)
    counts = [s["count"] for s in stats]
    assert counts == sorted(counts, reverse=True)


def test_frequency_analysis_pct():
    stats = frequency_analysis(SMALL_DRAWS)
    by_num = {s["number"]: s for s in stats}
    assert by_num[1]["pct"] == 100.0  # 3회 중 3회 출현


def test_frequency_analysis_last_seen_ago():
    stats = frequency_analysis(SMALL_DRAWS)
    by_num = {s["number"]: s for s in stats}
    # 6번은 1회차에만 출현, 최신 회차 3 - 마지막 출현 1 = 2회차 미출현
    assert by_num[6]["last_seen_ago"] == 2
    # 1번은 3회차에도 출현, ago = 0
    assert by_num[1]["last_seen_ago"] == 0


def test_pick_numbers_returns_requested_count(large_draws):
    results = pick_numbers(large_draws, strategy="mixed", count=3)
    assert len(results) == 3


def test_pick_numbers_each_set_has_6_unique(large_draws):
    for count in [3, 5, 7, 10]:
        results = pick_numbers(large_draws, strategy="mixed", count=count)
        assert len(results) == count, f"count={count}: expected {count} sets"
        for nums in results:
            assert len(nums) == 6, f"count={count}: set has {len(nums)} numbers"
            assert len(set(nums)) == 6
            assert all(1 <= n <= 45 for n in nums)
            assert nums == sorted(nums)


def test_pick_numbers_all_strategies(large_draws):
    for strategy in ["hot", "cold", "mixed"]:
        for count in [2, 5, 10]:
            results = pick_numbers(large_draws, strategy=strategy, count=count)
            assert len(results) == count
            for nums in results:
                assert len(nums) == 6
                assert len(set(nums)) == 6


def test_pick_numbers_is_deterministic(large_draws):
    result1 = pick_numbers(large_draws, strategy="mixed", count=5)
    result2 = pick_numbers(large_draws, strategy="mixed", count=5)
    assert result1 == result2


def test_hot_and_cold_strategies_differ(large_draws):
    hot_results = [n for nums in pick_numbers(large_draws, strategy="hot", count=3) for n in nums]
    cold_results = [n for nums in pick_numbers(large_draws, strategy="cold", count=3) for n in nums]
    assert set(hot_results) != set(cold_results)


def test_frequency_analysis_empty_draws():
    stats = frequency_analysis([])
    assert len(stats) == 45
    assert all(s["count"] == 0 for s in stats)
    assert all(s["pct"] == 0.0 for s in stats)
    assert all(s["last_seen_ago"] == 0 for s in stats)
