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
    random.seed(42)
    return [
        {
            "round": i + 1,
            "date": "2000-01-01",
            "numbers": sorted(random.sample(range(1, 46), 6)),
            "bonus": random.randint(1, 45),
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
    results = pick_numbers(large_draws, strategy="mixed", count=5)
    for nums in results:
        assert len(nums) == 6
        assert len(set(nums)) == 6
        assert all(1 <= n <= 45 for n in nums)
        assert nums == sorted(nums)


def test_pick_numbers_all_strategies(large_draws):
    for strategy in ["hot", "cold", "mixed"]:
        results = pick_numbers(large_draws, strategy=strategy, count=2)
        assert len(results) == 2
        for nums in results:
            assert len(nums) == 6
