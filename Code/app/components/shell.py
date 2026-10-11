"""Shared sidebar: role switcher, customer picker, role gates."""
from __future__ import annotations

import streamlit as st

import client
import theme as T

# Role -> pages it may open. Mirrors require_role(...) in api/routers (the server is what enforces it; this only hides UI).
ACCESS = {
    "hub": {"CUSTOMER", "RELATIONSHIP_MANAGER", "EVALUATOR"},
    "lab": {"RELATIONSHIP_MANAGER", "EVALUATOR"},
    "redteam": {"RELATIONSHIP_MANAGER", "EVALUATOR"},
    "cockpit": {"RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST", "AUDITOR", "EVALUATOR"},
    "customer_level": {"RELATIONSHIP_MANAGER", "EVALUATOR"},
    "governance": {"AUDITOR", "EVALUATOR"},
    "receipts": {"PORTFOLIO_ANALYST", "AUDITOR", "EVALUATOR"},
}


def can(area: str) -> bool:
    return client.role() in ACCESS[area]


def sidebar() -> dict:
    """Render the shared sidebar and return the selected persona summary."""
    people = client.personas()
    ids = [p["customer_id"] for p in people]
    # Assign (not setdefault) on every run: Streamlit drops a widget's keyed value when you move to
    # another page, which silently reset the role and customer to the first option.
    st.session_state["role"] = st.session_state.get("role", "EVALUATOR")
    st.session_state["persona_id"] = st.session_state.get("persona_id", ids[0])
    with st.sidebar:
        st.selectbox("Role", list(client.ROLES), format_func=lambda r: client.ROLES[r], key="role")
        label = "Signed in as" if st.session_state["role"] == "CUSTOMER" else "Customer"
        st.selectbox(label, ids, key="persona_id",
                     format_func=lambda i: next(f'{p["display_name"]} · {i}' for p in people if p["customer_id"] == i))
        # Follows the page's current mode; switching it applies to every page.
        st.session_state["dark_toggle"] = bool(st.session_state.get("_dark"))
        st.toggle("Dark mode", key="dark_toggle",
                  on_change=lambda: st.session_state.update(dark_mode=st.session_state["dark_toggle"]))
        st.caption(T.CORE_RULE)
    return next(p for p in people if p["customer_id"] == st.session_state["persona_id"])


def gate(area: str, what: str) -> None:
    """Stop the page if the current role may not open it (UI mirror of server-side default-deny)."""
    if not can(area):
        T.banner(f"Your role ({client.ROLES[client.role()]}) cannot open {what}. Access is default-deny.", "err")
        T.footer()
        st.stop()
