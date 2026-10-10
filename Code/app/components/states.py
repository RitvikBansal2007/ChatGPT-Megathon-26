"""Non-RECOMMEND status renderers: ABSTAIN · REVIEW · RULED_OUT · SOFT_SURFACE.

Each function receives the full opportunity dict and renders a self-contained
card using theme tokens only. No hard-coded hex values; no unsafe HTML with
data interpolated into it.
"""

import html
import streamlit as st
import theme


def _status_pill(status_key: str) -> str:
    s = theme.STATUS[status_key]
    g = html.escape(s["glyph"])
    label = html.escape(s["label"])
    cls = s["css_class"]
    return (
        f'<span class="gd-pill {cls}" role="status" aria-label="{label}">'
        f'{g} {label}'
        f'</span>'
    )


def render_abstain(opp: dict) -> None:
    """ABSTAIN: 'Need one thing' — names the single missing input, offers to add it."""
    s = theme.STATUS["ABSTAIN"]
    missing = (opp.get("impact") or {}).get("missing_inputs") or []
    missing_field = missing[0] if missing else "additional information"

    _FIELD_LABELS = {
        "epc_rating":       "your home's energy rating (EPC)",
        "roof_orientation": "your roof direction",
        "annual_mileage":   "your annual mileage",
        "vehicle_details":  "your vehicle details",
    }
    missing_label = _FIELD_LABELS.get(missing_field, missing_field.replace("_", " "))

    with st.container():
        st.markdown(
            f'<div class="gd-card {s["css_class"]}">'
            + _status_pill("ABSTAIN")
            + f'<h3 class="gd-headline">Not enough information to estimate this one yet.</h3>'
            f'<p class="gd-body">Add <strong>{html.escape(missing_label)}</strong> and '
            f'we can give you a range.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            f"Add {missing_label}",
            key=f"abstain_cta_{opp.get('id', 'x')}",
            type="secondary",
        ):
            st.info("This would open the data-entry flow in the full app.", icon=":material/edit:")


def render_review(opp: dict) -> None:
    """REVIEW: 'Mixed signals' — hides impact, shows one confirming question."""
    s = theme.STATUS["REVIEW"]
    review = (opp.get("review") or {})
    msg = review.get(
        "message",
        "We're seeing mixed signals — tell us a bit more and we'll sharpen this.",
    )
    question = review.get("question", "Can you confirm one thing?")
    options = review.get("options", ["Yes", "No", "Not sure"])

    with st.container():
        st.markdown(
            f'<div class="gd-card {s["css_class"]}">'
            + _status_pill("REVIEW")
            + f'<h3 class="gd-headline">We\'re seeing mixed signals.</h3>'
            f'<p class="gd-body">{html.escape(msg)}</p>'
            f'<p class="gd-muted" style="font-size:12px;">Impact estimate hidden until resolved.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.radio(
            question,
            options,
            key=f"review_q_{opp.get('id', 'x')}",
            index=None,
        )
        if st.button(
            "Submit answer",
            key=f"review_cta_{opp.get('id', 'x')}",
            type="secondary",
        ):
            st.info("Answer submitted — impact estimate will update in the full app.", icon=":material/check_circle:")


def render_ruled_out(opp: dict) -> None:
    """RULED_OUT: 'Why not?' — calm slate card, plain-English rule, NO action button."""
    s = theme.STATUS["RULED_OUT"]
    eligibility = opp.get("eligibility") or {}
    rules_fired = eligibility.get("rules_fired") or []

    _RULE_TEXT = {
        "GP01-R1": "You already have an electric vehicle and no replacement need on record.",
        "GP01-R2": "There's no vehicle on record for you right now.",
        "GP01-V1": "Your current car finance needs to be settled or transferred first.",
        "GP02-R1": "Green Home Loan is for homeowners, and our records show you rent.",
        "GP02-R2": "You already have a Green Home Loan with us.",
        "GP03-R1": "Solar Finance is for homeowners, and our records show you rent.",
        "GP03-R2": "Your home already has solar panels on record.",
        "GP04-R1": "You're already fully paperless — nothing to do here.",
    }
    rule_text = _RULE_TEXT.get(rules_fired[0] if rules_fired else "", "This product isn't right for you right now.")
    rule_id = rules_fired[0] if rules_fired else ""

    st.markdown(
        f'<div class="gd-card {s["css_class"]}">'
        + _status_pill("RULED_OUT")
        + f'<h3 class="gd-headline">Why not?</h3>'
        f'<p class="gd-body">{html.escape(rule_text)}</p>'
        + (f'<p class="gd-tag" style="margin-top:8px;">{html.escape(rule_id)}</p>' if rule_id else "")
        + f'<p class="gd-muted" style="font-size:12px;margin-top:8px;">'
        f'If your circumstances change, we\'ll re-check automatically.</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
    # NO action button — per playbook rule


def render_soft_surface(opp: dict) -> None:
    """SOFT_SURFACE: lower prominence, educational wording, no strong CTA."""
    s = theme.STATUS["SOFT_SURFACE"]
    headline = opp.get("headline", "Good to know about.")

    with st.container():
        st.markdown(
            f'<div class="gd-card {s["css_class"]}">'
            + _status_pill("SOFT_SURFACE")
            + f'<h3 class="gd-headline">{html.escape(headline)}</h3>'
            f'<p class="gd-muted">This is for your awareness. We\'ll surface it more prominently when it fits your situation better.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Learn more",
            key=f"soft_cta_{opp.get('id', 'x')}",
            type="secondary",
        ):
            st.info("Educational content would open here in the full app.", icon=":material/lightbulb:")
