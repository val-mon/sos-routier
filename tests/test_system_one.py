import json
from pathlib import Path

import pytest

from system_one import analyse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
IS_CIRC_CASES_PATH = Path(__file__).parent / "data" / "circulation_cases.json"
IS_CIRC_CASES = json.loads(IS_CIRC_CASES_PATH.read_text())

MAX_SPEED_CASES_PATH = Path(__file__).parent / "data" / "max_speed_cases.json"
MAX_SPEED_CASES = json.loads(MAX_SPEED_CASES_PATH.read_text())


@pytest.mark.parametrize("case", IS_CIRC_CASES)
def test_jev_classification_is_circulation(case):
    score, max_speed = analyse(case["text"])
    result = score >= 0.5

    assert 0.0 <= score <= 1.0
    assert (
        result is case["expected"]
    ), f"\n JEV score: {score:.3f}\n Text: {case['text']}"


@pytest.mark.parametrize("case", MAX_SPEED_CASES)
def test_jev_classification_max_speed(case):
    score, max_speed = analyse(case["text"])
    result = max_speed

    assert (
        result == case["expected"]
    ), f"\n JEV max speed: {result}\n Text: {case['text']}"
