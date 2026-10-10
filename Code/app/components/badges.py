"""Three separate verdict badges: Likelihood · Eligibility · Impact quality.

Never merged into one score. Each has a unique icon (glyph), title, and value.
Colours from theme.BADGES only — no hard-coded hex values.
"""

import html
import streamlit as st
import theme


def render_badges(opportunity: dict) -> None:
    """Render the three verdict badges in one row (st.columns)."""
    likelihood = opportunity.get("likelihood_band", "LOW")
    eligibility_result = (
        opportunity.get("eligibility", {}).get("result", "NOT_ELIGIBLE")
        .upper().replace(" ", "_").replace("-", "_")
    )
    impact_quality = opportunity.get("impact", {}).get("quality") or "LOW"

    # Normalise eligibility key to BADGES dict keys
    elig_map = {
        "PASSED": "ELIGIBLE",
        "ELIGIBLE": "ELIGIBLE",
        "NEEDS_VERIFICATION": "NEEDS_VERIFICATION",
        "NOT_ELIGIBLE": "NOT_ELIGIBLE",
    }
    elig_key = elig_map.get(eligibility_result, "NOT_ELIGIBLE")

    lk = theme.BADGES["LIKELIHOOD"]
    ek = theme.BADGES["ELIGIBILITY"]
    iq = theme.BADGES["IMPACT_QUALITY"]

    lv = lk["values"].get(likelihood, lk["values"]["LOW"])
    ev = ek["values"].get(elig_key, ek["values"]["NOT_ELIGIBLE"])
    iv = iq["values"].get(impact_quality, iq["values"]["LOW"])

    # Build HTML badges using design tokens (all text is escaped)
    def _badge(glyph: str, title: str, label: str, bg: str, fg: str, border: str,
               steps: str | None = None) -> str:
        meter = ""
        if steps is not None:
            total = 3
            lit = int(steps)
            dots = "".join(
                f'<i class="on"></i>' if i < lit else '<i></i>'
                for i in range(total)
            )
            meter = f'<span class="gd-meter" aria-hidden="true">{dots}</span>'
        return (
            f'<div class="gd-badge" style="background:{bg};color:{fg};border-color:{border};">'
            f'<span class="gd-badge-glyph" aria-hidden="true">{glyph}</span>'
            f'<div>'
            f'<div class="gd-badge-title">{html.escape(title)}</div>'
            f'<div class="gd-badge-value">{html.escape(label)}{meter}</div>'
            f'</div>'
            f'</div>'
        )

    # Meter steps for impact quality
    iq_steps = iv.get("steps")

    badges_html = (
        '<div class="gd-verdicts">'
        + _badge(lk["glyph"], lk["title"], lv["label"], lv["bg"], lv["fg"], lv["border"])
        + _badge(ek["glyph"], ek["title"], ev["label"], ev["bg"], ev["fg"], ev["border"])
        + _badge(iq["glyph"], iq["title"], iv["label"], iv["bg"], iv["fg"], iv["border"], iq_steps)
        + "</div>"
    )
    st.markdown(badges_html, unsafe_allow_html=True)

    # Accessible footnote
    st.caption(
        f"**{lk['title']}:** {lv['label']} · "
        f"**{ek['title']}:** {ev['label']} · "
        f"**{iq['title']}:** {iv['label']}. "
        + lk.get("footnote", "")
    )
