import json
from pathlib import Path

import pytest

from system_one import is_circulation

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = Path(__file__).parent / "data" / "circulation_cases.json"
CASES = json.loads(CASES_PATH.read_text())


@pytest.mark.parametrize("case", CASES)
def test_jev_classification(case):
    score = is_circulation(case["text"])
    result = score >= 0.5

    assert 0.0 <= score <= 1.0
    assert result is case["expected"], (
        f"\n JEV score: {score:.3f}\n Text: {case['text']}"
    )
