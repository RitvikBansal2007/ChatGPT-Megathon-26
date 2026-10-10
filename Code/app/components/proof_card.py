"""Proof Card: the main customer-facing opportunity card.

render(opp) dispatches by status:
  RECOMMEND    → full card (this file)
  SOFT_SURFACE → states.render_soft_surface
  ABSTAIN      → states.render_abstain
  REVIEW       → states.render_review
  RULED_OUT    → states.render_ruled_out

All data is read from the opportunity dict. No hard-coded values.
The ONLY unsafe_allow_html calls render static markup — never raw data.
"""

import html
import streamlit as st

import theme
from components import badges, claim_stamp, states


# ── Product pathway tiles config ──────────────────────────────────────
PATHWAYS = {
    "GP01": {"name": "EV Finance",       "icon": ":material/directions_car:"},
    "GP02": {"name": "Green Home Loan",  "icon": ":material/home:"},
    "GP03": {"name": "Solar Finance",    "icon": ":material/wb_sunny:"},
    "GP04": {"name": "Paperless Banking","icon": ":material/description:"},
}

_STATUS_ORDER = ["RECOMMEND", "REVIEW", "ABSTAIN", "SOFT_SURFACE", "RULED_OUT"]


def render(opp: dict) -> None:
    """Render the appropriate card for opp['status']."""
    status = opp.get("status", "SOFT_SURFACE")
    dispatch = {
        "RECOMMEND":    _render_recommend,
        "SOFT_SURFACE": states.render_soft_surface,
        "ABSTAIN":      states.render_abstain,
        "REVIEW":       states.render_review,
        "RULED_OUT":    states.render_ruled_out,
    }
    dispatch.get(status, states.render_soft_surface)(opp)


# ── Full RECOMMEND card ────────────────────────────────────────────────
def _render_recommend(opp: dict) -> None:
    product = html.escape(opp.get("product", ""))
    headline = html.escape(opp.get("headline", ""))
    why_now = (opp.get("why_now") or {}).get("display", "")
    reason_codes = opp.get("reason_codes", [])
    impact = opp.get("impact") or {}
    explanation = opp.get("explanation") or {}
    actions = opp.get("actions") or {}

    # ── Card open
    st.markdown(
        '<div class="gd-card gd-status--recommend">',
        unsafe_allow_html=True,
    )

    # 1. Status pill + product tag + headline
    s = theme.STATUS["RECOMMEND"]
    st.markdown(
        f'<div class="gd-row" style="margin-bottom:8px;">'
        f'<span class="gd-pill gd-status--recommend" role="status">'
        f'{html.escape(s["glyph"])} {html.escape(s["label"])}'
        f'</span>'
        f'<span class="gd-tag gd-tag--boxed">{product}</span>'
        f'</div>'
        f'<h3 class="gd-headline">{headline}</h3>',
        unsafe_allow_html=True,
    )

    # Why-now chip
    if why_now:
        st.markdown(
            f'<div class="gd-chip" style="margin-bottom:12px;">'
            f'⏰ Why now: {html.escape(why_now)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # 2. Evidence chips
    if reason_codes:
        st.markdown('<p class="gd-muted" style="font-size:12px;margin-bottom:6px;">Why you\'re seeing this</p>', unsafe_allow_html=True)
        chips = ""
        for rc in reason_codes:
            src_label = "You told us" if rc.get("source") == "customer_declared" else "From your transactions"
            date = html.escape(rc.get("observed_at", ""))
            display = html.escape(rc.get("display", ""))
            chips += (
                f'<div class="gd-chip" style="margin-bottom:6px;border-radius:14px;display:flex;gap:8px;align-items:flex-start;">'
                f'<span>{"👤" if rc.get("source")=="customer_declared" else "🧾"}</span>'
                f'<div><div>{display}</div>'
                f'<div class="gd-tag" style="margin-top:2px;">{src_label} · {date}</div>'
                f'</div></div>'
            )
        st.markdown(chips, unsafe_allow_html=True)

    # 3. Three verdict badges
    badges.render_badges(opp)

    # 4. Impact estimate expander
    if impact.get("status") not in ("INSUFFICIENT_DATA", "NOT_APPLICABLE", "HIDDEN"):
        family = impact.get("family", "co2")
        with st.expander("Impact estimate", expanded=False):
            if family == "paper":
                # Paperless: show sheets + digital adoption, never CO2e
                paper = impact.get("paper") or {}
                digital = impact.get("digital") or {}
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Paper sheets avoided", paper.get("value", "—"), help=paper.get("note", ""))
                with col2:
                    st.metric("Digital adoption", digital.get("value", "—"), help=digital.get("note", ""))
            else:
                st.markdown(
                    f'<div class="gd-well">'
                    f'<div class="gd-tag">ESTIMATE</div>'
                    f'<div class="gd-kpi">{html.escape(impact.get("display", "—"))}</div>'
                    f'<p class="gd-body">{html.escape(impact.get("bills", ""))}</p>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.caption(f"**Formula:** {impact.get('formula', '—')}")
            st.caption(f"**Baseline:** {impact.get('baseline', '—')} · **Horizon:** {impact.get('horizon', '—')}")
            st.caption(f"**Factor source:** {impact.get('factor_refs', '—')}")
            st.info("Estimate, not a guarantee.", icon=":material/info:")

    # 5. Claim-Check stamp
    claim_stamp.render(explanation)

    # Close card div
    st.markdown("</div>", unsafe_allow_html=True)

    # 6. Actions (outside the card div, full-width)
    primary = actions.get("primary")
    secondary = actions.get("secondary")

    st.markdown('<div class="gd-actions">', unsafe_allow_html=True)
    if primary:
        if st.button(primary, key=f"primary_{opp.get('id','x')}", type="primary", use_container_width=True):
            st.info(f"'{primary}' tapped — this would open the product flow.", icon=":material/open_in_new:")
    if secondary:
        if st.button(secondary, key=f"secondary_{opp.get('id','x')}", use_container_width=True):
            st.info(f"'{secondary}' tapped.", icon=":material/open_in_new:")
    st.markdown('<a class="gd-link" href="#" style="text-align:center;">Talk to a person</a>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption("Not a credit decision. Likelihood is not creditworthiness. Estimate, not a guarantee.")
