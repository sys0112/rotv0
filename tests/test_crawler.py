from unittest.mock import patch, Mock
import pytest
import requests as requests_lib
import crawler

_MOCK_ITEM = {
    "ltEpsd": 1,
    "ltRflYmd": "20021207",
    "tm1WnNo": 10,
    "tm2WnNo": 23,
    "tm3WnNo": 29,
    "tm4WnNo": 33,
    "tm5WnNo": 37,
    "tm6WnNo": 40,
    "bnsWnNo": 16,
}

_MOCK_RESPONSE = {
    "resultCode": "00",
    "resultMessage": "success",
    "data": {"list": [_MOCK_ITEM]},
}


def _make_mock_session(payload):
    session = Mock()
    resp = Mock()
    resp.json.return_value = payload
    session.get.return_value = resp
    return session


def test_fetch_draw_parses_response():
    with patch("crawler.build_session", return_value=_make_mock_session(_MOCK_RESPONSE)):
        result = crawler.fetch_draw(1)

    assert result["round"] == 1
    assert result["date"] == "2002-12-07"
    assert result["numbers"] == [10, 23, 29, 33, 37, 40]
    assert result["bonus"] == 16


def test_fetch_draw_returns_none_when_round_not_in_response():
    with patch("crawler.build_session", return_value=_make_mock_session(_MOCK_RESPONSE)):
        result = crawler.fetch_draw(9999)

    assert result is None


def test_fetch_latest_round():
    mock_resp = Mock()
    mock_resp.text = (
        '<li class="option-il" data-value="1229">1229회</li>'
        '<li class="option-il" data-value="1228">1228회</li>'
    )

    with patch("crawler.requests.get", return_value=mock_resp):
        result = crawler.fetch_latest_round()

    assert result == 1229


def test_fetch_draw_passes_correct_round():
    mock_session = _make_mock_session(_MOCK_RESPONSE)
    with patch("crawler.build_session", return_value=mock_session):
        crawler.fetch_draw(1)

    params = mock_session.get.call_args.kwargs["params"]
    assert params["srchLtEpsd"] == 1
    assert params["srchDir"] == "center"


def test_fetch_draw_raises_on_http_error():
    mock_session = Mock()
    mock_resp = Mock()
    mock_resp.raise_for_status.side_effect = requests_lib.HTTPError("404")
    mock_session.get.return_value = mock_resp

    with patch("crawler.build_session", return_value=mock_session):
        with pytest.raises(requests_lib.HTTPError):
            crawler.fetch_draw(1)
