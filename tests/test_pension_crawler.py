import pytest
from pension_crawler import _parse_pension_draw


FIXTURE_BASIC = """
<html><body>
<select id="Round" name="Round">
  <option value="195" selected>제195회(2026.06.28)</option>
  <option value="194">제194회(2026.06.21)</option>
</select>
<div class="result_area">
  <p>1등 당첨번호</p>
  <strong>3조 415207번</strong>
</div>
</body></html>
"""

FIXTURE_YEAR_FORMAT = """
<html><body>
<select name="Round">
  <option value="100">제100회(2024.03.02)</option>
</select>
<div>2024년 3월 2일 추첨</div>
<p>1등: 2조 091834번</p>
</body></html>
"""

FIXTURE_NO_DATA = "<html><body><p>결과 없음</p></body></html>"


def test_parse_basic():
    result = _parse_pension_draw(195, FIXTURE_BASIC)
    assert result is not None
    assert result["round"] == 195
    assert result["jo"] == 3
    assert result["number"] == "415207"
    assert result["date"] == "2026-06-28"


def test_parse_year_format_fallback():
    result = _parse_pension_draw(100, FIXTURE_YEAR_FORMAT)
    assert result is not None
    assert result["jo"] == 2
    assert result["number"] == "091834"
    assert result["date"] == "2024-03-02"


def test_parse_returns_none_on_missing_data():
    result = _parse_pension_draw(195, FIXTURE_NO_DATA)
    assert result is None


def test_parse_round_number_preserved():
    result = _parse_pension_draw(195, FIXTURE_BASIC)
    assert result["round"] == 195
