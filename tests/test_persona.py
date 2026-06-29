import pytest
from persona import normalize_input

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
