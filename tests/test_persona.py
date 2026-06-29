import pytest
from unittest.mock import patch
from persona import normalize_input, traverse

def test_yes_variants():
    assert normalize_input("y") == "yes"
    assert normalize_input("Y") == "yes"
    assert normalize_input("예") == "yes"
    assert normalize_input("ㅇ") == "yes"
    assert normalize_input("  y  ") == "yes"

def test_no_variants():
    assert normalize_input("n") == "no"
    assert normalize_input("N") == "no"
    assert normalize_input("아니오") == "no"
    assert normalize_input("ㄴ") == "no"
    assert normalize_input("  n  ") == "no"

def test_invalid_returns_none():
    assert normalize_input("maybe") is None
    assert normalize_input("") is None
    assert normalize_input("모름") is None

MINI_TREE = {
    "question": "살아있나요?",
    "yes": {
        "question": "동물인가요?",
        "yes": {"answer": "호랑이"},
        "no":  {"answer": "이순신"},
    },
    "no": {"answer": "스마트폰"},
}

def test_traverse_reaches_answer_yes_yes():
    with patch("builtins.input", side_effect=["y", "y"]):
        result = traverse(MINI_TREE)
    assert result == "호랑이"

def test_traverse_reaches_answer_yes_no():
    with patch("builtins.input", side_effect=["y", "n"]):
        result = traverse(MINI_TREE)
    assert result == "이순신"

def test_traverse_reaches_answer_no():
    with patch("builtins.input", side_effect=["n"]):
        result = traverse(MINI_TREE)
    assert result == "스마트폰"

def test_traverse_retries_on_invalid_input():
    with patch("builtins.input", side_effect=["모름", "y", "y"]):
        result = traverse(MINI_TREE)
    assert result == "호랑이"
