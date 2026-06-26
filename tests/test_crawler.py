from unittest.mock import patch, Mock
import pytest
import requests as requests_lib
import crawler

MOCK_SUCCESS = {
    "returnValue": "success",
    "drwNo": 1,
    "drwNoDate": "2002-12-07",
    "drwtNo1": 10,
    "drwtNo2": 23,
    "drwtNo3": 29,
    "drwtNo4": 33,
    "drwtNo5": 37,
    "drwtNo6": 40,
    "bnusNo": 16,
}


def test_fetch_draw_parses_response():
    mock_resp = Mock()
    mock_resp.json.return_value = MOCK_SUCCESS

    with patch("crawler.requests.get", return_value=mock_resp):
        result = crawler.fetch_draw(1)

    assert result["round"] == 1
    assert result["date"] == "2002-12-07"
    assert result["numbers"] == [10, 23, 29, 33, 37, 40]
    assert result["bonus"] == 16


def test_fetch_draw_returns_none_when_fail():
    mock_resp = Mock()
    mock_resp.json.return_value = {"returnValue": "fail"}

    with patch("crawler.requests.get", return_value=mock_resp):
        result = crawler.fetch_draw(9999)

    assert result is None


def test_fetch_latest_round():
    mock_resp = Mock()
    mock_resp.json.return_value = {"returnValue": "success", "drwNo": 1150}

    with patch("crawler.requests.get", return_value=mock_resp):
        result = crawler.fetch_latest_round()

    assert result == 1150


def test_fetch_draw_passes_correct_params():
    mock_resp = Mock()
    mock_resp.json.return_value = MOCK_SUCCESS

    with patch("crawler.requests.get", return_value=mock_resp) as mock_get:
        crawler.fetch_draw(42)

    assert mock_get.call_args.kwargs["params"]["drwNo"] == 42
    assert mock_get.call_args.kwargs["params"]["method"] == "byWin"


def test_fetch_draw_raises_on_http_error():
    mock_resp = Mock()
    mock_resp.raise_for_status.side_effect = requests_lib.HTTPError("404")
    with patch("crawler.requests.get", return_value=mock_resp):
        with pytest.raises(requests_lib.HTTPError):
            crawler.fetch_draw(1)
