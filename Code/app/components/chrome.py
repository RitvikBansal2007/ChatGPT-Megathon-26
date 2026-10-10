"""Shared page chrome: synthetic-data banner and demo role list.

No raw HTML here. The banner is a keyed container styled by theme.css()
(selector .st-key-gd_banner), so its text is a normal Streamlit widget.
"""

from pathlib import Path

import streamlit as st

_LOGOS = Path(__file__).resolve().parent.parent / "brand guidelines"

BANNER_TEXT = "⚠ Synthetic data – demo only"

ROLES: list[str] = [
    "Customer – Priya (GP01)",
    "Customer – Aisha (GP03)",
    "Customer – Marcus (GP02)",
    "Customer – Fatima (GP04)",
    "Customer – Tom (GP01)",
    "Customer – Persona 6",
    "Customer – Persona 7",
    "Customer – Persona 8",
    "Relationship Manager",
    "Portfolio Analyst",
    "Auditor",
    "Evaluator",
]
DEFAULT_ROLE = ROLES[0]


def banner(dark: bool = False) -> None:
    """Render the logo and the persistent synthetic-data pill (icon + text).

    dark=True (Cockpit, brand guidelines §4.3) also drops a keyed marker that
    theme.css() uses to switch the whole page to the DARK tokens.
    """
    st.logo(str(_LOGOS / ("greendash-logo-dark-transparent.png" if dark else "greendash-logo-on-light.png")),
            size="large")
    if dark:
        st.container(key="gd_dark").markdown("")  # marker only; styled via :has()
    with st.container(key="gd_banner"):
        st.markdown(BANNER_TEXT)


def current_role() -> str:
    """Return the demo role, setting the default on first visit to any page."""
    return st.session_state.setdefault("role", DEFAULT_ROLE)
