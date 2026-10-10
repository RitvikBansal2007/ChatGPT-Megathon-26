"""Shared page chrome: synthetic-data banner and demo role list.

No raw HTML here. The banner is a keyed container styled by theme.css()
(selector .st-key-gd_banner), so its text is a normal Streamlit widget.
"""

import streamlit as st

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


def banner() -> None:
    """Render the persistent synthetic-data pill (icon + text, never colour alone)."""
    with st.container(key="gd_banner"):
        st.markdown(BANNER_TEXT)


def current_role() -> str:
    """Return the demo role, setting the default on first visit to any page."""
    return st.session_state.setdefault("role", DEFAULT_ROLE)
