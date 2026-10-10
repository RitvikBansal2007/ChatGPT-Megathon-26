"""GreenProof landing page: synthetic-data banner, demo role switcher, page links."""

import streamlit as st

import theme
from components.chrome import ROLES, banner, current_role

st.set_page_config(page_title="GreenProof", layout="wide")
st.markdown(theme.css(), unsafe_allow_html=True)  # the only unsafe_allow_html call

banner()

st.title("GreenProof")
st.write(
    "Green-finance suggestions you can check: every recommendation comes with "
    "its evidence, its limits, and a clear reason when it is not for you."
)

# Role lives in st.session_state["role"]. The widget uses its own key so the
# value survives page switches (Streamlit clears widget keys on other pages).
role = current_role()


def _sync_role() -> None:
    st.session_state["role"] = st.session_state["_role_select"]


st.selectbox(
    "Demo role",
    options=ROLES,
    index=ROLES.index(role) if role in ROLES else 0,
    key="_role_select",
    on_change=_sync_role,
    help="Demo only. Switches the view between synthetic personas and staff roles.",
)
st.caption(f"Viewing as: {st.session_state['role']}")

st.subheader("Where to go")
st.page_link("pages/1_Customer_Hub.py", label="Customer Hub – your opportunities", icon=":material/eco:")
st.page_link("pages/2_Cockpit.py", label="Cockpit – portfolio view", icon=":material/monitoring:")
st.page_link("pages/3_Receipts.py", label="Receipts – how we checked", icon=":material/receipt_long:")
