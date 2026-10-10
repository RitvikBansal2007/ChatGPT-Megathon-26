"""Three separate verdict badges: Likelihood · Eligibility · Impact quality.

Reads from the real contracts.py field names:
  opportunity["likelihood_band"]          → HIGH / MEDIUM / LOW
  opportunity["eligibility"]["result"]    → ELIGIBLE / NEEDS_VERIFICATION / NOT_ELIGIBLE
  opportunity["impact"]["quality"]        → HIGH / MEDIUM / LOW / None

Never merged. Each badge: glyph + title + value label.
Colours from theme.BADGES only — no hard-coded hex.
"""

import html
import streamlit as st
import theme


def render_badges(opportunity: dict) -> None:
    likelihood   = opportunity.get("likelihood_band", "LOW")
    elig_result  = (opportunity.get("eligibility") or {}).get("result", "NOT_ELIGIBLE").upper()
    impact_quality = (opportunity.get("impact") or {}).get("quality") or "LOW"

    # Normalise eligibility to BADGES dict keys
    _ELIG_MAP = {
        "ELIGIBLE":           "ELIGIBLE",
        "PASSED":             "ELIGIBLE",
        "NEEDS_VERIFICATION": "NEEDS_VERIFICATION",
        "NOT_ELIGIBLE":       "NOT_ELIGIBLE",
        "NOT_PASSED":         "NOT_ELIGIBLE",
    }
    elig_key = _ELIG_MAP.get(elig_result, "NOT_ELIGIBLE")

    lk = theme.BADGES["LIKELIHOOD"]
    ek = theme.BADGES["ELIGIBILITY"]
    iq = theme.BADGES["IMPACT_QUALITY"]

    lv = lk["values"].get(likelihood, lk["values"]["LOW"])
    ev = ek["values"].get(elig_key, ek["values"]["NOT_ELIGIBLE"])
    iv = iq["values"].get(impact_quality, iq["values"]["LOW"])

    def _badge(glyph, title, label, bg, fg, border, steps=None):
        meter = ""
        if steps is not None:
            lit = int(steps)
            meter = "".join(
                '<i style="background:currentColor;"></i>' if i < lit
                else '<i style="opacity:0.2;background:currentColor;"></i>'
                for i in range(3)
            )
            meter = f'<span class="gd-meter" aria-hidden="true" style="display:inline-flex;gap:2px;margin-left:4px;">{meter}</span>'
        return (
            f'<div class="gd-badge" style="background:{bg};color:{fg};'
            f'border:1px solid {border};border-radius:12px;padding:10px 14px;'
            f'display:flex;align-items:center;gap:10px;flex:1;min-width:0;">'
            f'<span style="font-size:18px;" aria-hidden="true">{glyph}</span>'
            f'<div style="min-width:0;">'
            f'<div style="font-size:10px;font-weight:600;text-transform:uppercase;'
            f'letter-spacing:.06em;opacity:.7;">{html.escape(title)}</div>'
            f'<div style="font-size:13px;font-weight:700;margin-top:2px;">'
            f'{html.escape(label)}{meter}</div>'
            f'</div></div>'
        )

    html_out = (
        '<div style="display:flex;gap:8px;margin:12px 0;" role="group" '
        'aria-label="Three separate verdicts">'
        + _badge(lk["glyph"], lk["title"], lv["label"], lv["bg"], lv["fg"], lv["border"])
        + _badge(ek["glyph"], ek["title"], ev["label"], ev["bg"], ev["fg"], ev["border"])
        + _badge(iq["glyph"], iq["title"], iv["label"], iv["bg"], iv["fg"], iv["border"],
                 iv.get("steps"))
        + "</div>"
    )
    st.markdown(html_out, unsafe_allow_html=True)
    st.caption(
        f"**{lk['title']}:** {lv['label']} · "
        f"**{ek['title']}:** {ev['label']} · "
        f"**{iq['title']}:** {iv['label']}. "
        + lk.get("footnote", "Likelihood is not creditworthiness.")
    )
