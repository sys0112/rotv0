import random
import pytest
from argparse import Namespace
from unittest.mock import patch
import main


@pytest.fixture
def sample_draws():
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


def test_cmd_update_already_latest(capsys):
    with patch("main.db.init_db"), \
         patch("main.db.get_latest_round", return_value=1150), \
         patch("main.crawler.fetch_latest_round", return_value=1150):
        main.cmd_update(Namespace())
    out = capsys.readouterr().out
    assert "최신 상태" in out


def test_cmd_stats_no_data_shows_message(capsys):
    with patch("main.db.init_db"), \
         patch("main.db.get_all_draws", return_value=[]):
        main.cmd_stats(Namespace())
    out = capsys.readouterr().out
    assert "데이터가 없습니다" in out


def test_cmd_stats_shows_table(capsys, sample_draws):
    with patch("main.db.init_db"), \
         patch("main.db.get_all_draws", return_value=sample_draws):
        main.cmd_stats(Namespace())
    out = capsys.readouterr().out
    assert "출현 빈도" in out
    assert "60회차" in out


def test_cmd_pick_outputs_correct_set_count(capsys, sample_draws):
    with patch("main.db.init_db"), \
         patch("main.db.get_all_draws", return_value=sample_draws):
        main.cmd_pick(Namespace(count=3, strategy="mixed"))
    out = capsys.readouterr().out
    lines = [l for l in out.strip().split("\n") if l.startswith("세트")]
    assert len(lines) == 3


def test_cmd_pick_no_data_shows_message(capsys):
    with patch("main.db.init_db"), \
         patch("main.db.get_all_draws", return_value=[]):
        main.cmd_pick(Namespace(count=5, strategy="mixed"))
    out = capsys.readouterr().out
    assert "데이터가 없습니다" in out
