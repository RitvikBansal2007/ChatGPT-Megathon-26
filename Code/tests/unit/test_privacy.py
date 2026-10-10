import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from security.privacy import (find_pii, scrub_text, llm_payload, pseudonymise,
                              LLM_FORBIDDEN_FIELDS)
from greendash.carbon.units import SAFE


def test_scrub_redacts_common_pii():
    s = scrub_text("mail a.b@example.com sort 12-34-56 acc 12345678 card 4111 1111 1111 1111 SW1A 1AA")
    for tag in ("[EMAIL]", "[SORT_CODE]", "[ACCOUNT_NO]", "[CARD]", "[POSTCODE]"):
        assert tag in s
    assert find_pii(s) == []


def test_non_luhn_digits_not_flagged_as_card():
    assert "CARD" not in find_pii("order 1234 5678 9012 3456")


def test_llm_payload_drops_identifiers_and_unknown_keys():
    p = llm_payload({"customer_id": "CUST-0001", "postcode": "SW1A 1AA", "balance": 10,
                     "accessibility_paper_need": True, "surprise": 1,
                     "product_id": "GP01", "region": "London"})
    assert p == {"product_id": "GP01", "region": "London"}


def test_llm_payload_scrubs_strings():
    p = llm_payload({"formula": "contact x@y.com"})
    assert "@" not in p["formula"]


def test_pseudonym_needs_key(monkeypatch):
    monkeypatch.delenv("PSEUDONYM_KEY", raising=False)
    with pytest.raises(RuntimeError):
        pseudonymise("CUST-0001")
    a = pseudonymise("CUST-0001", key=b"k1")
    assert a == pseudonymise("CUST-0001", key=b"k1") and a != pseudonymise("CUST-0001", key=b"k2")


def test_eval_packs_are_private_and_safe():
    packs = json.loads((ROOT / "eval/llm_eval/packs.json").read_text())["packs"]
    for pk in packs:
        blob = json.dumps(pk)
        assert find_pii(blob) == []
        for v in pk["carbon"]["display"].values():
            assert SAFE.match(v), v
        assert not (set(pk["evidence_features"]) & LLM_FORBIDDEN_FIELDS)


def test_no_personal_names_in_tracked_files():
    banned = re.compile(r"aniket|madhav|kratik|akshit|ritvik|iiit", re.I)
    files = subprocess.run(["git", "ls-files"], cwd=ROOT.parent, capture_output=True,
                           text=True).stdout.split("\n")
    for f in files:
        if not f or f.startswith(("deliverables/", ".agent/rules.md")) or f.endswith((".parquet", ".pdf", ".png", "test_privacy.py")):
            continue
        p = ROOT.parent / f
        if p.is_file():
            assert not banned.search(p.read_text(errors="ignore")), f
