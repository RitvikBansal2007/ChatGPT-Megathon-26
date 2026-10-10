"""Customer Hub — four pathway tiles, always visible, ordered by status then propensity.

Scenario Lab side panel visible to Evaluator and Relationship Manager roles.
Mobile-first: single column under 640px (handled by theme.css()).
All data via client.py only.
"""

import streamlit as st

import theme
import client
from components.chrome import banner, current_role
from components import proof_card, scenario_lab

st.set_page_config(page_title="GreenDash – Customer Hub", layout="wide")
st.markdown(theme.css(), unsafe_allow_html=True)

banner()
st.title("Customer Hub")
role = current_role()
st.caption(f"Viewing as: {role}")

# ── Derive customer ID from role ─────────────────────────────────────────────
_ROLE_TO_CID = {
    "Customer – Priya (GP01)":  "CUST-0001",
    "Customer – Aisha (GP03)":  "CUST-0003",
    "Customer – Marcus (GP02)": "CUST-0002",
    "Customer – Fatima (GP04)": "CUST-0004",
    "Customer – Tom (GP01)":    "CUST-0005",
}
_DEFAULT_CID = "CUST-0001"
_STATUS_ORDER = {"RECOMMEND": 0, "REVIEW": 1, "ABSTAIN": 2, "SOFT_SURFACE": 3, "RULED_OUT": 4}
_PATHWAY_META = {
    "GP01": {"name": "EV Finance",        "icon": ":material/directions_car:"},
    "GP02": {"name": "Green Home Loan",   "icon": ":material/home:"},
    "GP03": {"name": "Solar Finance",     "icon": ":material/wb_sunny:"},
    "GP04": {"name": "Paperless Banking", "icon": ":material/description:"},
}

customer_id = _ROLE_TO_CID.get(role, _DEFAULT_CID)

# ── Scenario Lab (sidebar — only for allowed roles) ──────────────────────────
selected_pid = st.session_state.get("hub_selected")
opp_id = selected_pid or "GP01"
scenario_lab.render(customer_id, opp_id, role)

# ── Load opportunities ───────────────────────────────────────────────────────
with st.spinner("Loading your opportunities…"):
    try:
        opportunities: list[dict] = client.get_opportunities(customer_id)
    except FileNotFoundError:
        st.warning(
            "Fixture file not found — run the app from the repo root with "
            "`DEMO_MODE=fixtures streamlit run app/Home.py`.",
            icon=":material/warning:",
        )
        opportunities = []
    except Exception as exc:
        st.error(f"Could not load opportunities. {exc}", icon=":material/error:")
        opportunities = []

if not opportunities:
    st.info(
        "No opportunities loaded. Make sure `fixtures/opportunities.json` exists.",
        icon=":material/construction:",
    )
    st.stop()

# ── Sort: status order then propensity desc ──────────────────────────────────
opportunities.sort(
    key=lambda o: (
        _STATUS_ORDER.get(o.get("status", "SOFT_SURFACE"), 99),
        -o.get("propensity", 0),
    )
)
opp_by_product: dict[str, dict] = {
    o.get("opportunity_id", ""): o for o in opportunities
}

# ── Initialise session state ─────────────────────────────────────────────────
if "hub_selected" not in st.session_state:
    st.session_state["hub_selected"] = None

# ── Pathway tile row ─────────────────────────────────────────────────────────
st.subheader("Your green pathways")
st.caption("All four pathways are always visible — we show you where you stand on each.")

tile_cols = st.columns(4, gap="small")
for col, (pid, meta) in zip(tile_cols, _PATHWAY_META.items()):
    opp = opp_by_product.get(pid)
    status = opp.get("status", "SOFT_SURFACE") if opp else "SOFT_SURFACE"
    s_tok = theme.STATUS.get(status, theme.STATUS["SOFT_SURFACE"])
    is_selected = st.session_state["hub_selected"] == pid
    border = f"3px solid {s_tok['border']}" if is_selected else f"1px solid {s_tok['border']}"

    with col:
        st.markdown(
            f'<div class="gd-card" style="cursor:pointer;border:{border};background:{s_tok["bg"]};">'
            f'<div style="font-size:22px;margin-bottom:4px;" aria-hidden="true">{s_tok["glyph"]}</div>'
            f'<div style="font-weight:700;font-size:14px;margin-bottom:6px;">{meta["name"]}</div>'
            f'<span class="gd-pill {s_tok["css_class"]}" style="font-size:11px;padding:2px 8px;">'
            f'{s_tok["label"] if opp else "No data yet"}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Open" if not is_selected else "✓ Open",
            key=f"tile_{pid}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state["hub_selected"] = pid
            st.rerun()

# ── Selected Proof Card ──────────────────────────────────────────────────────
selected_pid = st.session_state.get("hub_selected")
if selected_pid:
    st.divider()
    opp = opp_by_product.get(selected_pid)
    meta = _PATHWAY_META.get(selected_pid, {"name": selected_pid})
    st.subheader(f"{meta['name']}")

    if opp:
        # Responsive columns: full width on mobile, max 480px on desktop
        card_col, spacer = st.columns([5, 4])
        with card_col:
            proof_card.render(opp)
    else:
        st.info(
            f"No opportunity data for {meta['name']} yet.",
            icon=":material/construction:",
        )

    if st.button("← All pathways", key="back_hub", type="secondary"):
        st.session_state["hub_selected"] = None
        st.rerun()
