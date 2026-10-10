"""Shared sidebar: role switcher, customer picker, role gates."""
from __future__ import annotations

import streamlit as st

import client
import theme as T

# Role -> pages it may open (config/rbac.yaml is the server-side source of truth; this only hides UI).
ACCESS = {
    "hub": {"CUSTOMER", "RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST", "AUDITOR", "EVALUATOR"},
    "lab": {"RELATIONSHIP_MANAGER", "EVALUATOR"},
    "redteam": {"AUDITOR", "EVALUATOR"},
    "cockpit": {"RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST", "AUDITOR", "EVALUATOR"},
    "customer_level": {"RELATIONSHIP_MANAGER", "EVALUATOR"},
    "governance": {"AUDITOR", "EVALUATOR"},
    "receipts": {"PORTFOLIO_ANALYST", "AUDITOR", "EVALUATOR"},
}


def can(area: str) -> bool:
    return client.role() in ACCESS[area]


def sidebar() -> dict:
    """Render the shared sidebar and return the selected persona summary."""
    st.session_state.setdefault("role", "EVALUATOR")
    people = client.personas()
    ids = [p["customer_id"] for p in people]
    st.session_state.setdefault("persona_id", ids[0])
    with st.sidebar:
        st.selectbox("Role", list(client.ROLES), format_func=lambda r: client.ROLES[r], key="role")
        label = "Signed in as" if st.session_state["role"] == "CUSTOMER" else "Customer"
        st.selectbox(label, ids, key="persona_id",
                     format_func=lambda i: next(f'{p["display_name"]} · {i}' for p in people if p["customer_id"] == i))
        st.caption(T.CORE_RULE)
    return next(p for p in people if p["customer_id"] == st.session_state["persona_id"])


def gate(area: str, what: str) -> None:
    """Stop the page if the current role may not open it (UI mirror of server-side default-deny)."""
    if not can(area):
        T.banner(f"Your role ({client.ROLES[client.role()]}) cannot open {what}. Access is default-deny.", "err")
        T.footer()
        st.stop()
