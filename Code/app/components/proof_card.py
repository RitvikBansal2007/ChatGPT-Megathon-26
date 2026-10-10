"""Proof Card — aligned to greenproof/contracts.py (frozen by G1-A).

Opportunity field names (real contract):
  opportunity_id, opportunity_name, status, propensity, likelihood_band
  eligibility.result / rules_fired / plain_reasons
  reason_codes[].code / .phrase / .display / .observed_at / .source
  why_now.display
  impact.status / .metric_family / .low / .central / .high / .display
         .formula / .baseline / .horizon / .factor_refs / .quality / .missing_inputs
  digital_adoption.paper_statements_12m / .digital_share
  explanation.sentences / .source / .claimcheck_status
  next_action.label / .secondary / .disclaimer
"""

import html
import streamlit as st

import theme
from components import badges, claim_stamp, states

_PATHWAY_META = {
    "GP01": {"name": "EV Finance",        "icon": "🚗"},
    "GP02": {"name": "Green Home Loan",   "icon": "🏠"},
    "GP03": {"name": "Solar Finance",     "icon": "☀️"},
    "GP04": {"name": "Paperless Banking", "icon": "📄"},
}


def render(opp: dict) -> None:
    status = opp.get("status", "SOFT_SURFACE")
    dispatch = {
        "RECOMMEND":    _render_recommend,
        "SOFT_SURFACE": states.render_soft_surface,
        "ABSTAIN":      states.render_abstain,
        "REVIEW":       states.render_review,
        "RULED_OUT":    states.render_ruled_out,
    }
    dispatch.get(status, states.render_soft_surface)(opp)


def _render_recommend(opp: dict) -> None:
    pid          = opp.get("opportunity_id", "")
    product      = html.escape(opp.get("opportunity_name", pid))
    headline     = html.escape(opp.get("headline") or "")
    # headline may not be in the contract — fall back to first reason_code phrase
    if not headline:
        rcs = opp.get("reason_codes") or []
        headline = html.escape(rcs[0].get("phrase", "Worth exploring.")) if rcs else "Worth exploring."
    why_now      = (opp.get("why_now") or {}).get("display", "")
    reason_codes = opp.get("reason_codes") or []
    impact       = opp.get("impact") or {}
    explanation  = opp.get("explanation") or {}
    next_action  = opp.get("next_action") or {}
    data_as_of   = opp.get("data_as_of", "")

    s = theme.STATUS["RECOMMEND"]

    # ── Card open ────────────────────────────────────────────────────────────
    st.markdown('<div class="gd-card gd-status--recommend">', unsafe_allow_html=True)

    # Status pill + product tag + date
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px;">'
        f'<span class="gd-pill gd-status--recommend" role="status">'
        f'{html.escape(s["glyph"])} {html.escape(s["label"])}</span>'
        f'<span style="font-size:11px;font-family:monospace;background:#E3EFE9;'
        f'padding:2px 8px;border-radius:4px;">{product}</span>'
        + (f'<span style="font-size:11px;color:#8AA79A;margin-left:auto;">AS OF {html.escape(str(data_as_of))}</span>'
           if data_as_of else "")
        + f'</div>'
        f'<h3 style="margin:0 0 8px;font-size:17px;line-height:1.4;">{headline}</h3>',
        unsafe_allow_html=True,
    )

    # Why-now chip
    if why_now:
        st.markdown(
            f'<div style="background:#E8F8FF;border:1px solid #22B8CF;border-radius:20px;'
            f'padding:6px 14px;font-size:12px;display:inline-flex;align-items:center;'
            f'gap:6px;margin-bottom:12px;">⏰ Why now: {html.escape(why_now)}</div>',
            unsafe_allow_html=True,
        )

    # Evidence chips (reason_codes)
    if reason_codes:
        st.markdown(
            '<p style="font-size:11px;font-weight:600;text-transform:uppercase;'
            'letter-spacing:.05em;color:#8AA79A;margin:0 0 6px;">Why you\'re seeing this</p>',
            unsafe_allow_html=True,
        )
        chips_html = ""
        for rc in reason_codes:
            src = rc.get("source", "")
            is_declared = "declared" in src
            icon = "👤" if is_declared else "🧾"
            src_label = "You told us" if is_declared else "From your transactions"
            display = html.escape(rc.get("display") or rc.get("phrase", ""))
            date = html.escape(str(rc.get("observed_at", "")))
            code = html.escape(rc.get("code", ""))
            chips_html += (
                f'<div style="background:#F1F8F4;border:1px solid #C8E6D4;border-radius:10px;'
                f'padding:8px 12px;margin-bottom:6px;display:flex;gap:10px;align-items:flex-start;">'
                f'<span>{icon}</span>'
                f'<div style="min-width:0;">'
                f'<div style="font-size:13px;">{display}</div>'
                f'<div style="display:flex;gap:6px;margin-top:4px;">'
                f'<span style="font-size:10px;font-family:monospace;background:#E3EFE9;'
                f'padding:1px 5px;border-radius:3px;">{code}</span>'
                f'<span style="font-size:10px;color:#8AA79A;">{src_label} · {date}</span>'
                f'</div></div></div>'
            )
        st.markdown(chips_html, unsafe_allow_html=True)

    # Three verdict badges
    badges.render_badges(opp)

    # Impact expander
    imp_status = impact.get("status", "ESTIMATED")
    if imp_status not in ("INSUFFICIENT_DATA", "NOT_APPLICABLE", "HIDDEN"):
        family = (impact.get("metric_family") or "").lower()
        with st.expander("Impact estimate", expanded=False):
            if family == "paper":
                # Paperless — show paper sheets and digital adoption separately, NEVER CO₂e
                dig = opp.get("digital_adoption") or {}
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "Paper sheets/year",
                        int(impact.get("central") or impact.get("high") or 0),
                        help=impact.get("display", ""),
                    )
                with col2:
                    share = dig.get("digital_share", 0)
                    st.metric("Digital adoption", f"{share:.0%}", help="Statements already digital")
            else:
                lo  = impact.get("low")
                hi  = impact.get("high")
                disp = impact.get("display", "")
                st.markdown(
                    f'<div style="background:#DDF8EA;border-radius:10px;padding:14px 16px;margin-bottom:8px;">'
                    f'<div style="font-size:10px;font-family:monospace;color:#8AA79A;margin-bottom:4px;">ESTIMATE</div>'
                    f'<div style="font-size:26px;font-weight:800;color:#0F7A55;line-height:1.2;">'
                    f'{html.escape(disp)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            st.caption(f"**Formula:** {impact.get('formula','—')}")
            st.caption(f"**Baseline:** {impact.get('baseline','—')} · **Horizon:** {impact.get('horizon','—')}")
            refs = impact.get("factor_refs") or []
            if refs:
                st.caption(f"**Factor refs:** {', '.join(refs)}")
            st.info("Estimate, not a guarantee.", icon=":material/info:")

    # Claim-Check stamp
    claim_stamp.render(explanation)

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Action buttons (outside card) ────────────────────────────────────────
    primary   = next_action.get("label")
    secondary = next_action.get("secondary")
    disclaimer = next_action.get("disclaimer", "Not a credit decision. Estimate, not a guarantee.")

    if primary:
        if st.button(primary, key=f"cta_p_{pid}", type="primary", use_container_width=True):
            st.info(f"'{primary}' — this would open the product flow in the full app.",
                    icon=":material/open_in_new:")
    if secondary:
        if st.button(secondary, key=f"cta_s_{pid}", use_container_width=True):
            st.info(f"'{secondary}' tapped.", icon=":material/open_in_new:")

    st.markdown(
        '<div style="text-align:center;margin-top:8px;">'
        '<a href="#" style="color:#0F7A55;font-size:12px;">Talk to a person</a></div>',
        unsafe_allow_html=True,
    )
    st.caption(disclaimer)
