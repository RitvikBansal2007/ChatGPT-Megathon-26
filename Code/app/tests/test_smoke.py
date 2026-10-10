"""Smoke tests: every page renders without an exception, with banner and theme."""

import sys
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_DIR = Path(__file__).resolve().parent.parent
# `streamlit run app/Home.py` puts app/ on sys.path; AppTest does not, so do it here.
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

PAGES = [
    "Home.py",
    "pages/1_Customer_Hub.py",
    "pages/2_Cockpit.py",
    "pages/3_Receipts.py",
]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_exception(page):
    at = AppTest.from_file(str(APP_DIR / page), default_timeout=30).run()
    assert not at.exception, at.exception
    assert any("Synthetic data – demo only" in m.value for m in at.markdown), "banner missing"
    assert at.title, "page title missing"


def test_role_switcher_updates_session_state():
    at = AppTest.from_file(str(APP_DIR / "Home.py"), default_timeout=30).run()
    assert at.session_state["role"] == "Customer – Priya (GP01)"
    at.selectbox(key="_role_select").select("Auditor").run()
    assert not at.exception
    assert at.session_state["role"] == "Auditor"


@pytest.mark.parametrize("mode", ["cached", "live"])
def test_client_unimplemented_modes(monkeypatch, mode):
    import client

    monkeypatch.setenv("DEMO_MODE", mode)
    with pytest.raises(NotImplementedError, match="Step 3.5"):
        client.get_portfolio()
