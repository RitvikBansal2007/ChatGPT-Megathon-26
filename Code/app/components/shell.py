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


def auth_gate(page_name: str = "Welcome to greendash") -> None:
    """Block access to the app until the user logs in or registers."""
    if client.current_user():
        return

    # Hide sidebar navigation completely so visitor lands strictly on auth screen
    st.markdown("""
        <style>
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarCollapsedControl"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .stApp > header { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="text-align:center;padding:24px 0 12px 0">'
                '<div style="display:inline-flex;align-items:center;gap:10px;margin-bottom:6px">'
                '<span style="font-size:32px">🌱</span>'
                '<span style="font-family:var(--font-display);font-size:32px;font-weight:700;color:var(--ink)">greendash</span>'
                '</div>'
                '<p class="gd-muted" style="font-size:16px;max-width:540px;margin:0 auto">'
                'Please sign in with your credentials or create a new account to enter the platform.'
                '</p></div>', unsafe_allow_html=True)

    c_pad_l, c_main, c_pad_r = st.columns([1, 2, 1])
    with c_main:
        with st.container(border=True):
            tab_in, tab_up = st.tabs(["Sign In", "Create New Account (Sign Up)"])
            with tab_in:
                st.markdown("#### Sign In")
                u_in = st.text_input("Username or Email", placeholder="priya@greenproof.bank", key="gate-login-u")
                p_in = st.text_input("Password", placeholder="••••••••", type="password", key="gate-login-p")
                if st.button("Sign In", key="gate-login-btn", type="primary", use_container_width=True):
                    if not u_in or not p_in:
                        st.warning("Please enter your credentials.")
                    else:
                        try:
                            u = client.login(u_in, p_in)
                            st.success(f"Welcome back, {u.get('display_name')}!")
                            try:
                                st.switch_page("Home.py")
                            except Exception:
                                st.rerun()
                        except Exception:
                            st.error("Authentication failed: invalid credentials or backend unavailable.")

                st.divider()
                st.caption("Quick sample accounts:")
                q1, q2 = st.columns(2)
                with q1:
                    if st.button("Priya (Customer)", key="gate-quick-priya", use_container_width=True):
                        client.login("priya@greenproof.bank", "password123")
                        try:
                            st.switch_page("Home.py")
                        except Exception:
                            st.rerun()
                with q2:
                    if st.button("Sarah (RM)", key="gate-quick-rm", use_container_width=True):
                        client.login("rm_user", "password123")
                        try:
                            st.switch_page("Home.py")
                        except Exception:
                            st.rerun()
                q3, q4 = st.columns(2)
                with q3:
                    if st.button("Alex (Analyst)", key="gate-quick-analyst", use_container_width=True):
                        client.login("analyst_user", "password123")
                        try:
                            st.switch_page("Home.py")
                        except Exception:
                            st.rerun()
                with q4:
                    if st.button("Dr. James (Evaluator)", key="gate-quick-eval", use_container_width=True):
                        client.login("evaluator_user", "password123")
                        try:
                            st.switch_page("Home.py")
                        except Exception:
                            st.rerun()

            with tab_up:
                st.markdown("#### Create New Account")
                su_name = st.text_input("Full Name", placeholder="e.g. Maya Green", key="gate-su-name")
                su_email = st.text_input("Email", placeholder="e.g. maya@greenproof.bank", key="gate-su-email")
                su_pwd = st.text_input("Password (min 6 characters)", type="password", key="gate-su-pwd")
                su_role = st.selectbox(
                    "Account Type",
                    ["CUSTOMER", "RELATIONSHIP_MANAGER", "PORTFOLIO_ANALYST"],
                    format_func=lambda r: client.ROLES[r],
                    key="gate-su-role"
                )
                if st.button("Create Account & Sign In", key="gate-su-btn", type="primary", use_container_width=True):
                    if not su_name or not su_email or not su_pwd:
                        st.warning("Please fill in all registration fields.")
                    elif len(su_pwd) < 6:
                        st.warning("Password must be at least 6 characters.")
                    else:
                        try:
                            u = client.register(su_name, su_email, su_pwd, su_role)
                            st.session_state["show_profile_quiz"] = True
                            st.success(f"Account created! Welcome, {u.get('display_name')}.")
                            try:
                                st.switch_page("Home.py")
                            except Exception:
                                st.rerun()
                        except Exception as err:
                            st.error(f"Registration failed: {err}")

    T.footer()
    st.stop()


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
                try:
                    st.switch_page("Home.py")
                except Exception:
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
            st.caption("Please sign in or register to access the menu.")

        st.caption(T.CORE_RULE)
    return next((p for p in people if p["customer_id"] == st.session_state["persona_id"]), people[0])





def gate(area: str, what: str) -> None:
    """Stop the page if the current role may not open it (UI mirror of server-side default-deny)."""
    if not can(area):
        T.banner(f"Your role ({client.ROLES[client.role()]}) cannot open {what}. Access is default-deny.", "err")
        T.footer()
        st.stop()
