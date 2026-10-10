import pytest, yaml
from eval.scenarios.runner import CASES, check

cases = yaml.safe_load(CASES.read_text())

def test_there_are_at_least_30_cases_covering_all_four_organiser_types():
    assert len(cases) >= 30
    assert {"missing", "conflict", "ruled_out", "insufficient"} <= {c["tag"] for c in cases}

@pytest.mark.parametrize("case", cases, ids=[c["id"] for c in cases])
def test_case(case):
    assert check(case) == []
