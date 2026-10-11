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
        user = client.current_user()
        if user:
            st.markdown(f"**Signed in:** {T.esc(user.get('display_name', user.get('user_key')))}")
            st.caption(f"Role: {client.ROLES.get(user.get('role'), user.get('role'))} · Live JWT")
            if st.button("Sign Out", key="sb-logout"):
                client.logout()
                st.rerun()
            st.divider()

            if user.get("role") == "CUSTOMER":
                st.session_state["role"] = "CUSTOMER"
                if user.get("customer_id"):
                    st.session_state["persona_id"] = user["customer_id"]
                st.caption(f"Account: {T.esc(user.get('display_name'))} · {user.get('customer_id')}")
            else:
                st.selectbox(
                    "Customer in Book",
                    ids,
                    key="persona_id",
                    format_func=lambda i: next((f'{p["display_name"]} · {i}' for p in people if p["customer_id"] == i), i),
                )
        else:
            with st.expander("Sign In / Sign Up", expanded=True):
                tab_login, tab_register = st.tabs(["Sign In", "Sign Up"])
                with tab_login:
                    u_in = st.text_input("Username or Email", value="", placeholder="priya@greenproof.bank", key="sb-login-u")
                    p_in = st.text_input("Password", value="", placeholder="password123", type="password", key="sb-login-p")
                    if st.button("Sign In", key="sb-login-btn", type="primary"):
                        if not u_in or not p_in:
                            st.warning("Please enter your credentials.")
                        else:
                            try:
                                u = client.login(u_in, p_in)
                                st.success(f"Welcome, {u.get('display_name')}!")
                                st.rerun()
                            except Exception:
                                st.error("Authentication failed: check credentials or server.")
                    
                    st.caption("Quick sample accounts:")
                    c_col1, c_col2 = st.columns(2)
                    with c_col1:
                        if st.button("Priya (Customer)", key="sb-quick-priya"):
                            client.login("priya@greenproof.bank", "password123")
                            st.rerun()
                    with c_col2:
                        if st.button("Sarah (RM)", key="sb-quick-rm"):
                            client.login("rm_user", "password123")
                            st.rerun()

                with tab_register:
                    su_name = st.text_input("Full Name", placeholder="Alex Green", key="sb-su-name")
                    su_email = st.text_input("Email", placeholder="alex@greenproof.bank", key="sb-su-email")
                    su_pwd = st.text_input("Password", placeholder="At least 6 characters", type="password", key="sb-su-pwd")
                    su_role = st.selectbox(
                        "Account Type",
                        ["CUSTOMER", "RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST"],
                        format_func=lambda r: client.ROLES[r],
                        key="sb-su-role",
                    )
                    if st.button("Create Account & Sign In", key="sb-su-btn", type="primary"):
                        if not su_name or not su_email or not su_pwd:
                            st.warning("Please complete all fields.")
                        else:
                            try:
                                u = client.register(su_name, su_email, su_pwd, su_role)
                                st.success(f"Account created! Welcome, {u.get('display_name')}.")
                                st.rerun()
                            except Exception as err:
                                st.error(f"Sign up failed: {err}")

            st.divider()
            with st.expander("Preview Navigation", expanded=False):
                st.caption("Browse sample profiles in preview mode:")
                st.selectbox("Role", list(client.ROLES), format_func=lambda r: client.ROLES[r], key="role")
                label = "Signed in as" if st.session_state.get("role") == "CUSTOMER" else "Customer"
                st.selectbox(
                    label,
                    ids,
                    key="persona_id",
                    format_func=lambda i: next((f'{p["display_name"]} · {i}' for p in people if p["customer_id"] == i), i),
                )

        st.caption(T.CORE_RULE)
    return next((p for p in people if p["customer_id"] == st.session_state["persona_id"]), people[0])




def gate(area: str, what: str) -> None:
    """Stop the page if the current role may not open it (UI mirror of server-side default-deny)."""
    if not can(area):
        T.banner(f"Your role ({client.ROLES[client.role()]}) cannot open {what}. Access is default-deny.", "err")
        T.footer()
        st.stop()
