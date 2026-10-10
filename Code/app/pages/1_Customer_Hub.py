"""Customer Hub — four pathway tiles, always visible, ordered by status then propensity.

Mobile-first: single column under 640px (handled by theme.css()).
Data comes through client.py only. No engine imports.
"""

import streamlit as st

import theme
import client
from components.chrome import banner, current_role
from components import proof_card

st.set_page_config(page_title="GreenProof – Customer Hub", layout="wide")
st.markdown(theme.css(), unsafe_allow_html=True)  # the only unsafe_allow_html call on this page

banner()

st.title("Customer Hub")
role = current_role()
st.caption(f"Viewing as: {role}")

# ── Derive customer ID from role ────────────────────────────────────────────
_ROLE_TO_CID = {
    "Customer – Priya (GP01)":  "CUST-0001",
    "Customer – Aisha (GP03)":  "CUST-0003",
    "Customer – Marcus (GP02)": "CUST-0002",
    "Customer – Fatima (GP04)": "CUST-0004",
}
_STATUS_ORDER = {"RECOMMEND": 0, "REVIEW": 1, "ABSTAIN": 2, "SOFT_SURFACE": 3, "RULED_OUT": 4}
_PATHWAY_META = {
    "GP01": {"name": "EV Finance",        "icon": ":material/directions_car:"},
    "GP02": {"name": "Green Home Loan",   "icon": ":material/home:"},
    "GP03": {"name": "Solar Finance",     "icon": ":material/wb_sunny:"},
    "GP04": {"name": "Paperless Banking", "icon": ":material/description:"},
}

customer_id = _ROLE_TO_CID.get(role, "CUST-0001")

# ── Load opportunities ──────────────────────────────────────────────────────
with st.spinner("Loading your opportunities…"):
    try:
        opportunities: list[dict] = client.get_opportunities(customer_id)
    except FileNotFoundError:
        st.warning(
            "Fixture file not found — showing placeholder tiles.",
            icon=":material/warning:",
        )
        opportunities = []
    except Exception as exc:
        st.error(f"Could not load opportunities: {exc}", icon=":material/error:")
        opportunities = []

# ── Sort: status order then propensity desc ─────────────────────────────────
opportunities.sort(
    key=lambda o: (
        _STATUS_ORDER.get(o.get("status", "SOFT_SURFACE"), 99),
        -o.get("propensity", 0),
    )
)

# ── Pathway tile grid ───────────────────────────────────────────────────────
st.subheader("Your green pathways")
st.caption("All four pathways are always visible — we show you where you stand on each.")

# Build an index by product_id for quick lookup
opp_by_product: dict[str, dict] = {o.get("id", o.get("product_id", "")): o for o in opportunities}

# Initialise selected tile in session state
if "hub_selected" not in st.session_state:
    st.session_state["hub_selected"] = None

# Tile row
tile_cols = st.columns(4, gap="small")
for col, (pid, meta) in zip(tile_cols, _PATHWAY_META.items()):
    opp = opp_by_product.get(pid)
    status = opp.get("status", "SOFT_SURFACE") if opp else "SOFT_SURFACE"
    s_token = theme.STATUS.get(status, theme.STATUS["SOFT_SURFACE"])
    selected = st.session_state["hub_selected"] == pid
    border_style = "3px solid " + s_token["border"] if selected else f"1px solid {s_token['border']}"

    with col:
        st.markdown(
            f'<div class="gd-card" style="cursor:pointer;border:{border_style};background:{s_token["bg"]};">'
            f'<div style="font-size:24px;" aria-hidden="true">{s_token["glyph"]}</div>'
            f'<div style="font-weight:700;margin:4px 0;">{meta["name"]}</div>'
            f'<div class="gd-pill {s_token["css_class"]}" style="font-size:11px;padding:2px 8px;">'
            f'{s_token["label"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            f"Open {meta['name']}",
            key=f"tile_{pid}",
            use_container_width=True,
        ):
            st.session_state["hub_selected"] = pid
            st.rerun()

# ── Selected card ────────────────────────────────────────────────────────────
selected_pid = st.session_state.get("hub_selected")
if selected_pid:
    st.divider()
    opp = opp_by_product.get(selected_pid)
    if opp:
        meta = _PATHWAY_META[selected_pid]
        st.subheader(f"{meta['name']} — Detail")

        # Responsive: single col on mobile, sidebar+main on desktop
        card_col, _ = st.columns([1, 0])  # full width (theme handles 390px)
        with card_col:
            proof_card.render(opp)
    else:
        st.info(
            f"No opportunity data for {_PATHWAY_META.get(selected_pid, {}).get('name', selected_pid)} yet.",
            icon=":material/construction:",
        )
    if st.button("← Back to all pathways", key="back_hub"):
        st.session_state["hub_selected"] = None
        st.rerun()
elif not opportunities:
    st.info(
        "No opportunities loaded. Make sure fixtures/opportunities.json exists and DEMO_MODE=fixtures.",
        icon=":material/construction:",
    )
