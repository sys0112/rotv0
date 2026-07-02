import pytest
from unittest.mock import patch, Mock
from pension_crawler import fetch_all_pension_draws, fetch_latest_pension_round, fetch_pension_draw

MOCK_API_RESPONSE = {
    "resultCode": None,
    "resultMessage": None,
    "data": {
        "result": [
            {"psltEpsd": 321, "psltRflYmd": "20260625", "wnBndNo": "5", "wnRnkVl": "686709", "bnsRnkVl": "326599"},
            {"psltEpsd": 320, "psltRflYmd": "20260618", "wnBndNo": "5", "wnRnkVl": "766487", "bnsRnkVl": "897760"},
            {"psltEpsd": 100, "psltRflYmd": "20240302", "wnBndNo": "2", "wnRnkVl": "091834", "bnsRnkVl": "123456"},
        ]
    }
}


def make_mock_response(data):
    m = Mock()
    m.json.return_value = data
    m.raise_for_status.return_value = None
    return m


def test_fetch_all_returns_list():
    with patch("pension_crawler.requests.get", return_value=make_mock_response(MOCK_API_RESPONSE)):
        draws = fetch_all_pension_draws()
    assert isinstance(draws, list)
    assert len(draws) == 3


def test_fetch_all_parses_fields():
    with patch("pension_crawler.requests.get", return_value=make_mock_response(MOCK_API_RESPONSE)):
        draws = fetch_all_pension_draws()
    d = next(x for x in draws if x["round"] == 321)
    assert d["date"] == "2026-06-25"
    assert d["jo"] == 5
    assert d["number"] == "686709"


def test_fetch_latest_round():
    with patch("pension_crawler.requests.get", return_value=make_mock_response(MOCK_API_RESPONSE)):
        latest = fetch_latest_pension_round()
    assert latest == 321


def test_fetch_pension_draw_found():
    with patch("pension_crawler.requests.get", return_value=make_mock_response(MOCK_API_RESPONSE)):
        draw = fetch_pension_draw(100)
    assert draw is not None
    assert draw["jo"] == 2
    assert draw["number"] == "091834"
    assert draw["date"] == "2024-03-02"


def test_fetch_pension_draw_not_found():
    with patch("pension_crawler.requests.get", return_value=make_mock_response(MOCK_API_RESPONSE)):
        draw = fetch_pension_draw(999)
    assert draw is None


def test_number_zero_padded():
    with patch("pension_crawler.requests.get", return_value=make_mock_response(MOCK_API_RESPONSE)):
        draws = fetch_all_pension_draws()
    d = next(x for x in draws if x["round"] == 100)
    assert d["number"] == "091834"
    assert len(d["number"]) == 6
