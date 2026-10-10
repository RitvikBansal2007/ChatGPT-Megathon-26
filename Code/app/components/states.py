"""Non-RECOMMEND status renderers aligned to real contracts.py field names.

Key contract fields used here:
  ABSTAIN:    impact.missing_inputs[0]  (MissingInput enum value)
              next_action.label
  REVIEW:     (review block not in contracts — use plain_reasons from eligibility)
  RULED_OUT:  eligibility.plain_reasons[0]  (human-readable, never raw rule ID)
              eligibility.rules_fired[0]    (for tag only)
  SOFT_SURFACE: opportunity_name, headline/first reason_code phrase
"""

import html
import streamlit as st
import theme

_MISSING_LABELS = {
    "annual_mileage":   "your annual mileage",
    "roof_suitability": "your roof suitability",
    "energy_data":      "your energy data",
    "vehicle_record":   "your vehicle record",
    "statement_history":"your statement history",
}


def _status_pill(status_key: str) -> str:
    s = theme.STATUS[status_key]
    return (
        f'<span style="background:{s["bg"]};color:{s["fg"]};border:1px solid {s["border"]};'
        f'border-radius:20px;padding:4px 12px;font-size:12px;font-weight:600;'
        f'display:inline-flex;align-items:center;gap:6px;" role="status">'
        f'{html.escape(s["glyph"])} {html.escape(s["label"])}</span>'
    )


def render_abstain(opp: dict) -> None:
    s = theme.STATUS["ABSTAIN"]
    impact   = opp.get("impact") or {}
    missing  = impact.get("missing_inputs") or []
    next_act = opp.get("next_action") or {}

    missing_key   = missing[0] if missing else "additional_information"
    missing_label = _MISSING_LABELS.get(missing_key, missing_key.replace("_", " "))
    cta_label     = next_act.get("label") or f"Add {missing_label}"
    pid           = opp.get("opportunity_id", "x")

    st.markdown(
        f'<div style="background:{s["bg"]};border:1px solid {s["border"]};'
        f'border-radius:16px;padding:16px 20px;">'
        + _status_pill("ABSTAIN")
        + f'<h3 style="margin:10px 0 6px;font-size:16px;">Not enough information to estimate this one yet.</h3>'
        f'<p style="color:#5C7A6B;font-size:14px;margin:0;">Add <strong>{html.escape(missing_label)}</strong> and we can give you a range.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button(cta_label, key=f"abstain_cta_{pid}", type="secondary"):
        st.info("This would open the data-entry flow in the full app.", icon=":material/edit:")
    st.caption(next_act.get("disclaimer", "Not a credit decision."))


def render_review(opp: dict) -> None:
    s = theme.STATUS["REVIEW"]
    pid       = opp.get("opportunity_id", "x")
    next_act  = opp.get("next_action") or {}
    eligibility = opp.get("eligibility") or {}
    plain_reasons = eligibility.get("plain_reasons") or []
    msg = plain_reasons[0] if plain_reasons else "We're seeing mixed signals — tell us a bit more."

    st.markdown(
        f'<div style="background:{s["bg"]};border:1px solid {s["border"]};'
        f'border-radius:16px;padding:16px 20px;">'
        + _status_pill("REVIEW")
        + f'<h3 style="margin:10px 0 6px;font-size:16px;">We\'re seeing mixed signals.</h3>'
        f'<p style="color:#5C7A6B;font-size:14px;margin:0 0 4px;">{html.escape(msg)}</p>'
        f'<p style="font-size:11px;color:#8AA79A;margin:0;">Impact estimate hidden until resolved.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.radio(
        "Can you confirm one thing?",
        ["Yes, confirm", "No, that's wrong", "I'm not sure"],
        key=f"review_q_{pid}",
        index=None,
    )
    if st.button(next_act.get("label", "Submit answer"), key=f"review_cta_{pid}", type="secondary"):
        st.info("Answer submitted — impact estimate will update in the full app.", icon=":material/check_circle:")
    st.caption(next_act.get("disclaimer", "Not a credit decision."))


def render_ruled_out(opp: dict) -> None:
    """RULED_OUT: calm slate card, plain-English rule, NO action button."""
    s = theme.STATUS["RULED_OUT"]
    eligibility   = opp.get("eligibility") or {}
    plain_reasons = eligibility.get("plain_reasons") or []
    rules_fired   = eligibility.get("rules_fired") or []

    # Use plain_reasons (human-readable) from contract; never show raw rule ID to user
    rule_text = plain_reasons[0] if plain_reasons else "This product isn't right for you right now."
    rule_tag  = rules_fired[0] if rules_fired else ""

    st.markdown(
        f'<div style="background:{s["bg"]};border:1px solid {s["border"]};'
        f'border-radius:16px;padding:16px 20px;">'
        + _status_pill("RULED_OUT")
        + f'<h3 style="margin:10px 0 6px;font-size:16px;">Why not?</h3>'
        f'<p style="color:#5C7A6B;font-size:14px;margin:0 0 8px;">{html.escape(rule_text)}</p>'
        + (f'<span style="font-size:10px;font-family:monospace;background:#E3EFE9;'
           f'padding:2px 6px;border-radius:4px;">{html.escape(rule_tag)}</span>' if rule_tag else "")
        + f'<p style="font-size:11px;color:#8AA79A;margin-top:8px;">If your circumstances change, we\'ll re-check automatically.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    # NO action button per playbook. Ghost link only.
    st.markdown(
        '<div style="margin-top:8px;">'
        '<a href="#" style="color:#0F7A55;font-size:12px;">See what else fits</a></div>',
        unsafe_allow_html=True,
    )


def render_soft_surface(opp: dict) -> None:
    s = theme.STATUS["SOFT_SURFACE"]
    pid      = opp.get("opportunity_id", "x")
    next_act = opp.get("next_action") or {}
    rcs      = opp.get("reason_codes") or []
    # Headline: first reason_code phrase or generic
    headline = html.escape(rcs[0].get("phrase", "Good to know about.") if rcs else "Good to know about.")

    st.markdown(
        f'<div style="background:{s["bg"]};border:1px solid {s["border"]};'
        f'border-radius:16px;padding:16px 20px;">'
        + _status_pill("SOFT_SURFACE")
        + f'<h3 style="margin:10px 0 6px;font-size:16px;">{headline}</h3>'
        f'<p style="color:#5C7A6B;font-size:12px;margin:0;">This is for your awareness. '
        f"We'll surface it more prominently when it fits your situation better.</p>"
        f'</div>',
        unsafe_allow_html=True,
    )
    cta = next_act.get("label", "Learn more")
    if st.button(cta, key=f"soft_cta_{pid}", type="secondary"):
        st.info("Educational content would open here in the full app.", icon=":material/lightbulb:")
    st.caption(next_act.get("disclaimer", "Not a credit decision."))
